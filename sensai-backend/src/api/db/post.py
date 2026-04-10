import json
from typing import List, Optional, Dict
from api.utils.db import execute_db_operation, get_new_db_connection
from api.config import (
    posts_table_name,
    post_skills_table_name,
    post_tasks_table_name,
    replies_table_name,
    votes_table_name,
    bookmarks_table_name,
    poll_options_table_name,
    poll_votes_table_name,
    endorsements_table_name,
    skills_table_name,
    tasks_table_name,
    users_table_name,
    vote_audit_table_name,
)


# ── Posts ──────────────────────────────────────────────────────────────────────

async def create_post(
    hub_id: int,
    author_id: int,
    post_type: str,
    title: str,
    blocks: Optional[List] = None,
    status: str = "published",
) -> int:
    blocks_json = json.dumps(blocks) if blocks else None
    return await execute_db_operation(
        f"""INSERT INTO {posts_table_name}
            (hub_id, author_id, post_type, title, blocks, status)
            VALUES (?, ?, ?, ?, ?, ?)""",
        (hub_id, author_id, post_type, title, blocks_json, status),
        get_last_row_id=True,
    )


async def get_post(post_id: int) -> Optional[Dict]:
    row = await execute_db_operation(
        f"""SELECT p.id, p.hub_id, p.author_id, u.first_name, u.last_name,
                   p.post_type, p.title, p.blocks, p.status, p.lifecycle_status,
                   p.is_pinned, p.upvote_count, p.downvote_count,
                   p.reply_count, p.view_count, p.accepted_reply_id,
                   p.created_at, p.updated_at
            FROM {posts_table_name} p
            JOIN {users_table_name} u ON u.id = p.author_id
            WHERE p.id = ? AND p.deleted_at IS NULL""",
        (post_id,),
        fetch_one=True,
    )
    if not row:
        return None
    return _row_to_post_detail(row)


async def update_post(
    post_id: int,
    title: Optional[str] = None,
    blocks: Optional[List] = None,
    status: Optional[str] = None,
) -> None:
    fields = []
    params = []
    if title is not None:
        fields.append("title = ?")
        params.append(title)
    if blocks is not None:
        fields.append("blocks = ?")
        params.append(json.dumps(blocks))
    if status is not None:
        fields.append("status = ?")
        params.append(status)
    if not fields:
        return
    fields.append("updated_at = CURRENT_TIMESTAMP")
    params.append(post_id)
    await execute_db_operation(
        f"UPDATE {posts_table_name} SET {', '.join(fields)} WHERE id = ? AND deleted_at IS NULL",
        tuple(params),
    )


async def delete_post(post_id: int) -> None:
    await execute_db_operation(
        f"UPDATE {posts_table_name} SET deleted_at = CURRENT_TIMESTAMP WHERE id = ? AND deleted_at IS NULL",
        (post_id,),
    )


async def increment_view_count(post_id: int) -> None:
    await execute_db_operation(
        f"UPDATE {posts_table_name} SET view_count = view_count + 1 WHERE id = ?",
        (post_id,),
    )


# ── Replies ────────────────────────────────────────────────────────────────────

async def create_reply(
    post_id: int,
    author_id: int,
    blocks: List,
    parent_reply_id: Optional[int] = None,
) -> int:
    blocks_json = json.dumps(blocks)
    reply_id = await execute_db_operation(
        f"""INSERT INTO {replies_table_name}
            (post_id, author_id, blocks, parent_reply_id)
            VALUES (?, ?, ?, ?)""",
        (post_id, author_id, blocks_json, parent_reply_id),
        get_last_row_id=True,
    )
    # Increment denormalized reply count
    await execute_db_operation(
        f"UPDATE {posts_table_name} SET reply_count = reply_count + 1 WHERE id = ?",
        (post_id,),
    )
    return reply_id


