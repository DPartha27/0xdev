import json
import re
from typing import List, Dict, Optional
from api.config import (
    network_posts_table_name,
    network_tags_table_name,
    network_post_tags_table_name,
    network_comments_table_name,
    network_votes_table_name,
    network_poll_options_table_name,
    network_poll_votes_table_name,
    user_network_profiles_table_name,
    users_table_name,
    user_cohorts_table_name,
    course_cohorts_table_name,
    course_tasks_table_name,
    task_completions_table_name,
    user_organizations_table_name,
)
from api.utils.db import (
    execute_db_operation,
    get_new_db_connection,
)


BOT_EMAIL = "sensai-bot@sensai.internal"


async def get_or_create_bot_user() -> int:
    """Return the user ID of the SensAI Bot user, creating it if needed."""
    row = await execute_db_operation(
        f"SELECT id FROM {users_table_name} WHERE email = ?",
        (BOT_EMAIL,),
        fetch_one=True,
    )
    if row:
        return row[0]

    bot_id = await execute_db_operation(
        f"INSERT INTO {users_table_name} (email, first_name, last_name) VALUES (?, ?, ?)",
        (BOT_EMAIL, "SensAI", "Bot"),
        get_last_row_id=True,
    )
    return bot_id


# ─── Helpers ───


async def get_comment_author_and_org(comment_id: int) -> tuple[int, int, int] | None:
    """Return (author_id, org_id, post_id) for a comment, or None if not found."""
    row = await execute_db_operation(
        f"""SELECT c.author_id, p.org_id, c.post_id
            FROM {network_comments_table_name} c
            JOIN {network_posts_table_name} p ON c.post_id = p.id
            WHERE c.id = ? AND c.deleted_at IS NULL""",
        (comment_id,),
        fetch_one=True,
    )
    if not row:
        return None
    return (row[0], row[1], row[2])


# ─── Tag Operations ───


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    return slug


async def get_or_create_tag(org_id: int, name: str) -> Dict:
    slug = _slugify(name)
    existing = await execute_db_operation(
        f"SELECT id, name, slug, usage_count FROM {network_tags_table_name} WHERE org_id = ? AND slug = ? AND deleted_at IS NULL",
        (org_id, slug),
        fetch_one=True,
    )
    if existing:
        return {"id": existing[0], "name": existing[1], "slug": existing[2], "usage_count": existing[3]}

    tag_id = await execute_db_operation(
        f"INSERT INTO {network_tags_table_name} (org_id, name, slug) VALUES (?, ?, ?)",
        (org_id, name.strip(), slug),
        get_last_row_id=True,
    )
    return {"id": tag_id, "name": name.strip(), "slug": slug, "usage_count": 0}


async def search_tags(org_id: int, query: str, limit: int = 20) -> List[Dict]:
    results = await execute_db_operation(
        f"SELECT id, name, slug, usage_count FROM {network_tags_table_name} WHERE org_id = ? AND name LIKE ? AND deleted_at IS NULL ORDER BY usage_count DESC LIMIT ?",
        (org_id, f"%{query}%", limit),
        fetch_all=True,
    )
    return [{"id": r[0], "name": r[1], "slug": r[2], "usage_count": r[3]} for r in (results or [])]


async def get_trending_tags(org_id: int, days: int = 7, limit: int = 20) -> List[Dict]:
    results = await execute_db_operation(
        f"""SELECT t.id, t.name, t.slug, t.usage_count, COUNT(pt.post_id) as recent_posts
            FROM {network_tags_table_name} t
            JOIN {network_post_tags_table_name} pt ON t.id = pt.tag_id
            JOIN {network_posts_table_name} p ON pt.post_id = p.id
            WHERE t.org_id = ? AND t.deleted_at IS NULL AND p.deleted_at IS NULL
            AND p.created_at >= datetime('now', '-{days} days')
            GROUP BY t.id
            ORDER BY recent_posts DESC, t.usage_count DESC
            LIMIT ?""",
        (org_id, limit),
        fetch_all=True,
    )
    return [{"id": r[0], "name": r[1], "slug": r[2], "usage_count": r[3], "recent_posts": r[4]} for r in (results or [])]


async def get_recommended_tags(user_id: int, org_id: int, limit: int = 15) -> List[Dict]:
    # Get tags related to courses/tasks the user is enrolled in
    results = await execute_db_operation(
        f"""SELECT DISTINCT t.id, t.name, t.slug, t.usage_count
            FROM {network_tags_table_name} t
            JOIN {network_post_tags_table_name} pt ON t.id = pt.tag_id
            JOIN {network_posts_table_name} p ON pt.post_id = p.id
            WHERE t.org_id = ? AND t.deleted_at IS NULL AND p.deleted_at IS NULL
            AND t.usage_count > 0
            ORDER BY t.usage_count DESC
            LIMIT ?""",
        (org_id, limit),
        fetch_all=True,
    )
    return [{"id": r[0], "name": r[1], "slug": r[2], "usage_count": r[3]} for r in (results or [])]


