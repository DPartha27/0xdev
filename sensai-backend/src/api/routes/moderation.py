from fastapi import APIRouter, HTTPException, Query
from api.db.moderation import (
    get_pending_flags as get_pending_flags_from_db,
    review_flag as review_flag_in_db,
    dismiss_flag as dismiss_flag_in_db,
    get_moderation_stats as get_moderation_stats_from_db,
    get_flag as get_flag_from_db,
)
from api.models import ReviewFlagRequest

router = APIRouter()


@router.get("/queue")
async def get_moderation_queue(
    org_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return await get_pending_flags_from_db(org_id, limit=limit, offset=offset)


@router.put("/flags/{flag_id}/review")
async def review_flag(flag_id: int, request: ReviewFlagRequest):
    flag = await get_flag_from_db(flag_id)
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
    if request.action_taken == "dismissed":
        await dismiss_flag_in_db(flag_id, request.reviewed_by)
    else:
        await review_flag_in_db(flag_id, request.reviewed_by, request.action_taken)
    return {"status": "reviewed"}


@router.get("/stats")
async def get_moderation_stats(org_id: int):
    return await get_moderation_stats_from_db(org_id)
