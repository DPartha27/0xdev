from fastapi import APIRouter, Query
from api.db.reputation import (
    get_user_reputation as get_user_reputation_from_db,
    get_reputation_leaderboard as get_reputation_leaderboard_from_db,
    get_reputation_history as get_reputation_history_from_db,
)

router = APIRouter()


@router.get("/user/{user_id}")
async def get_user_reputation(user_id: int, org_id: int):
    return await get_user_reputation_from_db(user_id, org_id)


@router.get("/leaderboard")
async def get_reputation_leaderboard(
    org_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return await get_reputation_leaderboard_from_db(org_id, limit=limit, offset=offset)


@router.get("/user/{user_id}/history")
async def get_reputation_history(
    user_id: int,
    org_id: int,
    limit: int = Query(50, ge=1, le=200),
):
    return await get_reputation_history_from_db(user_id, org_id, limit=limit)