async def get_replies_for_post(post_id: int) -> List[Dict]:
    rows = await execute_db_operation(
        f"""SELECT r.id, r.post_id, r.parent_reply_id, r.author_id,
                   u.first_name, u.last_name,
                   r.blocks, r.upvote_count, r.downvote_count, r.is_accepted,
                   r.created_at, r.updated_at,
                   (SELECT COUNT(*) FROM {endorsements_table_name} e
                    WHERE e.reply_id = r.id AND e.deleted_at IS NULL) as endorsement_count
            FROM {replies_table_name} r
            JOIN {users_table_name} u ON u.id = r.author_id
            WHERE r.post_id = ? AND r.deleted_at IS NULL
            ORDER BY r.is_accepted DESC, r.upvote_count DESC, r.created_at ASC""",
        (post_id,),
        fetch_all=True,
    )
    return [_row_to_reply(r) for r in rows]


async def update_reply(reply_id: int, blocks: List) -> None:
    await execute_db_operation(
        f"""UPDATE {replies_table_name}
            SET blocks = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND deleted_at IS NULL""",
        (json.dumps(blocks), reply_id),
    )


async def delete_reply(reply_id: int, post_id: int) -> None:
    await execute_db_operation(
        f"UPDATE {replies_table_name} SET deleted_at = CURRENT_TIMESTAMP WHERE id = ? AND deleted_at IS NULL",
        (reply_id,),
    )
    await execute_db_operation(
        f"UPDATE {posts_table_name} SET reply_count = MAX(0, reply_count - 1) WHERE id = ?",
        (post_id,),
    )


async def accept_reply(post_id: int, reply_id: int) -> None:
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        # Unaccept any previously accepted reply
        await cursor.execute(
            f"UPDATE {replies_table_name} SET is_accepted = 0 WHERE post_id = ? AND is_accepted = 1",
            (post_id,),
        )
        # Accept the new reply
        await cursor.execute(
            f"UPDATE {replies_table_name} SET is_accepted = 1 WHERE id = ?",
            (reply_id,),
        )
        # Set accepted_reply_id on post
        await cursor.execute(
            f"UPDATE {posts_table_name} SET accepted_reply_id = ? WHERE id = ?",
            (reply_id, post_id),
        )
        await conn.commit()


# ── Votes ──────────────────────────────────────────────────────────────────────

async def vote(
    user_id: int,
    target_type: str,
    target_id: int,
    value: int,
    view_duration_ms: Optional[int] = None,
) -> Dict:
    """Cast or update a vote. Returns {'action': 'created'|'updated'|'removed', 'old_value': int|None}."""
    existing = await execute_db_operation(
        f"""SELECT id, value FROM {votes_table_name}
            WHERE user_id = ? AND target_type = ? AND target_id = ? AND deleted_at IS NULL""",
        (user_id, target_type, target_id),
        fetch_one=True,
    )

    table = posts_table_name if target_type == "post" else replies_table_name
    old_value = None

    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()

        if existing:
            old_value = existing[1]
            if old_value == value:
                # Same vote — remove it (toggle)
                await cursor.execute(
                    f"UPDATE {votes_table_name} SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (existing[0],),
                )
                delta_up = -1 if value == 1 else 0
                delta_down = -1 if value == -1 else 0
                action = "removed"
            else:
                # Different vote — update
                await cursor.execute(
                    f"UPDATE {votes_table_name} SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (value, existing[0]),
                )
                delta_up = 1 if value == 1 else -1
                delta_down = 1 if value == -1 else -1
                action = "updated"
        else:
            # New vote
            await cursor.execute(
                f"INSERT INTO {votes_table_name} (user_id, target_type, target_id, value) VALUES (?, ?, ?, ?)",
                (user_id, target_type, target_id, value),
            )
            delta_up = 1 if value == 1 else 0
            delta_down = 1 if value == -1 else 0
            action = "created"

        # Update denormalized counts
        if delta_up != 0:
            await cursor.execute(
                f"UPDATE {table} SET upvote_count = MAX(0, upvote_count + ?) WHERE id = ?",
                (delta_up, target_id),
            )
        if delta_down != 0:
            await cursor.execute(
                f"UPDATE {table} SET downvote_count = MAX(0, downvote_count + ?) WHERE id = ?",
                (delta_down, target_id),
            )

        await conn.commit()

    # Record vote audit
    if target_type == "post":
        recipient_row = await execute_db_operation(
            f"SELECT author_id FROM {posts_table_name} WHERE id = ?",
            (target_id,),
            fetch_one=True,
        )
    else:
        recipient_row = await execute_db_operation(
            f"SELECT author_id FROM {replies_table_name} WHERE id = ?",
            (target_id,),
            fetch_one=True,
        )

    if recipient_row and action == "created":
        await execute_db_operation(
            f"""INSERT INTO {vote_audit_table_name}
                (voter_id, recipient_id, {'post_id' if target_type == 'post' else 'reply_id'}, vote_type, view_duration_ms)
                VALUES (?, ?, ?, ?, ?)""",
            (user_id, recipient_row[0], target_id, "up" if value == 1 else "down", view_duration_ms),
        )

    return {"action": action, "old_value": old_value}


