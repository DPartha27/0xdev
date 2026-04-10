import json
from typing import List, Optional, Dict
from api.utils.db import execute_db_operation, get_new_db_connection
from api.config import (
    hubs_table_name,
    hub_members_table_name,
    hub_skills_table_name,
    hub_courses_table_name,
    skills_table_name,
    users_table_name,
    posts_table_name,
)


async def create_hub(
    org_id: int,
    name: str,
    slug: str,
    created_by: int,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    visibility: str = "public",
) -> int:
    hub_id = await execute_db_operation(
        f"""INSERT INTO {hubs_table_name}
            (org_id, name, slug, description, icon, visibility, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (org_id, name, slug, description, icon, visibility, created_by),
        get_last_row_id=True,
    )
    # Auto-add creator as owner
    await execute_db_operation(
        f"""INSERT OR IGNORE INTO {hub_members_table_name} (hub_id, user_id, role)
            VALUES (?, ?, 'owner')""",
        (hub_id, created_by),
    )
    return hub_id


async def get_hub(hub_id: int) -> Optional[Dict]:
    row = await execute_db_operation(
        f"""SELECT h.id, h.org_id, h.name, h.slug, h.description, h.icon,
                   h.visibility, h.created_by, h.created_at, h.updated_at,
                   (SELECT COUNT(*) FROM {hub_members_table_name} hm
                    WHERE hm.hub_id = h.id AND hm.deleted_at IS NULL) as member_count,
                   (SELECT COUNT(*) FROM {posts_table_name} p
                    WHERE p.hub_id = h.id AND p.deleted_at IS NULL AND p.status = 'published') as post_count
            FROM {hubs_table_name} h
            WHERE h.id = ? AND h.deleted_at IS NULL""",
        (hub_id,),
        fetch_one=True,
    )
    if not row:
        return None
    hub = _row_to_hub(row)
    hub["skills"] = await get_skills_for_hub(hub_id)
    return hub


async def get_hub_by_slug(org_id: int, slug: str) -> Optional[Dict]:
    row = await execute_db_operation(
        f"""SELECT h.id, h.org_id, h.name, h.slug, h.description, h.icon,
                   h.visibility, h.created_by, h.created_at, h.updated_at,
                   (SELECT COUNT(*) FROM {hub_members_table_name} hm
                    WHERE hm.hub_id = h.id AND hm.deleted_at IS NULL) as member_count,
                   (SELECT COUNT(*) FROM {posts_table_name} p
                    WHERE p.hub_id = h.id AND p.deleted_at IS NULL AND p.status = 'published') as post_count
            FROM {hubs_table_name} h
            WHERE h.org_id = ? AND h.slug = ? AND h.deleted_at IS NULL""",
        (org_id, slug),
        fetch_one=True,
    )
    if not row:
        return None
    hub = _row_to_hub(row)
    hub["skills"] = await get_skills_for_hub(hub["id"])
    return hub


async def get_hubs_for_org(org_id: int) -> List[Dict]:
    rows = await execute_db_operation(
        f"""SELECT h.id, h.org_id, h.name, h.slug, h.description, h.icon,
                   h.visibility, h.created_by, h.created_at, h.updated_at,
                   (SELECT COUNT(*) FROM {hub_members_table_name} hm
                    WHERE hm.hub_id = h.id AND hm.deleted_at IS NULL) as member_count,
                   (SELECT COUNT(*) FROM {posts_table_name} p
                    WHERE p.hub_id = h.id AND p.deleted_at IS NULL AND p.status = 'published') as post_count
            FROM {hubs_table_name} h
            WHERE h.org_id = ? AND h.deleted_at IS NULL
            ORDER BY h.created_at DESC""",
        (org_id,),
        fetch_all=True,
    )
    hubs = [_row_to_hub(r) for r in rows]
    for hub in hubs:
        hub["skills"] = await get_skills_for_hub(hub["id"])
    return hubs


async def update_hub(
    hub_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    icon: Optional[str] = None,
    visibility: Optional[str] = None,
) -> None:
    fields = []
    params = []
    if name is not None:
        fields.append("name = ?")
        params.append(name)
    if description is not None:
        fields.append("description = ?")
        params.append(description)
    if icon is not None:
        fields.append("icon = ?")
        params.append(icon)
    if visibility is not None:
        fields.append("visibility = ?")
        params.append(visibility)
    if not fields:
        return
    fields.append("updated_at = CURRENT_TIMESTAMP")
    params.append(hub_id)
    await execute_db_operation(
        f"UPDATE {hubs_table_name} SET {', '.join(fields)} WHERE id = ? AND deleted_at IS NULL",
        tuple(params),
    )


async def delete_hub(hub_id: int) -> None:
    await execute_db_operation(
        f"UPDATE {hubs_table_name} SET deleted_at = CURRENT_TIMESTAMP WHERE id = ? AND deleted_at IS NULL",
        (hub_id,),
    )


async def add_hub_members(hub_id: int, user_ids: List[int], role: str = "member") -> None:
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        for user_id in user_ids:
            await cursor.execute(
                f"""INSERT INTO {hub_members_table_name} (hub_id, user_id, role)
                    VALUES (?, ?, ?)
                    ON CONFLICT(hub_id, user_id) DO UPDATE SET
                        role = excluded.role,
                        deleted_at = NULL,
                        updated_at = CURRENT_TIMESTAMP""",
                (hub_id, user_id, role),
            )
        await conn.commit()


async def remove_hub_members(hub_id: int, user_ids: List[int]) -> None:
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        for user_id in user_ids:
            await cursor.execute(
                f"""UPDATE {hub_members_table_name}
                    SET deleted_at = CURRENT_TIMESTAMP
                    WHERE hub_id = ? AND user_id = ? AND deleted_at IS NULL""",
                (hub_id, user_id),
            )
        await conn.commit()


async def update_hub_member_role(hub_id: int, user_id: int, role: str) -> None:
    await execute_db_operation(
        f"""UPDATE {hub_members_table_name}
            SET role = ?, updated_at = CURRENT_TIMESTAMP
            WHERE hub_id = ? AND user_id = ? AND deleted_at IS NULL""",
        (role, hub_id, user_id),
    )


async def get_hub_member_role(hub_id: int, user_id: int) -> Optional[str]:
    row = await execute_db_operation(
        f"""SELECT role FROM {hub_members_table_name}
            WHERE hub_id = ? AND user_id = ? AND deleted_at IS NULL""",
        (hub_id, user_id),
        fetch_one=True,
    )
    return row[0] if row else None


async def link_skills_to_hub(hub_id: int, skill_ids: List[int]) -> None:
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        for skill_id in skill_ids:
            await cursor.execute(
                f"""INSERT OR IGNORE INTO {hub_skills_table_name} (hub_id, skill_id)
                    VALUES (?, ?)""",
                (hub_id, skill_id),
            )
        await conn.commit()


async def unlink_skills_from_hub(hub_id: int, skill_ids: List[int]) -> None:
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        for skill_id in skill_ids:
            await cursor.execute(
                f"""UPDATE {hub_skills_table_name}
                    SET deleted_at = CURRENT_TIMESTAMP
                    WHERE hub_id = ? AND skill_id = ? AND deleted_at IS NULL""",
                (hub_id, skill_id),
            )
        await conn.commit()


async def link_courses_to_hub(hub_id: int, course_ids: List[int]) -> None:
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        for course_id in course_ids:
            await cursor.execute(
                f"""INSERT OR IGNORE INTO {hub_courses_table_name} (hub_id, course_id)
                    VALUES (?, ?)""",
                (hub_id, course_id),
            )
        await conn.commit()


async def unlink_courses_from_hub(hub_id: int, course_ids: List[int]) -> None:
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        for course_id in course_ids:
            await cursor.execute(
                f"""UPDATE {hub_courses_table_name}
                    SET deleted_at = CURRENT_TIMESTAMP
                    WHERE hub_id = ? AND course_id = ? AND deleted_at IS NULL""",
                (hub_id, course_id),
            )
        await conn.commit()


async def get_skills_for_hub(hub_id: int) -> List[Dict]:
    rows = await execute_db_operation(
        f"""SELECT s.id, s.org_id, s.name, s.slug, s.description, s.parent_skill_id,
                   s.created_at, s.updated_at
            FROM {skills_table_name} s
            JOIN {hub_skills_table_name} hs ON hs.skill_id = s.id
            WHERE hs.hub_id = ? AND hs.deleted_at IS NULL AND s.deleted_at IS NULL""",
        (hub_id,),
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


async def get_hub_feed(
    hub_id: int,
    sort: str = "newest",
    post_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[Dict]:
    type_filter = "AND p.post_type = ?" if post_type else ""
    type_param = (post_type,) if post_type else ()

    if sort == "popular":
        order = "p.upvote_count DESC, p.reply_count DESC"
    elif sort == "unanswered":
        order = "p.reply_count ASC, p.created_at DESC"
        type_filter += " AND p.post_type = 'question' AND p.accepted_reply_id IS NULL"
    else:
        order = "p.created_at DESC"

    rows = await execute_db_operation(
        f"""SELECT p.id, p.hub_id, p.author_id, u.first_name, u.last_name,
                   p.post_type, p.title, p.status, p.lifecycle_status,
                   p.is_pinned, p.upvote_count, p.downvote_count,
                   p.reply_count, p.view_count, p.accepted_reply_id,
                   p.created_at, p.updated_at
            FROM {posts_table_name} p
            JOIN {users_table_name} u ON u.id = p.author_id
            WHERE p.hub_id = ? AND p.deleted_at IS NULL AND p.status = 'published'
              AND p.lifecycle_status != 'archived'
              {type_filter}
            ORDER BY p.is_pinned DESC, {order}
            LIMIT ? OFFSET ?""",
        (hub_id, *type_param, limit, offset),
        fetch_all=True,
    )
    return [_row_to_post_summary(r) for r in rows]


def _row_to_hub(row) -> Dict:
    return {
        "id": row[0],
        "org_id": row[1],
        "name": row[2],
        "slug": row[3],
        "description": row[4],
        "icon": row[5],
        "visibility": row[6],
        "created_by": row[7],
        "created_at": row[8],
        "updated_at": row[9],
        "member_count": row[10],
        "post_count": row[11],
    }


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
