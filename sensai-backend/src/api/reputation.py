from api.config import (
    user_network_profiles_table_name,
    task_completions_table_name,
)
from api.utils.db import execute_db_operation, get_new_db_connection


BADGE_TIERS = [
    (0, "Bronze 1"),
    (50, "Bronze 2"),
    (120, "Bronze 3"),
    (200, "Silver 1"),
    (300, "Silver 2"),
    (420, "Silver 3"),
    (550, "Gold 1"),
    (700, "Gold 2"),
    (870, "Gold 3"),
    (1050, "Platinum 1"),
    (1250, "Platinum 2"),
    (1470, "Platinum 3"),
    (1700, "Diamond 1"),
    (1950, "Diamond 2"),
    (2220, "Diamond 3"),
    (2500, "God"),
]


def compute_badge_tier(score: int) -> str:
    tier = "Bronze 1"
    for threshold, name in BADGE_TIERS:
        if score >= threshold:
            tier = name
        else:
            break
    return tier


def compute_network_role(badge_tier: str, is_mentor: bool) -> str:
    if is_mentor:
        return "mentor"
    # Check if badge tier is Gold 1 or higher
    gold_and_above = [t[1] for t in BADGE_TIERS if t[0] >= 550]
    if badge_tier in gold_and_above:
        return "master"
    return "newbie"


async def recompute_user_badge(user_id: int, org_id: int):
    """Recompute badge score and tier for a user."""
    profile = await execute_db_operation(
        f"SELECT posts_count, upvotes_received, downvotes_received, comments_count, network_role FROM {user_network_profiles_table_name} WHERE user_id = ? AND org_id = ?",
        (user_id, org_id),
        fetch_one=True,
    )
    if not profile:
        return

    posts_count = profile[0] or 0
    upvotes = profile[1] or 0
    downvotes = profile[2] or 0
    comments = profile[3] or 0
    current_role = profile[4] or "newbie"

    # Learning score: based on task completions (capped at 500)
    completions = await execute_db_operation(
        f"SELECT COUNT(*) FROM {task_completions_table_name} WHERE user_id = ? AND deleted_at IS NULL",
        (user_id,),
        fetch_one=True,
    )
    completion_count = completions[0] if completions else 0
    learning_score = min(completion_count * 10, 500)

    # Contribution score: posts + upvotes + comments (capped at 500)
    contribution_score = min(
        (posts_count * 5) + (upvotes * 3) + (comments * 2),
        500,
    )

    # Endorsement score: placeholder (mentor endorsements would go here)
    endorsement_score = 0

    # Downvote penalty (capped at 200)
    downvote_penalty = min(downvotes * 2, 200)

    total = learning_score + contribution_score + endorsement_score - downvote_penalty
    total = max(0, total)

    badge_tier = compute_badge_tier(total)
    is_mentor = current_role == "mentor"
    network_role = compute_network_role(badge_tier, is_mentor)

    await execute_db_operation(
        f"""UPDATE {user_network_profiles_table_name}
            SET badge_score = ?, badge_tier = ?, learning_score = ?, contribution_score = ?,
                endorsement_score = ?, downvote_penalty = ?, network_role = ?
            WHERE user_id = ? AND org_id = ?""",
        (total, badge_tier, learning_score, contribution_score, endorsement_score, downvote_penalty, network_role, user_id, org_id),
    )