async def get_user_vote(user_id: int, target_type: str, target_id: int) -> Optional[int]:
    row = await execute_db_operation(
        f"""SELECT value FROM {votes_table_name}
            WHERE user_id = ? AND target_type = ? AND target_id = ? AND deleted_at IS NULL""",
        (user_id, target_type, target_id),
        fetch_one=True,
    )
    return row[0] if row else None


# ── Bookmarks ─────────────────────────────────────────────────────────────────

async def toggle_bookmark(user_id: int, post_id: int) -> str:
    existing = await execute_db_operation(
        f"""SELECT id FROM {bookmarks_table_name}
            WHERE user_id = ? AND post_id = ? AND deleted_at IS NULL""",
        (user_id, post_id),
        fetch_one=True,
    )
    if existing:
        await execute_db_operation(
            f"UPDATE {bookmarks_table_name} SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?",
            (existing[0],),
        )
        return "removed"
    else:
        await execute_db_operation(
            f"INSERT INTO {bookmarks_table_name} (user_id, post_id) VALUES (?, ?)",
            (user_id, post_id),
        )
        return "added"


async def is_bookmarked(user_id: int, post_id: int) -> bool:
    row = await execute_db_operation(
        f"""SELECT id FROM {bookmarks_table_name}
            WHERE user_id = ? AND post_id = ? AND deleted_at IS NULL""",
        (user_id, post_id),
        fetch_one=True,
    )
    return row is not None


async def get_bookmarks_for_user(user_id: int) -> List[Dict]:
    rows = await execute_db_operation(
        f"""SELECT p.id, p.hub_id, p.author_id, u.first_name, u.last_name,
                   p.post_type, p.title, p.status, p.lifecycle_status,
                   p.is_pinned, p.upvote_count, p.downvote_count,
                   p.reply_count, p.view_count, p.accepted_reply_id,
                   p.created_at, p.updated_at
            FROM {bookmarks_table_name} b
            JOIN {posts_table_name} p ON p.id = b.post_id
            JOIN {users_table_name} u ON u.id = p.author_id
            WHERE b.user_id = ? AND b.deleted_at IS NULL AND p.deleted_at IS NULL
            ORDER BY b.created_at DESC""",
        (user_id,),
        fetch_all=True,
    )
    return [_row_to_post_summary(r) for r in rows]


# ── Poll ──────────────────────────────────────────────────────────────────────

async def create_poll_options(post_id: int, options: List[str]) -> None:
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        for i, text in enumerate(options):
            await cursor.execute(
                f"INSERT INTO {poll_options_table_name} (post_id, text, position) VALUES (?, ?, ?)",
                (post_id, text, i),
            )
        await conn.commit()


async def get_poll_options(post_id: int) -> List[Dict]:
    rows = await execute_db_operation(
        f"""SELECT id, post_id, text, position, vote_count
            FROM {poll_options_table_name}
            WHERE post_id = ? AND deleted_at IS NULL
            ORDER BY position ASC""",
        (post_id,),
        fetch_all=True,
    )
    return [
        {"id": r[0], "post_id": r[1], "text": r[2], "position": r[3], "vote_count": r[4]}
        for r in rows
    ]


