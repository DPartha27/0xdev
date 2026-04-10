from fastapi import APIRouter, Query
from typing import Optional
from api.db.search import (
    full_search as full_search_from_db,
    get_trending_posts as get_trending_posts_from_db,
    get_recommended_posts as get_recommended_posts_from_db,
)

router = APIRouter()


@router.get("/")
async def search(
    q: str,
    org_id: int,
    type: Optional[str] = Query(None, regex="^(post|hub|skill)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return await full_search_from_db(q, org_id, search_type=type, limit=limit, offset=offset)


@router.get("/trending")
async def trending_posts(
    org_id: int,
    limit: int = Query(10, ge=1, le=50),
):
    return await get_trending_posts_from_db(org_id, limit=limit)


@router.get("/recommended")
async def recommended_posts(
    user_id: int,
    org_id: int,
    limit: int = Query(10, ge=1, le=50),
):
    return await get_recommended_posts_from_db(user_id, org_id, limit=limit)
