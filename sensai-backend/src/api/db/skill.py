from typing import List, Optional, Dict
from api.utils.db import execute_db_operation, get_new_db_connection
from api.config import (
    skills_table_name,
    task_skills_table_name,
    user_skills_table_name,
    organizations_table_name,
    users_table_name,
    tasks_table_name,
    hub_skills_table_name,
    post_skills_table_name,
    hubs_table_name,
    posts_table_name,
)


async def create_skill(
    org_id: int,
    name: str,
    slug: str,
    description: Optional[str] = None,
    parent_skill_id: Optional[int] = None,
) -> int:
    return await execute_db_operation(
        f"""INSERT INTO {skills_table_name}
            (org_id, name, slug, description, parent_skill_id)
            VALUES (?, ?, ?, ?, ?)""",
        (org_id, name, slug, description, parent_skill_id),
        get_last_row_id=True,
    )


async def get_skill(skill_id: int) -> Optional[Dict]:
    row = await execute_db_operation(
        f"""SELECT id, org_id, name, slug, description, parent_skill_id, created_at, updated_at
            FROM {skills_table_name}
            WHERE id = ? AND deleted_at IS NULL""",
        (skill_id,),
        fetch_one=True,
    )
    if not row:
        return None
    return _row_to_skill(row)


async def get_skills_for_org(org_id: int) -> List[Dict]:
    rows = await execute_db_operation(
        f"""SELECT id, org_id, name, slug, description, parent_skill_id, created_at, updated_at
            FROM {skills_table_name}
            WHERE org_id = ? AND deleted_at IS NULL
            ORDER BY name ASC""",
        (org_id,),
        fetch_all=True,
    )
    return [_row_to_skill(r) for r in rows]


async def update_skill(
    skill_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    parent_skill_id: Optional[int] = None,
) -> None:
    fields = []
    params = []
    if name is not None:
        fields.append("name = ?")
        params.append(name)
    if description is not None:
        fields.append("description = ?")
        params.append(description)
    if parent_skill_id is not None:
        fields.append("parent_skill_id = ?")
        params.append(parent_skill_id)
    if not fields:
        return
    fields.append("updated_at = CURRENT_TIMESTAMP")
    params.append(skill_id)
    await execute_db_operation(
        f"UPDATE {skills_table_name} SET {', '.join(fields)} WHERE id = ? AND deleted_at IS NULL",
        tuple(params),
    )


async def delete_skill(skill_id: int) -> None:
    await execute_db_operation(
        f"UPDATE {skills_table_name} SET deleted_at = CURRENT_TIMESTAMP WHERE id = ? AND deleted_at IS NULL",
        (skill_id,),
    )


async def link_skills_to_task(task_id: int, skill_ids: List[int]) -> None:
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        for skill_id in skill_ids:
            await cursor.execute(
                f"""INSERT OR IGNORE INTO {task_skills_table_name} (task_id, skill_id)
                    VALUES (?, ?)""",
                (task_id, skill_id),
            )
        await conn.commit()


async def unlink_skills_from_task(task_id: int, skill_ids: List[int]) -> None:
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        for skill_id in skill_ids:
            await cursor.execute(
                f"""UPDATE {task_skills_table_name}
                    SET deleted_at = CURRENT_TIMESTAMP
                    WHERE task_id = ? AND skill_id = ? AND deleted_at IS NULL""",
                (task_id, skill_id),
            )
        await conn.commit()


async def get_skills_for_task(task_id: int) -> List[Dict]:
    rows = await execute_db_operation(
        f"""SELECT s.id, s.org_id, s.name, s.slug, s.description, s.parent_skill_id,
                   s.created_at, s.updated_at
            FROM {skills_table_name} s
            JOIN {task_skills_table_name} ts ON ts.skill_id = s.id
            WHERE ts.task_id = ? AND ts.deleted_at IS NULL AND s.deleted_at IS NULL""",
        (task_id,),
        fetch_all=True,
    )
    return [_row_to_skill(r) for r in rows]


async def get_user_skill_profile(user_id: int) -> List[Dict]:
    rows = await execute_db_operation(
        f"""SELECT s.id, s.name, s.slug, s.description, s.parent_skill_id,
                   us.proficiency_level, us.evidence_count, us.updated_at
            FROM {user_skills_table_name} us
            JOIN {skills_table_name} s ON s.id = us.skill_id
            WHERE us.user_id = ? AND us.deleted_at IS NULL AND s.deleted_at IS NULL
            ORDER BY us.proficiency_level DESC""",
        (user_id,),
        fetch_all=True,
    )
    return [
        {
            "skill_id": r[0],
            "skill_name": r[1],
            "slug": r[2],
            "description": r[3],
            "parent_skill_id": r[4],
            "proficiency_level": r[5],
            "evidence_count": r[6],
            "updated_at": r[7],
        }
        for r in rows
    ]


async def update_user_skill_proficiency(
    user_id: int, skill_id: int, delta: int = 1
) -> None:
    """Upsert user skill proficiency, incrementing evidence_count."""
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            f"""INSERT INTO {user_skills_table_name} (user_id, skill_id, proficiency_level, evidence_count)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(user_id, skill_id) DO UPDATE SET
                    proficiency_level = MIN(100, proficiency_level + ?),
                    evidence_count = evidence_count + 1,
                    updated_at = CURRENT_TIMESTAMP,
                    deleted_at = NULL""",
            (user_id, skill_id, delta, delta),
        )
        await conn.commit()


async def get_skill_graph(skill_id: int) -> Dict:
    """Return related posts, tasks, hubs for a skill."""
    linked_tasks = await execute_db_operation(
        f"""SELECT t.id, t.title, t.type
            FROM {tasks_table_name} t
            JOIN {task_skills_table_name} ts ON ts.task_id = t.id
            WHERE ts.skill_id = ? AND ts.deleted_at IS NULL AND t.deleted_at IS NULL
            LIMIT 20""",
        (skill_id,),
        fetch_all=True,
    )
    linked_hubs = await execute_db_operation(
        f"""SELECT h.id, h.name, h.slug, h.description
            FROM {hubs_table_name} h
            JOIN {hub_skills_table_name} hs ON hs.hub_id = h.id
            WHERE hs.skill_id = ? AND hs.deleted_at IS NULL AND h.deleted_at IS NULL
            LIMIT 20""",
        (skill_id,),
        fetch_all=True,
    )
    linked_posts = await execute_db_operation(
        f"""SELECT p.id, p.title, p.post_type, p.upvote_count, p.reply_count
            FROM {posts_table_name} p
            JOIN {post_skills_table_name} ps ON ps.post_id = p.id
            WHERE ps.skill_id = ? AND ps.deleted_at IS NULL AND p.deleted_at IS NULL
            ORDER BY p.upvote_count DESC
            LIMIT 20""",
        (skill_id,),
        fetch_all=True,
    )
    return {
        "tasks": [
            {"id": r[0], "title": r[1], "type": r[2]} for r in linked_tasks
        ],
        "hubs": [
            {"id": r[0], "name": r[1], "slug": r[2], "description": r[3]}
            for r in linked_hubs
        ],
        "posts": [
            {
                "id": r[0],
                "title": r[1],
                "post_type": r[2],
                "upvote_count": r[3],
                "reply_count": r[4],
            }
            for r in linked_posts
        ],
    }


def _row_to_skill(row) -> Dict:
    return {
        "id": row[0],
        "org_id": row[1],
        "name": row[2],
        "slug": row[3],
        "description": row[4],
        "parent_skill_id": row[5],
        "created_at": row[6],
        "updated_at": row[7],
    }