async def vote_poll(user_id: int, post_id: int, option_id: int) -> None:
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        # Check existing vote
        await cursor.execute(
            f"SELECT id, poll_option_id FROM {poll_votes_table_name} WHERE user_id = ? AND post_id = ? AND deleted_at IS NULL",
            (user_id, post_id),
        )
        existing = await cursor.fetchone()
        if existing:
            old_option_id = existing[1]
            # Decrement old option
            await cursor.execute(
                f"UPDATE {poll_options_table_name} SET vote_count = MAX(0, vote_count - 1) WHERE id = ?",
                (old_option_id,),
            )
            # Remove old vote
            await cursor.execute(
                f"UPDATE {poll_votes_table_name} SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?",
                (existing[0],),
            )
        # Insert new vote
        await cursor.execute(
            f"INSERT INTO {poll_votes_table_name} (user_id, poll_option_id, post_id) VALUES (?, ?, ?)",
            (user_id, option_id, post_id),
        )
        # Increment new option
        await cursor.execute(
            f"UPDATE {poll_options_table_name} SET vote_count = vote_count + 1 WHERE id = ?",
            (option_id,),
        )
        await conn.commit()


# ── Skills / Tasks Linking ─────────────────────────────────────────────────────

async def link_skills_to_post(post_id: int, skill_ids: List[int]) -> None:
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        for skill_id in skill_ids:
            await cursor.execute(
                f"INSERT OR IGNORE INTO {post_skills_table_name} (post_id, skill_id) VALUES (?, ?)",
                (post_id, skill_id),
            )
        await conn.commit()


async def link_tasks_to_post(post_id: int, task_ids: List[int], relation_type: str = "related") -> None:
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        for task_id in task_ids:
            await cursor.execute(
                f"""INSERT INTO {post_tasks_table_name} (post_id, task_id, relation_type)
                    VALUES (?, ?, ?)
                    ON CONFLICT(post_id, task_id) DO UPDATE SET
                        relation_type = excluded.relation_type,
                        deleted_at = NULL""",
                (post_id, task_id, relation_type),
            )
        await conn.commit()


async def get_skills_for_post(post_id: int) -> List[Dict]:
    rows = await execute_db_operation(
        f"""SELECT s.id, s.org_id, s.name, s.slug, s.description, s.parent_skill_id,
                   s.created_at, s.updated_at
            FROM {skills_table_name} s
            JOIN {post_skills_table_name} ps ON ps.skill_id = s.id
            WHERE ps.post_id = ? AND ps.deleted_at IS NULL AND s.deleted_at IS NULL""",
        (post_id,),
        fetch_all=True,
    )
    return [
        {
            "id": r[0], "org_id": r[1], "name": r[2], "slug": r[3],
            "description": r[4], "parent_skill_id": r[5],
            "created_at": r[6], "updated_at": r[7],
        }
        for r in rows
    ]


async def get_tasks_for_post(post_id: int) -> List[Dict]:
    rows = await execute_db_operation(
        f"""SELECT t.id, t.title, t.type, pt.relation_type
            FROM {tasks_table_name} t
            JOIN {post_tasks_table_name} pt ON pt.task_id = t.id
            WHERE pt.post_id = ? AND pt.deleted_at IS NULL AND t.deleted_at IS NULL""",
        (post_id,),
        fetch_all=True,
    )
    return [
        {"id": r[0], "title": r[1], "type": r[2], "relation_type": r[3]}
        for r in rows
    ]


# ── Endorsements ───────────────────────────────────────────────────────────────

async def get_reply_author_id(reply_id: int) -> Optional[int]:
    row = await execute_db_operation(
        f"SELECT author_id FROM {replies_table_name} WHERE id = ? AND deleted_at IS NULL",
        (reply_id,),
        fetch_one=True,
    )
    return row[0] if row else None


async def endorse_reply(endorser_id: int, reply_id: int, skill_id: Optional[int] = None) -> None:
    await execute_db_operation(
        f"""INSERT INTO {endorsements_table_name} (endorser_id, reply_id, skill_id)
            VALUES (?, ?, ?)
            ON CONFLICT(endorser_id, reply_id) DO UPDATE SET
                skill_id = excluded.skill_id,
                deleted_at = NULL""",
        (endorser_id, reply_id, skill_id),
    )


# ── Lifecycle ──────────────────────────────────────────────────────────────────

async def update_post_lifecycle(post_id: int, lifecycle_status: str) -> None:
    await execute_db_operation(
        f"""UPDATE {posts_table_name}
            SET lifecycle_status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND deleted_at IS NULL""",
        (lifecycle_status, post_id),
    )


