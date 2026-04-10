from typing import List, Optional, Dict
from api.utils.db import execute_db_operation, get_new_db_connection
from api.config import (
    reputation_events_table_name,
    user_reputation_table_name,
    vote_audit_table_name,
    users_table_name,
    organizations_table_name,
    REPUTATION_LEVELS,
    REPUTATION_POINTS,
    REPUTATION_DAILY_CAP,
)


def _compute_level(points: int) -> str:
    level = "newcomer"
    for lvl, threshold in sorted(REPUTATION_LEVELS.items(), key=lambda x: x[1]):
        if points >= threshold:
            level = lvl
    return level


async def log_reputation_event(
    user_id: int,
    org_id: Optional[int],
    event_type: str,
    source_type: Optional[str] = None,
    source_id: Optional[int] = None,
    granted_by: Optional[int] = None,
) -> None:
    """Log a reputation event and update the materialized user_reputation table."""
    if org_id is None:
        return  # org_id is required; skip if not resolvable

    points = REPUTATION_POINTS.get(event_type, 0)
    if points == 0:
        return

    # Check daily cap for positive events
    if points > 0:
        daily_total = await execute_db_operation(
            f"""SELECT COALESCE(SUM(points), 0)
                FROM {reputation_events_table_name}
                WHERE user_id = ? AND org_id = ? AND points > 0
                  AND created_at >= datetime('now', '-1 day')""",
            (user_id, org_id),
            fetch_one=True,
        )
        if daily_total and daily_total[0] >= REPUTATION_DAILY_CAP:
            return  # Daily cap hit

    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()

        # Insert event
        await cursor.execute(
            f"""INSERT INTO {reputation_events_table_name}
                (user_id, org_id, event_type, points, source_type, source_id, granted_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, org_id, event_type, points, source_type, source_id, granted_by),
        )

        # Upsert materialized reputation
        await cursor.execute(
            f"""INSERT INTO {user_reputation_table_name} (user_id, org_id, total_points, level)
                VALUES (?, ?, ?, 'newcomer')
                ON CONFLICT(user_id, org_id) DO UPDATE SET
                    total_points = total_points + ?,
                    updated_at = CURRENT_TIMESTAMP""",
            (user_id, org_id, points, points),
        )

        # Update level
        await cursor.execute(
            f"SELECT total_points FROM {user_reputation_table_name} WHERE user_id = ? AND org_id = ?",
            (user_id, org_id),
        )
        row = await cursor.fetchone()
        if row:
            new_level = _compute_level(row[0])
            await cursor.execute(
                f"""UPDATE {user_reputation_table_name}
                    SET level = ? WHERE user_id = ? AND org_id = ?""",
                (new_level, user_id, org_id),
            )

        await conn.commit()


async def get_user_reputation(user_id: int, org_id: int) -> Optional[Dict]:
    row = await execute_db_operation(
        f"""SELECT user_id, org_id, total_points, level, updated_at
            FROM {user_reputation_table_name}
            WHERE user_id = ? AND org_id = ?""",
        (user_id, org_id),
        fetch_one=True,
    )
    if not row:
        return {
            "user_id": user_id,
            "org_id": org_id,
            "total_points": 0,
            "level": "newcomer",
            "updated_at": None,
        }
    return {
        "user_id": row[0],
        "org_id": row[1],
        "total_points": row[2],
        "level": row[3],
        "updated_at": row[4],
    }


async def get_reputation_leaderboard(org_id: int, limit: int = 20, offset: int = 0) -> List[Dict]:
    rows = await execute_db_operation(
        f"""SELECT ur.user_id, u.first_name, u.last_name, u.email,
                   ur.total_points, ur.level, ur.updated_at
            FROM {user_reputation_table_name} ur
            JOIN {users_table_name} u ON u.id = ur.user_id
            WHERE ur.org_id = ?
            ORDER BY ur.total_points DESC
            LIMIT ? OFFSET ?""",
        (org_id, limit, offset),
        fetch_all=True,
    )
    return [
        {
            "user_id": r[0],
            "user_name": f"{r[1] or ''} {r[2] or ''}".strip(),
            "email": r[3],
            "total_points": r[4],
            "level": r[5],
            "updated_at": r[6],
        }
        for r in rows
    ]


async def get_reputation_history(user_id: int, org_id: int, limit: int = 50) -> List[Dict]:
    rows = await execute_db_operation(
        f"""SELECT id, event_type, points, source_type, source_id, created_at
            FROM {reputation_events_table_name}
            WHERE user_id = ? AND org_id = ?
            ORDER BY created_at DESC
            LIMIT ?""",
        (user_id, org_id, limit),
        fetch_all=True,
    )
    return [
        {
            "id": r[0],
            "event_type": r[1],
            "points": r[2],
            "source_type": r[3],
            "source_id": r[4],
            "created_at": r[5],
        }
        for r in rows
    ]


async def recalculate_reputation(user_id: int, org_id: int) -> None:
    """Recalculate total_points from events table to fix drift."""
    row = await execute_db_operation(
        f"""SELECT COALESCE(SUM(points), 0)
            FROM {reputation_events_table_name}
            WHERE user_id = ? AND org_id = ?""",
        (user_id, org_id),
        fetch_one=True,
    )
    total = row[0] if row else 0
    level = _compute_level(total)
    await execute_db_operation(
        f"""INSERT INTO {user_reputation_table_name} (user_id, org_id, total_points, level)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, org_id) DO UPDATE SET
                total_points = ?,
                level = ?,
                updated_at = CURRENT_TIMESTAMP""",
        (user_id, org_id, total, level, total, level),
    )


async def detect_vote_rings(org_id: int) -> List[Dict]:
    """Detect mutual voting patterns for anti-gaming. Returns suspicious pairs."""
    rows = await execute_db_operation(
        f"""SELECT v1.voter_id, v1.recipient_id, COUNT(*) as mutual_votes
            FROM {vote_audit_table_name} v1
            JOIN {vote_audit_table_name} v2
              ON v1.voter_id = v2.recipient_id AND v1.recipient_id = v2.voter_id
            WHERE v1.created_at > datetime('now', '-7 days')
            GROUP BY v1.voter_id, v1.recipient_id
            HAVING mutual_votes > 5""",
        fetch_all=True,
    )
    return [
        {"voter_id": r[0], "recipient_id": r[1], "mutual_votes": r[2]}
        for r in rows
    ]
