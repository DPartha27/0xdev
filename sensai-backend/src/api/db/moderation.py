from typing import List, Optional, Dict
from api.utils.db import execute_db_operation, get_new_db_connection
from api.config import (
    flags_table_name,
    users_table_name,
    posts_table_name,
    replies_table_name,
)


async def create_flag(
    reporter_id: int,
    target_type: str,
    target_id: int,
    reason: str,
    description: Optional[str] = None,
) -> int:
    return await execute_db_operation(
        f"""INSERT INTO {flags_table_name}
            (reporter_id, target_type, target_id, reason, description)
            VALUES (?, ?, ?, ?, ?)""",
        (reporter_id, target_type, target_id, reason, description),
        get_last_row_id=True,
    )


async def get_flag(flag_id: int) -> Optional[Dict]:
    row = await execute_db_operation(
        f"""SELECT id, reporter_id, target_type, target_id, reason, description,
                   status, reviewed_by, reviewed_at, action_taken, created_at, updated_at
            FROM {flags_table_name}
            WHERE id = ? AND deleted_at IS NULL""",
        (flag_id,),
        fetch_one=True,
    )
    return _row_to_flag(row) if row else None


async def get_pending_flags(org_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
    """Return pending flags for content in the given org (via posts/replies)."""
    rows = await execute_db_operation(
        f"""SELECT f.id, f.reporter_id, f.target_type, f.target_id, f.reason,
                   f.description, f.status, f.reviewed_by, f.reviewed_at,
                   f.action_taken, f.created_at, f.updated_at
            FROM {flags_table_name} f
            WHERE f.status = 'pending' AND f.deleted_at IS NULL
            ORDER BY f.created_at ASC
            LIMIT ? OFFSET ?""",
        (limit, offset),
        fetch_all=True,
    )
    return [_row_to_flag(r) for r in rows]


async def review_flag(
    flag_id: int,
    reviewed_by: int,
    action_taken: str,
) -> None:
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()

        await cursor.execute(
            f"""UPDATE {flags_table_name}
                SET status = 'actioned', reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP,
                    action_taken = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND deleted_at IS NULL""",
            (reviewed_by, action_taken, flag_id),
        )

        # Apply action to the flagged content
        if action_taken in ("hidden", "deleted"):
            await cursor.execute(
                f"SELECT target_type, target_id FROM {flags_table_name} WHERE id = ?",
                (flag_id,),
            )
            flag_row = await cursor.fetchone()
            if flag_row:
                target_type, target_id = flag_row
                if target_type == "post":
                    if action_taken == "deleted":
                        await cursor.execute(
                            f"UPDATE {posts_table_name} SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (target_id,),
                        )
                    elif action_taken == "hidden":
                        await cursor.execute(
                            f"UPDATE {posts_table_name} SET status = 'archived' WHERE id = ?",
                            (target_id,),
                        )
                elif target_type == "reply":
                    if action_taken == "deleted":
                        await cursor.execute(
                            f"UPDATE {replies_table_name} SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (target_id,),
                        )

        await conn.commit()


async def dismiss_flag(flag_id: int, reviewed_by: int) -> None:
    await execute_db_operation(
        f"""UPDATE {flags_table_name}
            SET status = 'dismissed', reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP,
                action_taken = 'none', updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND deleted_at IS NULL""",
        (reviewed_by, flag_id),
    )


async def get_moderation_stats(org_id: int) -> Dict:
    rows = await execute_db_operation(
        f"""SELECT status, COUNT(*) as count
            FROM {flags_table_name}
            WHERE deleted_at IS NULL
            GROUP BY status""",
        fetch_all=True,
    )
    stats = {"pending": 0, "actioned": 0, "dismissed": 0}
    for row in rows:
        stats[row[0]] = row[1]
    return stats


def _row_to_flag(row) -> Dict:
    return {
        "id": row[0],
        "reporter_id": row[1],
        "target_type": row[2],
        "target_id": row[3],
        "reason": row[4],
        "description": row[5],
        "status": row[6],
        "reviewed_by": row[7],
        "reviewed_at": row[8],
        "action_taken": row[9],
        "created_at": row[10],
        "updated_at": row[11],
    }