async def get_posts_for_staleness_check() -> List[Dict]:
    """Return posts that should be checked for lifecycle transitions."""
    rows = await execute_db_operation(
        f"""SELECT id, lifecycle_status, updated_at, upvote_count, reply_count
            FROM {posts_table_name}
            WHERE deleted_at IS NULL
              AND lifecycle_status IN ('active', 'stale')
              AND status = 'published'""",
        fetch_all=True,
    )
    return [
        {
            "id": r[0],
            "lifecycle_status": r[1],
            "updated_at": r[2],
            "upvote_count": r[3],
            "reply_count": r[4],
        }
        for r in rows
    ]


async def search_tasks_for_org(org_id: int, query: str, limit: int = 10) -> List[Dict]:
    """Search tasks belonging to courses in an org by title (for post task-linking)."""
    rows = await execute_db_operation(
        f"""SELECT DISTINCT t.id, t.title, t.type
            FROM {tasks_table_name} t
            JOIN course_tasks ct ON ct.task_id = t.id
            JOIN courses c ON c.id = ct.course_id
            WHERE c.org_id = ? AND t.title LIKE ? AND t.deleted_at IS NULL
            ORDER BY t.title
            LIMIT ?""",
        (org_id, f"%{query}%", limit),
        fetch_all=True,
    )
    return [{"id": r[0], "title": r[1], "type": r[2]} for r in rows]


async def get_posts_by_user(user_id: int) -> List[Dict]:
    rows = await execute_db_operation(
        f"""SELECT p.id, p.hub_id, p.author_id, u.first_name, u.last_name,
                   p.post_type, p.title, p.status, p.lifecycle_status,
                   p.is_pinned, p.upvote_count, p.downvote_count,
                   p.reply_count, p.view_count, p.accepted_reply_id,
                   p.created_at, p.updated_at
            FROM {posts_table_name} p
            JOIN {users_table_name} u ON u.id = p.author_id
            WHERE p.author_id = ? AND p.deleted_at IS NULL
            ORDER BY p.created_at DESC""",
        (user_id,),
        fetch_all=True,
    )
    return [_row_to_post_summary(r) for r in rows]


# ── Private helpers ────────────────────────────────────────────────────────────

def _row_to_post_summary(row) -> Dict:
    return {
        "id": row[0],
        "hub_id": row[1],
        "author_id": row[2],
        "author_name": f"{row[3] or ''} {row[4] or ''}".strip(),
        "post_type": row[5],
        "title": row[6],
        "status": row[7],
        "lifecycle_status": row[8],
        "is_pinned": bool(row[9]),
        "upvote_count": row[10],
        "downvote_count": row[11],
        "reply_count": row[12],
        "view_count": row[13],
        "has_accepted_answer": row[14] is not None,
        "created_at": row[15],
        "updated_at": row[16],
    }


def _row_to_post_detail(row) -> Dict:
    blocks = None
    if row[7]:
        try:
            blocks = json.loads(row[7])
        except (json.JSONDecodeError, TypeError):
            blocks = row[7]
    return {
        "id": row[0],
        "hub_id": row[1],
        "author_id": row[2],
        "author_name": f"{row[3] or ''} {row[4] or ''}".strip(),
        "post_type": row[5],
        "title": row[6],
        "blocks": blocks,
        "status": row[8],
        "lifecycle_status": row[9],
        "is_pinned": bool(row[10]),
        "upvote_count": row[11],
        "downvote_count": row[12],
        "reply_count": row[13],
        "view_count": row[14],
        "has_accepted_answer": row[15] is not None,
        "created_at": row[16],
        "updated_at": row[17],
    }


def _row_to_reply(row) -> Dict:
    blocks = None
    if row[6]:
        try:
            blocks = json.loads(row[6])
        except (json.JSONDecodeError, TypeError):
            blocks = row[6]
    return {
        "id": row[0],
        "post_id": row[1],
        "parent_reply_id": row[2],
        "author_id": row[3],
        "author_name": f"{row[4] or ''} {row[5] or ''}".strip(),
        "blocks": blocks,
        "upvote_count": row[7],
        "downvote_count": row[8],
        "is_accepted": bool(row[9]),
        "created_at": row[10],
        "updated_at": row[11],
        "endorsement_count": row[12],
    }