async def get_all_tags(org_id: int) -> List[Dict]:
    results = await execute_db_operation(
        f"SELECT id, name, slug, usage_count FROM {network_tags_table_name} WHERE org_id = ? AND deleted_at IS NULL ORDER BY usage_count DESC",
        (org_id,),
        fetch_all=True,
    )
    return [{"id": r[0], "name": r[1], "slug": r[2], "usage_count": r[3]} for r in (results or [])]


# ─── Post Operations ───


async def create_post(
    org_id: int,
    author_id: int,
    post_type: str,
    title: str,
    blocks: list | None = None,
    content_text: str | None = None,
    code_content: str | None = None,
    coding_language: str | None = None,
    image_url: str | None = None,
    tag_names: list[str] | None = None,
    poll_options: list[str] | None = None,
    status: str = "published",
) -> Dict:
    blocks_json = json.dumps(blocks) if blocks else None

    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()

        await cursor.execute(
            f"""INSERT INTO {network_posts_table_name}
                (org_id, author_id, post_type, title, blocks, content_text, code_content, coding_language, image_url, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (org_id, author_id, post_type, title, blocks_json, content_text, code_content, coding_language, image_url, status),
        )
        post_id = cursor.lastrowid

        # Create and link tags (inline to avoid opening a second connection)
        if tag_names:
            for tag_name in tag_names:
                slug = _slugify(tag_name)
                await cursor.execute(
                    f"SELECT id FROM {network_tags_table_name} WHERE org_id = ? AND slug = ? AND deleted_at IS NULL",
                    (org_id, slug),
                )
                existing_tag = await cursor.fetchone()
                if existing_tag:
                    tag_id = existing_tag[0]
                else:
                    await cursor.execute(
                        f"INSERT INTO {network_tags_table_name} (org_id, name, slug) VALUES (?, ?, ?)",
                        (org_id, tag_name.strip(), slug),
                    )
                    tag_id = cursor.lastrowid

                await cursor.execute(
                    f"INSERT OR IGNORE INTO {network_post_tags_table_name} (post_id, tag_id) VALUES (?, ?)",
                    (post_id, tag_id),
                )
                await cursor.execute(
                    f"UPDATE {network_tags_table_name} SET usage_count = usage_count + 1 WHERE id = ?",
                    (tag_id,),
                )

        # Create poll options
        if post_type == "poll" and poll_options:
            for option_text in poll_options:
                await cursor.execute(
                    f"INSERT INTO {network_poll_options_table_name} (post_id, option_text) VALUES (?, ?)",
                    (post_id, option_text),
                )

        # Update user network profile
        await _ensure_user_profile(cursor, author_id, org_id)
        await cursor.execute(
            f"UPDATE {user_network_profiles_table_name} SET posts_count = posts_count + 1, last_active_at = CURRENT_TIMESTAMP WHERE user_id = ? AND org_id = ?",
            (author_id, org_id),
        )

        await conn.commit()

    return await get_post_by_id(post_id)


async def get_post_by_id(post_id: int, user_id: int | None = None) -> Dict | None:
    row = await execute_db_operation(
        f"""SELECT p.id, p.org_id, p.author_id, p.post_type, p.title, p.blocks, p.content_text,
                p.code_content, p.coding_language, p.image_url, p.status, p.is_pinned, p.view_count,
                p.reply_count, p.upvote_count, p.downvote_count, p.quality_score, p.created_at,
                u.first_name, u.last_name, u.email,
                COALESCE(np.badge_tier, 'Bronze 1') as badge_tier,
                COALESCE(np.network_role, 'newbie') as network_role,
                COALESCE(p.is_edited, 0) as is_edited
            FROM {network_posts_table_name} p
            JOIN {users_table_name} u ON p.author_id = u.id
            LEFT JOIN {user_network_profiles_table_name} np ON p.author_id = np.user_id AND p.org_id = np.org_id
            WHERE p.id = ? AND p.deleted_at IS NULL""",
        (post_id,),
        fetch_one=True,
    )
    if not row:
        return None

    post = _row_to_post_dict(row)

    # Get tags
    tags = await execute_db_operation(
        f"""SELECT t.id, t.name, t.slug, t.usage_count
            FROM {network_tags_table_name} t
            JOIN {network_post_tags_table_name} pt ON t.id = pt.tag_id
            WHERE pt.post_id = ? AND t.deleted_at IS NULL""",
        (post_id,),
        fetch_all=True,
    )
    post["tags"] = [{"id": t[0], "name": t[1], "slug": t[2], "usage_count": t[3]} for t in (tags or [])]

    # Get user vote if user_id provided
    if user_id:
        vote = await execute_db_operation(
            f"SELECT vote_type FROM {network_votes_table_name} WHERE user_id = ? AND target_type = 'post' AND target_id = ?",
            (user_id, post_id),
            fetch_one=True,
        )
        post["user_vote"] = vote[0] if vote else None

    # Get poll options if poll
    if post["post_type"] == "poll":
        options = await execute_db_operation(
            f"SELECT id, option_text, vote_count FROM {network_poll_options_table_name} WHERE post_id = ?",
            (post_id,),
            fetch_all=True,
        )
        poll_options = []
        for opt in (options or []):
            user_voted = False
            if user_id:
                v = await execute_db_operation(
                    f"SELECT 1 FROM {network_poll_votes_table_name} WHERE user_id = ? AND option_id = ?",
                    (user_id, opt[0]),
                    fetch_one=True,
                )
                user_voted = v is not None
            poll_options.append({"id": opt[0], "option_text": opt[1], "vote_count": opt[2], "user_voted": user_voted})
        post["poll_options"] = poll_options

    # Increment view count
    await execute_db_operation(
        f"UPDATE {network_posts_table_name} SET view_count = view_count + 1 WHERE id = ?",
        (post_id,),
    )

    return post


def _row_to_post_dict(row) -> Dict:
    return {
        "id": row[0],
        "org_id": row[1],
        "author": {
            "id": row[2],
            "first_name": row[18] or "",
            "last_name": row[19] or "",
            "email": row[20],
            "badge_tier": row[21],
            "network_role": row[22],
        },
        "post_type": row[3],
        "title": row[4],
        "blocks": json.loads(row[5]) if row[5] else None,
        "content_text": row[6],
        "code_content": row[7],
        "coding_language": row[8],
        "image_url": row[9],
        "status": row[10],
        "is_pinned": bool(row[11]),
        "view_count": row[12],
        "reply_count": row[13],
        "upvote_count": row[14],
        "downvote_count": row[15],
        "quality_score": row[16],
        "tags": [],
        "user_vote": None,
        "poll_options": [],
        "created_at": row[17],
        "is_edited": bool(row[23]),
    }


async def get_network_feed(
    org_id: int,
    user_id: int | None = None,
    filter_type: str = "recent",
    tag_slug: str | None = None,
    search: str | None = None,
    post_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> List[Dict]:
    base_query = f"""
        SELECT DISTINCT p.id, p.org_id, p.author_id, p.post_type, p.title, p.blocks, p.content_text,
            p.code_content, p.coding_language, p.image_url, p.status, p.is_pinned, p.view_count,
            p.reply_count, p.upvote_count, p.downvote_count, p.quality_score, p.created_at,
            u.first_name, u.last_name, u.email,
            COALESCE(np.badge_tier, 'Bronze 1') as badge_tier,
            COALESCE(np.network_role, 'newbie') as network_role,
            COALESCE(p.is_edited, 0) as is_edited
        FROM {network_posts_table_name} p
        JOIN {users_table_name} u ON p.author_id = u.id
        LEFT JOIN {user_network_profiles_table_name} np ON p.author_id = np.user_id AND p.org_id = np.org_id
    """

    conditions = [f"p.org_id = ?", "p.deleted_at IS NULL", "p.status = 'published'"]
    params: list = [org_id]

    if tag_slug:
        base_query += f" JOIN {network_post_tags_table_name} pt ON p.id = pt.post_id JOIN {network_tags_table_name} t ON pt.tag_id = t.id"
        conditions.append("t.slug = ?")
        params.append(tag_slug)

    if search:
        conditions.append("(p.title LIKE ? OR p.content_text LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    if post_type:
        conditions.append("p.post_type = ?")
        params.append(post_type)

    if filter_type == "unanswered":
        conditions.append("p.post_type = 'question' AND p.reply_count = 0")

    if filter_type == "my_posts" and user_id:
        conditions.append("p.author_id = ?")
        params.append(user_id)

    where_clause = " WHERE " + " AND ".join(conditions)

    if filter_type == "popular":
        order = "ORDER BY p.is_pinned DESC, p.upvote_count DESC, p.quality_score DESC"
    elif filter_type == "for_you" and user_id:
        order = "ORDER BY p.is_pinned DESC, p.quality_score DESC, p.created_at DESC"
    else:  # recent
        order = "ORDER BY p.is_pinned DESC, p.created_at DESC"

    query = f"{base_query}{where_clause} {order} LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = await execute_db_operation(query, tuple(params), fetch_all=True)

    posts = []
    for row in (rows or []):
        post = _row_to_post_dict(row)

        # Get tags for each post
        tags = await execute_db_operation(
            f"""SELECT t.id, t.name, t.slug, t.usage_count
                FROM {network_tags_table_name} t
                JOIN {network_post_tags_table_name} pt ON t.id = pt.tag_id
                WHERE pt.post_id = ? AND t.deleted_at IS NULL""",
            (post["id"],),
            fetch_all=True,
        )
        post["tags"] = [{"id": t[0], "name": t[1], "slug": t[2], "usage_count": t[3]} for t in (tags or [])]

        # Get user vote
        if user_id:
            vote = await execute_db_operation(
                f"SELECT vote_type FROM {network_votes_table_name} WHERE user_id = ? AND target_type = 'post' AND target_id = ?",
                (user_id, post["id"]),
                fetch_one=True,
            )
            post["user_vote"] = vote[0] if vote else None

        posts.append(post)

    return posts


async def delete_post(post_id: int) -> Dict | None:
    """Soft-delete a post and clean up related counters."""
    # Fetch post info before deleting
    post = await execute_db_operation(
        f"SELECT author_id, org_id FROM {network_posts_table_name} WHERE id = ? AND deleted_at IS NULL",
        (post_id,),
        fetch_one=True,
    )
    if not post:
        return None

    author_id, org_id = post[0], post[1]

    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()

        # Soft-delete the post
        await cursor.execute(
            f"UPDATE {network_posts_table_name} SET deleted_at = CURRENT_TIMESTAMP WHERE id = ? AND deleted_at IS NULL",
            (post_id,),
        )

        # Decrement tag usage_count for all tags on this post
        await cursor.execute(
            f"""UPDATE {network_tags_table_name} SET usage_count = MAX(0, usage_count - 1)
                WHERE id IN (SELECT tag_id FROM {network_post_tags_table_name} WHERE post_id = ?)""",
            (post_id,),
        )

        # Decrement author's posts_count
        await cursor.execute(
            f"UPDATE {user_network_profiles_table_name} SET posts_count = MAX(0, posts_count - 1) WHERE user_id = ? AND org_id = ?",
            (author_id, org_id),
        )

        # Soft-delete associated comments
        await cursor.execute(
            f"UPDATE {network_comments_table_name} SET deleted_at = CURRENT_TIMESTAMP WHERE post_id = ? AND deleted_at IS NULL",
            (post_id,),
        )

        await conn.commit()

    return {"author_id": author_id, "org_id": org_id}


async def toggle_pin_post(post_id: int):
    await execute_db_operation(
        f"UPDATE {network_posts_table_name} SET is_pinned = NOT is_pinned WHERE id = ? AND deleted_at IS NULL",
        (post_id,),
    )


async def update_post(
    post_id: int,
    title: str | None = None,
    content_text: str | None = None,
    code_content: str | None = None,
    coding_language: str | None = None,
    tag_names: list[str] | None = None,
) -> Dict | None:
    # Build SET clause dynamically for provided fields
    updates = []
    params = []
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    if content_text is not None:
        updates.append("content_text = ?")
        params.append(content_text)
    if code_content is not None:
        updates.append("code_content = ?")
        params.append(code_content)
    if coding_language is not None:
        updates.append("coding_language = ?")
        params.append(coding_language)

    # Always mark as edited when content changes
    updates.append("is_edited = 1")

    if not updates and tag_names is None:
        return await get_post_by_id(post_id)

    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()

        if updates:
            params.append(post_id)
            await cursor.execute(
                f"UPDATE {network_posts_table_name} SET {', '.join(updates)} WHERE id = ? AND deleted_at IS NULL",
                tuple(params),
            )

        # Update tags if provided
        if tag_names is not None:
            # Get org_id for this post
            await cursor.execute(f"SELECT org_id FROM {network_posts_table_name} WHERE id = ?", (post_id,))
            org_row = await cursor.fetchone()
            if org_row:
                org_id = org_row[0]

                # Remove old tag links
                await cursor.execute(
                    f"DELETE FROM {network_post_tags_table_name} WHERE post_id = ?",
                    (post_id,),
                )

                # Add new tags
                for tag_name in tag_names:
                    slug = _slugify(tag_name)
                    await cursor.execute(
                        f"SELECT id FROM {network_tags_table_name} WHERE org_id = ? AND slug = ? AND deleted_at IS NULL",
                        (org_id, slug),
                    )
                    existing_tag = await cursor.fetchone()
                    if existing_tag:
                        tag_id = existing_tag[0]
                    else:
                        await cursor.execute(
                            f"INSERT INTO {network_tags_table_name} (org_id, name, slug) VALUES (?, ?, ?)",
                            (org_id, tag_name.strip(), slug),
                        )
                        tag_id = cursor.lastrowid

                    await cursor.execute(
                        f"INSERT OR IGNORE INTO {network_post_tags_table_name} (post_id, tag_id) VALUES (?, ?)",
                        (post_id, tag_id),
                    )

        await conn.commit()

    return await get_post_by_id(post_id)


async def get_pending_posts(org_id: int) -> List[Dict]:
    """Get all posts with pending_approval status for mentor review."""
    rows = await execute_db_operation(
        f"""SELECT DISTINCT p.id, p.org_id, p.author_id, p.post_type, p.title, p.blocks, p.content_text,
            p.code_content, p.coding_language, p.image_url, p.status, p.is_pinned, p.view_count,
            p.reply_count, p.upvote_count, p.downvote_count, p.quality_score, p.created_at,
            u.first_name, u.last_name, u.email,
            COALESCE(np.badge_tier, 'Bronze 1') as badge_tier,
            COALESCE(np.network_role, 'newbie') as network_role,
            COALESCE(p.is_edited, 0) as is_edited
        FROM {network_posts_table_name} p
        JOIN {users_table_name} u ON p.author_id = u.id
        LEFT JOIN {user_network_profiles_table_name} np ON p.author_id = np.user_id AND p.org_id = np.org_id
        WHERE p.org_id = ? AND p.status = 'pending_approval' AND p.deleted_at IS NULL
        ORDER BY p.created_at DESC""",
        (org_id,),
        fetch_all=True,
    )

    posts = []
    for row in (rows or []):
        post = _row_to_post_dict(row)
        tags = await execute_db_operation(
            f"""SELECT t.id, t.name, t.slug, t.usage_count
                FROM {network_tags_table_name} t
                JOIN {network_post_tags_table_name} pt ON t.id = pt.tag_id
                WHERE pt.post_id = ? AND t.deleted_at IS NULL""",
            (post["id"],),
            fetch_all=True,
        )
        post["tags"] = [{"id": t[0], "name": t[1], "slug": t[2], "usage_count": t[3]} for t in (tags or [])]
        posts.append(post)

    return posts


async def update_post_status(post_id: int, status: str) -> Dict | None:
    """Update post status (e.g. pending_approval -> published or rejected)."""
    await execute_db_operation(
        f"UPDATE {network_posts_table_name} SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND deleted_at IS NULL",
        (status, post_id),
    )
    return await get_post_by_id(post_id)


# ─── Comment Operations ───


async def create_comment(
    post_id: int,
    author_id: int,
    content: str,
    code_content: str | None = None,
    coding_language: str | None = None,
    image_url: str | None = None,
    parent_comment_id: int | None = None,
) -> Dict:
    comment_id = await execute_db_operation(
        f"""INSERT INTO {network_comments_table_name}
            (post_id, author_id, content, code_content, coding_language, image_url, parent_comment_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (post_id, author_id, content, code_content, coding_language, image_url, parent_comment_id),
        get_last_row_id=True,
    )

    # Update reply count on post
    await execute_db_operation(
        f"UPDATE {network_posts_table_name} SET reply_count = reply_count + 1 WHERE id = ?",
        (post_id,),
    )

    # Get the post org_id for profile update
    post = await execute_db_operation(
        f"SELECT org_id FROM {network_posts_table_name} WHERE id = ?",
        (post_id,),
        fetch_one=True,
    )
    if post:
        async with get_new_db_connection() as conn:
            cursor = await conn.cursor()
            await _ensure_user_profile(cursor, author_id, post[0])
            await cursor.execute(
                f"UPDATE {user_network_profiles_table_name} SET comments_count = comments_count + 1, last_active_at = CURRENT_TIMESTAMP WHERE user_id = ? AND org_id = ?",
                (author_id, post[0]),
            )
            await conn.commit()

    return await get_comment_by_id(comment_id)


async def get_comment_by_id(comment_id: int) -> Dict | None:
    row = await execute_db_operation(
        f"""SELECT c.id, c.post_id, c.author_id, c.parent_comment_id, c.content, c.code_content,
                c.coding_language, c.image_url, c.upvote_count, c.created_at,
                u.first_name, u.last_name, u.email,
                COALESCE(np.badge_tier, 'Bronze 1'), COALESCE(np.network_role, 'newbie')
            FROM {network_comments_table_name} c
            JOIN {users_table_name} u ON c.author_id = u.id
            LEFT JOIN {user_network_profiles_table_name} np ON c.author_id = np.user_id
            WHERE c.id = ? AND c.deleted_at IS NULL""",
        (comment_id,),
        fetch_one=True,
    )
    if not row:
        return None

    return {
        "id": row[0],
        "post_id": row[1],
        "author": {
            "id": row[2],
            "first_name": row[10] or "",
            "last_name": row[11] or "",
            "email": row[12],
            "badge_tier": row[13],
            "network_role": row[14],
        },
        "parent_comment_id": row[3],
        "content": row[4],
        "code_content": row[5],
        "coding_language": row[6],
        "image_url": row[7],
        "upvote_count": row[8],
        "user_vote": None,
        "replies": [],
        "created_at": row[9],
    }


async def get_comments_for_post(post_id: int, user_id: int | None = None) -> List[Dict]:
    rows = await execute_db_operation(
        f"""SELECT c.id, c.post_id, c.author_id, c.parent_comment_id, c.content, c.code_content,
                c.coding_language, c.image_url, c.upvote_count, c.created_at,
                u.first_name, u.last_name, u.email,
                COALESCE(np.badge_tier, 'Bronze 1'), COALESCE(np.network_role, 'newbie')
            FROM {network_comments_table_name} c
            JOIN {users_table_name} u ON c.author_id = u.id
            LEFT JOIN {user_network_profiles_table_name} np ON c.author_id = np.user_id
            WHERE c.post_id = ? AND c.deleted_at IS NULL
            ORDER BY c.created_at ASC""",
        (post_id,),
        fetch_all=True,
    )

    comments_map = {}
    top_level = []

    for row in (rows or []):
        comment = {
            "id": row[0],
            "post_id": row[1],
            "author": {
                "id": row[2],
                "first_name": row[10] or "",
                "last_name": row[11] or "",
                "email": row[12],
                "badge_tier": row[13],
                "network_role": row[14],
            },
            "parent_comment_id": row[3],
            "content": row[4],
            "code_content": row[5],
            "coding_language": row[6],
            "image_url": row[7],
            "upvote_count": row[8],
            "user_vote": None,
            "replies": [],
            "created_at": row[9],
        }

        if user_id:
            vote = await execute_db_operation(
                f"SELECT vote_type FROM {network_votes_table_name} WHERE user_id = ? AND target_type = 'comment' AND target_id = ?",
                (user_id, comment["id"]),
                fetch_one=True,
            )
            comment["user_vote"] = vote[0] if vote else None

        comments_map[comment["id"]] = comment

        if comment["parent_comment_id"] is None:
            top_level.append(comment)
        else:
            parent = comments_map.get(comment["parent_comment_id"])
            if parent:
                parent["replies"].append(comment)

    return top_level


# ─── Vote Operations ───


async def vote_on_target(user_id: int, target_type: str, target_id: int, vote_type: str) -> Dict:
    # Check for existing vote
    existing = await execute_db_operation(
        f"SELECT id, vote_type FROM {network_votes_table_name} WHERE user_id = ? AND target_type = ? AND target_id = ?",
        (user_id, target_type, target_id),
        fetch_one=True,
    )

    table = network_posts_table_name if target_type == "post" else network_comments_table_name

    if existing:
        old_vote = existing[1]
        if old_vote == vote_type:
            # Remove vote (toggle off)
            await execute_db_operation(
                f"DELETE FROM {network_votes_table_name} WHERE id = ?",
                (existing[0],),
            )
            if old_vote == "upvote":
                await execute_db_operation(f"UPDATE {table} SET upvote_count = MAX(0, upvote_count - 1) WHERE id = ?", (target_id,))
            else:
                await execute_db_operation(f"UPDATE {table} SET downvote_count = MAX(0, downvote_count - 1) WHERE id = ?", (target_id,))
            await _update_vote_profile(target_type, target_id, old_vote, remove=True)
            return {"action": "removed", "vote_type": None}
        else:
            # Change vote
            await execute_db_operation(
                f"UPDATE {network_votes_table_name} SET vote_type = ? WHERE id = ?",
                (vote_type, existing[0]),
            )
            if old_vote == "upvote":
                await execute_db_operation(f"UPDATE {table} SET upvote_count = MAX(0, upvote_count - 1), downvote_count = downvote_count + 1 WHERE id = ?", (target_id,))
            else:
                await execute_db_operation(f"UPDATE {table} SET downvote_count = MAX(0, downvote_count - 1), upvote_count = upvote_count + 1 WHERE id = ?", (target_id,))
            await _update_vote_profile(target_type, target_id, old_vote, remove=True)
            await _update_vote_profile(target_type, target_id, vote_type, remove=False)
            return {"action": "changed", "vote_type": vote_type}
    else:
        # New vote
        await execute_db_operation(
            f"INSERT INTO {network_votes_table_name} (user_id, target_type, target_id, vote_type) VALUES (?, ?, ?, ?)",
            (user_id, target_type, target_id, vote_type),
        )
        if vote_type == "upvote":
            await execute_db_operation(f"UPDATE {table} SET upvote_count = upvote_count + 1 WHERE id = ?", (target_id,))
        else:
            await execute_db_operation(f"UPDATE {table} SET downvote_count = downvote_count + 1 WHERE id = ?", (target_id,))
        await _update_vote_profile(target_type, target_id, vote_type, remove=False)
        return {"action": "added", "vote_type": vote_type}


async def _update_vote_profile(target_type: str, target_id: int, vote_type: str, remove: bool):
    """Update the author's network profile when their content receives votes."""
    table = network_posts_table_name if target_type == "post" else network_comments_table_name
    row = await execute_db_operation(
        f"SELECT author_id, org_id FROM {network_posts_table_name} WHERE id = ?" if target_type == "post"
        else f"SELECT c.author_id, p.org_id FROM {network_comments_table_name} c JOIN {network_posts_table_name} p ON c.post_id = p.id WHERE c.id = ?",
        (target_id,),
        fetch_one=True,
    )
    if not row:
        return

    author_id, org_id = row[0], row[1]
    delta = -1 if remove else 1

    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        await _ensure_user_profile(cursor, author_id, org_id)
        if vote_type == "upvote":
            await cursor.execute(
                f"UPDATE {user_network_profiles_table_name} SET upvotes_received = MAX(0, upvotes_received + ?) WHERE user_id = ? AND org_id = ?",
                (delta, author_id, org_id),
            )
        else:
            await cursor.execute(
                f"UPDATE {user_network_profiles_table_name} SET downvotes_received = MAX(0, downvotes_received + ?) WHERE user_id = ? AND org_id = ?",
                (delta, author_id, org_id),
            )
        await conn.commit()


async def vote_on_poll(user_id: int, option_id: int) -> Dict:
    # Check if user already voted on this poll
    option = await execute_db_operation(
        f"SELECT post_id FROM {network_poll_options_table_name} WHERE id = ?",
        (option_id,),
        fetch_one=True,
    )
    if not option:
        return {"error": "Option not found"}

    post_id = option[0]

    # Check if user already voted on any option of this poll
    existing = await execute_db_operation(
        f"""SELECT pv.option_id FROM {network_poll_votes_table_name} pv
            JOIN {network_poll_options_table_name} po ON pv.option_id = po.id
            WHERE pv.user_id = ? AND po.post_id = ?""",
        (user_id, post_id),
        fetch_one=True,
    )

    if existing:
        # Remove old vote
        await execute_db_operation(
            f"DELETE FROM {network_poll_votes_table_name} WHERE user_id = ? AND option_id = ?",
            (user_id, existing[0]),
        )
        await execute_db_operation(
            f"UPDATE {network_poll_options_table_name} SET vote_count = MAX(0, vote_count - 1) WHERE id = ?",
            (existing[0],),
        )

    # Add new vote
    await execute_db_operation(
        f"INSERT INTO {network_poll_votes_table_name} (user_id, option_id) VALUES (?, ?)",
        (user_id, option_id),
    )
    await execute_db_operation(
        f"UPDATE {network_poll_options_table_name} SET vote_count = vote_count + 1 WHERE id = ?",
        (option_id,),
    )

    return {"success": True}


# ─── Comment Management ───


async def delete_comment(comment_id: int) -> Dict | None:
    """Soft-delete a comment and update related counters."""
    row = await execute_db_operation(
        f"""SELECT c.author_id, c.post_id, p.org_id
            FROM {network_comments_table_name} c
            JOIN {network_posts_table_name} p ON c.post_id = p.id
            WHERE c.id = ? AND c.deleted_at IS NULL""",
        (comment_id,),
        fetch_one=True,
    )
    if not row:
        return None

    author_id, post_id, org_id = row[0], row[1], row[2]

    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()

        # Soft-delete the comment
        await cursor.execute(
            f"UPDATE {network_comments_table_name} SET deleted_at = CURRENT_TIMESTAMP WHERE id = ? AND deleted_at IS NULL",
            (comment_id,),
        )

        # Soft-delete child replies
        await cursor.execute(
            f"UPDATE {network_comments_table_name} SET deleted_at = CURRENT_TIMESTAMP WHERE parent_comment_id = ? AND deleted_at IS NULL",
            (comment_id,),
        )

        # Decrement reply_count on the post
        await cursor.execute(
            f"UPDATE {network_posts_table_name} SET reply_count = MAX(0, reply_count - 1) WHERE id = ?",
            (post_id,),
        )

        # Decrement author's comments_count
        await cursor.execute(
            f"UPDATE {user_network_profiles_table_name} SET comments_count = MAX(0, comments_count - 1) WHERE user_id = ? AND org_id = ?",
            (author_id, org_id),
        )

        await conn.commit()

    return {"author_id": author_id, "org_id": org_id, "post_id": post_id}


async def update_comment(comment_id: int, content: str, code_content: str | None = None, coding_language: str | None = None) -> Dict | None:
    """Update a comment's content."""
    existing = await execute_db_operation(
        f"SELECT id FROM {network_comments_table_name} WHERE id = ? AND deleted_at IS NULL",
        (comment_id,),
        fetch_one=True,
    )
    if not existing:
        return None

    updates = ["content = ?"]
    params: list = [content]

    if code_content is not None:
        updates.append("code_content = ?")
        params.append(code_content)
    if coding_language is not None:
        updates.append("coding_language = ?")
        params.append(coding_language)

    params.append(comment_id)
    await execute_db_operation(
        f"UPDATE {network_comments_table_name} SET {', '.join(updates)} WHERE id = ? AND deleted_at IS NULL",
        tuple(params),
    )

    return await get_comment_by_id(comment_id)


# ─── Profile Operations ───


async def _ensure_user_profile(cursor, user_id: int, org_id: int):
    await cursor.execute(
        f"SELECT 1 FROM {user_network_profiles_table_name} WHERE user_id = ? AND org_id = ?",
        (user_id, org_id),
    )
    exists = await cursor.fetchone()
    if not exists:
        # Determine network role based on cohort roles
        role_row = await cursor.execute(
            f"""SELECT uc.role FROM {user_cohorts_table_name} uc
                JOIN {course_cohorts_table_name} cc ON uc.cohort_id = cc.cohort_id
                WHERE uc.user_id = ? AND uc.deleted_at IS NULL
                LIMIT 1""",
            (user_id,),
        )
        role_result = await role_row.fetchone()
        network_role = "mentor" if (role_result and role_result[0] == "mentor") else "newbie"

        # Check if org admin/owner
        admin_row = await cursor.execute(
            f"SELECT role FROM {user_organizations_table_name} WHERE user_id = ? AND org_id = ? AND deleted_at IS NULL",
            (user_id, org_id),
        )
        admin_result = await admin_row.fetchone()
        if admin_result and admin_result[0] in ("owner", "admin"):
            network_role = "mentor"

        await cursor.execute(
            f"INSERT OR IGNORE INTO {user_network_profiles_table_name} (user_id, org_id, network_role) VALUES (?, ?, ?)",
            (user_id, org_id, network_role),
        )


async def get_user_network_profile(user_id: int, org_id: int) -> Dict:
    row = await execute_db_operation(
        f"""SELECT unp.badge_tier, unp.badge_score, unp.learning_score, unp.contribution_score,
                unp.endorsement_score, unp.downvote_penalty, unp.posts_count, unp.comments_count,
                unp.upvotes_received, unp.downvotes_received, unp.network_role, unp.last_active_at,
                u.first_name, u.last_name, u.email
            FROM {user_network_profiles_table_name} unp
            JOIN {users_table_name} u ON unp.user_id = u.id
            WHERE unp.user_id = ? AND unp.org_id = ?""",
        (user_id, org_id),
        fetch_one=True,
    )
    if not row:
        # Create profile and return defaults
        async with get_new_db_connection() as conn:
            cursor = await conn.cursor()
            await _ensure_user_profile(cursor, user_id, org_id)
            await conn.commit()
        return await get_user_network_profile(user_id, org_id)

    return {
        "user_id": user_id,
        "org_id": org_id,
        "badge_tier": row[0],
        "badge_score": row[1],
        "learning_score": row[2],
        "contribution_score": row[3],
        "endorsement_score": row[4],
        "downvote_penalty": row[5],
        "posts_count": row[6],
        "comments_count": row[7],
        "upvotes_received": row[8],
        "downvotes_received": row[9],
        "network_role": row[10],
        "last_active_at": row[11],
        "first_name": row[12] or "",
        "last_name": row[13] or "",
        "email": row[14],
    }


async def get_network_leaderboard(org_id: int, limit: int = 50) -> List[Dict]:
    """Get users ranked by badge_score for an organization."""
    rows = await execute_db_operation(
        f"""SELECT unp.user_id, unp.badge_tier, unp.badge_score, unp.learning_score,
                unp.contribution_score, unp.posts_count, unp.comments_count,
                unp.upvotes_received, unp.network_role,
                u.first_name, u.last_name, u.email
            FROM {user_network_profiles_table_name} unp
            JOIN {users_table_name} u ON unp.user_id = u.id
            WHERE unp.org_id = ? AND unp.badge_score > 0
            ORDER BY unp.badge_score DESC
            LIMIT ?""",
        (org_id, limit),
        fetch_all=True,
    )
    return [
        {
            "rank": i + 1,
            "user_id": row[0],
            "badge_tier": row[1],
            "badge_score": row[2],
            "learning_score": row[3],
            "contribution_score": row[4],
            "posts_count": row[5],
            "comments_count": row[6],
            "upvotes_received": row[7],
            "network_role": row[8],
            "first_name": row[9] or "",
            "last_name": row[10] or "",
            "email": row[11],
        }
        for i, row in enumerate(rows or [])
    ]
