import json
from typing import List, Optional, Dict
from api.utils.db import execute_db_operation, get_new_db_connection
from api.config import (
    posts_table_name,
    hubs_table_name,
    skills_table_name,
    users_table_name,
    user_skills_table_name,
    hub_skills_table_name,
)


# ── FTS5 table creation ────────────────────────────────────────────────────────

async def create_fts_tables(cursor) -> None:
    """Create FTS5 virtual tables for full-text search."""
    await cursor.execute(
        """CREATE VIRTUAL TABLE IF NOT EXISTS posts_fts
           USING fts5(title, content, post_id UNINDEXED, tokenize='porter unicode61')"""
    )
    await cursor.execute(
        """CREATE VIRTUAL TABLE IF NOT EXISTS skills_fts
           USING fts5(name, description, skill_id UNINDEXED, tokenize='porter unicode61')"""
    )
    await cursor.execute(
        """CREATE VIRTUAL TABLE IF NOT EXISTS hubs_fts
           USING fts5(name, description, hub_id UNINDEXED, tokenize='porter unicode61')"""
    )


async def ensure_fts_tables() -> None:
    """Called during migration to set up FTS tables."""
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        await create_fts_tables(cursor)
        await conn.commit()


# ── FTS index population ───────────────────────────────────────────────────────

def _extract_text_from_blocks(blocks_json: Optional[str]) -> str:
    """Extract plain text from blocks JSON for FTS indexing."""
    if not blocks_json:
        return ""
    try:
        blocks = json.loads(blocks_json) if isinstance(blocks_json, str) else blocks_json
        texts = []
        if isinstance(blocks, list):
            for block in blocks:
                if isinstance(block, dict):
                    content = block.get("content", [])
                    if isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "text":
                                texts.append(item.get("text", ""))
                    elif isinstance(content, str):
                        texts.append(content)
        return " ".join(texts)
    except (json.JSONDecodeError, TypeError, AttributeError):
        return ""


async def index_post(post_id: int, title: str, blocks_json: Optional[str]) -> None:
    content = _extract_text_from_blocks(blocks_json)
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        # Check if FTS table exists before indexing
        await cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='posts_fts'"
        )
        if not await cursor.fetchone():
            return
        await cursor.execute(
            "DELETE FROM posts_fts WHERE post_id = ?", (post_id,)
        )
        await cursor.execute(
            "INSERT INTO posts_fts (title, content, post_id) VALUES (?, ?, ?)",
            (title, content, post_id),
        )
        await conn.commit()


async def index_skill(skill_id: int, name: str, description: Optional[str]) -> None:
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='skills_fts'"
        )
        if not await cursor.fetchone():
            return
        await cursor.execute(
            "DELETE FROM skills_fts WHERE skill_id = ?", (skill_id,)
        )
        await cursor.execute(
            "INSERT INTO skills_fts (name, description, skill_id) VALUES (?, ?, ?)",
            (name, description or "", skill_id),
        )
        await conn.commit()


async def index_hub(hub_id: int, name: str, description: Optional[str]) -> None:
    async with get_new_db_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='hubs_fts'"
        )
        if not await cursor.fetchone():
            return
        await cursor.execute(
            "DELETE FROM hubs_fts WHERE hub_id = ?", (hub_id,)
        )
        await cursor.execute(
            "INSERT INTO hubs_fts (name, description, hub_id) VALUES (?, ?, ?)",
            (name, description or "", hub_id),
        )
        await conn.commit()


# ── Search queries ─────────────────────────────────────────────────────────────

async def search_posts(query: str, org_id: int, limit: int = 20, offset: int = 0) -> List[Dict]:
    rows = await execute_db_operation(
        f"""SELECT p.id, p.title, p.post_type, p.upvote_count, p.reply_count,
                   h.name as hub_name, h.slug as hub_slug
            FROM posts_fts pf
            JOIN {posts_table_name} p ON p.id = pf.post_id
            JOIN {hubs_table_name} h ON h.id = p.hub_id
            WHERE posts_fts MATCH ? AND h.org_id = ?
              AND p.deleted_at IS NULL AND p.status = 'published'
            ORDER BY rank
            LIMIT ? OFFSET ?""",
        (query, org_id, limit, offset),
        fetch_all=True,
    )
    return [
        {
            "type": "post",
            "id": r[0],
            "title": r[1],
            "snippet": f"{r[2]} · {r[4]} replies",
            "hub_name": r[5],
            "score": float(r[3]),
        }
        for r in rows
    ]


async def search_hubs(query: str, org_id: int, limit: int = 20) -> List[Dict]:
    rows = await execute_db_operation(
        f"""SELECT h.id, h.name, h.description, h.slug
            FROM hubs_fts hf
            JOIN {hubs_table_name} h ON h.id = hf.hub_id
            WHERE hubs_fts MATCH ? AND h.org_id = ?
              AND h.deleted_at IS NULL
            ORDER BY rank
            LIMIT ?""",
        (query, org_id, limit),
        fetch_all=True,
    )
    return [
        {
            "type": "hub",
            "id": r[0],
            "title": r[1],
            "snippet": r[2] or "",
            "score": 0.0,
        }
        for r in rows
    ]


async def search_skills(query: str, org_id: int, limit: int = 20) -> List[Dict]:
    rows = await execute_db_operation(
        f"""SELECT s.id, s.name, s.description
            FROM skills_fts sf
            JOIN {skills_table_name} s ON s.id = sf.skill_id
            WHERE skills_fts MATCH ? AND s.org_id = ?
              AND s.deleted_at IS NULL
            ORDER BY rank
            LIMIT ?""",
        (query, org_id, limit),
        fetch_all=True,
    )
    return [
        {
            "type": "skill",
            "id": r[0],
            "title": r[1],
            "snippet": r[2] or "",
            "score": 0.0,
        }
        for r in rows
    ]


async def full_search(
    query: str,
    org_id: int,
    search_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[Dict]:
    results = []
    try:
        if search_type in (None, "post"):
            results.extend(await search_posts(query, org_id, limit, offset))
        if search_type in (None, "hub"):
            results.extend(await search_hubs(query, org_id, limit))
        if search_type in (None, "skill"):
            results.extend(await search_skills(query, org_id, limit))
    except Exception:
        # FTS tables may not exist yet — return empty gracefully
        pass
    return results[:limit]


async def get_trending_posts(org_id: int, limit: int = 10) -> List[Dict]:
    """Trending = highest (upvotes + replies) in the last 7 days."""
    rows = await execute_db_operation(
        f"""SELECT p.id, p.title, p.post_type, p.upvote_count, p.reply_count,
                   h.name as hub_name, h.slug as hub_slug,
                   u.first_name, u.last_name
            FROM {posts_table_name} p
            JOIN {hubs_table_name} h ON h.id = p.hub_id
            JOIN {users_table_name} u ON u.id = p.author_id
            WHERE h.org_id = ? AND p.deleted_at IS NULL AND p.status = 'published'
              AND p.created_at >= datetime('now', '-7 days')
            ORDER BY (p.upvote_count + p.reply_count * 2) DESC
            LIMIT ?""",
        (org_id, limit),
        fetch_all=True,
    )
    return [
        {
            "type": "post",
            "id": r[0],
            "title": r[1],
            "post_type": r[2],
            "upvote_count": r[3],
            "reply_count": r[4],
            "hub_name": r[5],
            "hub_slug": r[6],
            "author_name": f"{r[7] or ''} {r[8] or ''}".strip(),
        }
        for r in rows
    ]


async def get_recommended_posts(user_id: int, org_id: int, limit: int = 10) -> List[Dict]:
    """Posts in hubs linked to skills the user has proficiency in."""
    rows = await execute_db_operation(
        f"""SELECT DISTINCT p.id, p.title, p.post_type, p.upvote_count, p.reply_count,
                   h.name as hub_name, h.slug as hub_slug
            FROM {posts_table_name} p
            JOIN {hubs_table_name} h ON h.id = p.hub_id
            JOIN {hub_skills_table_name} hs ON hs.hub_id = h.id
            JOIN {user_skills_table_name} us ON us.skill_id = hs.skill_id
            WHERE us.user_id = ? AND h.org_id = ?
              AND p.deleted_at IS NULL AND p.status = 'published'
              AND us.deleted_at IS NULL AND hs.deleted_at IS NULL
            ORDER BY p.upvote_count DESC
            LIMIT ?""",
        (user_id, org_id, limit),
        fetch_all=True,
    )
    return [
        {
            "type": "post",
            "id": r[0],
            "title": r[1],
            "post_type": r[2],
            "upvote_count": r[3],
            "reply_count": r[4],
            "hub_name": r[5],
            "hub_slug": r[6],
        }
        for r in rows
    ]
