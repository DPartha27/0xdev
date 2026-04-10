from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from api.db.hub import (
    create_hub as create_hub_in_db,
    get_hub as get_hub_from_db,
    get_hub_by_slug as get_hub_by_slug_from_db,
    get_hubs_for_org as get_hubs_for_org_from_db,
    update_hub as update_hub_in_db,
    delete_hub as delete_hub_in_db,
    add_hub_members as add_hub_members_in_db,
    remove_hub_members as remove_hub_members_in_db,
    update_hub_member_role as update_hub_member_role_in_db,
    link_skills_to_hub as link_skills_to_hub_in_db,
    unlink_skills_from_hub as unlink_skills_from_hub_in_db,
    link_courses_to_hub as link_courses_to_hub_in_db,
    unlink_courses_from_hub as unlink_courses_from_hub_in_db,
    get_hub_feed as get_hub_feed_from_db,
)
from api.models import (
    CreateHubRequest,
    CreateHubResponse,
    UpdateHubRequest,
    AddHubMembersRequest,
    RemoveHubMembersRequest,
    UpdateHubMemberRoleRequest,
    LinkHubSkillsRequest,
    LinkHubCoursesRequest,
)

router = APIRouter()


@router.get("/")
async def list_hubs(org_id: int):
    return await get_hubs_for_org_from_db(org_id)


@router.post("/", response_model=CreateHubResponse)
async def create_hub(request: CreateHubRequest) -> CreateHubResponse:
    hub_id = await create_hub_in_db(
        org_id=request.org_id,
        name=request.name,
        slug=request.slug,
        created_by=request.created_by,
        description=request.description,
        icon=request.icon,
        visibility=request.visibility.value,
    )
    if request.skill_ids:
        await link_skills_to_hub_in_db(hub_id, request.skill_ids)
    if request.course_ids:
        await link_courses_to_hub_in_db(hub_id, request.course_ids)
    return {"id": hub_id}


@router.get("/{hub_id}")
async def get_hub(hub_id: int):
    hub = await get_hub_from_db(hub_id)
    if not hub:
        raise HTTPException(status_code=404, detail="Hub not found")
    return hub


@router.put("/{hub_id}")
async def update_hub(hub_id: int, request: UpdateHubRequest):
    hub = await get_hub_from_db(hub_id)
    if not hub:
        raise HTTPException(status_code=404, detail="Hub not found")
    await update_hub_in_db(
        hub_id=hub_id,
        name=request.name,
        description=request.description,
        icon=request.icon,
        visibility=request.visibility.value if request.visibility else None,
    )
    return {"status": "updated"}


@router.delete("/{hub_id}")
async def delete_hub(hub_id: int):
    hub = await get_hub_from_db(hub_id)
    if not hub:
        raise HTTPException(status_code=404, detail="Hub not found")
    await delete_hub_in_db(hub_id)
    return {"status": "deleted"}


@router.post("/{hub_id}/members")
async def add_members(hub_id: int, request: AddHubMembersRequest):
    hub = await get_hub_from_db(hub_id)
    if not hub:
        raise HTTPException(status_code=404, detail="Hub not found")
    await add_hub_members_in_db(hub_id, request.user_ids, request.role.value)
    return {"status": "members added"}


@router.delete("/{hub_id}/members")
async def remove_members(hub_id: int, request: RemoveHubMembersRequest):
    hub = await get_hub_from_db(hub_id)
    if not hub:
        raise HTTPException(status_code=404, detail="Hub not found")
    await remove_hub_members_in_db(hub_id, request.user_ids)
    return {"status": "members removed"}


@router.put("/{hub_id}/members/{user_id}/role")
async def update_member_role(hub_id: int, user_id: int, request: UpdateHubMemberRoleRequest):
    hub = await get_hub_from_db(hub_id)
    if not hub:
        raise HTTPException(status_code=404, detail="Hub not found")
    await update_hub_member_role_in_db(hub_id, user_id, request.role.value)
    return {"status": "role updated"}


@router.post("/{hub_id}/skills")
async def link_skills(hub_id: int, request: LinkHubSkillsRequest):
    hub = await get_hub_from_db(hub_id)
    if not hub:
        raise HTTPException(status_code=404, detail="Hub not found")
    await link_skills_to_hub_in_db(hub_id, request.skill_ids)
    return {"status": "skills linked"}


@router.delete("/{hub_id}/skills")
async def unlink_skills(hub_id: int, request: LinkHubSkillsRequest):
    hub = await get_hub_from_db(hub_id)
    if not hub:
        raise HTTPException(status_code=404, detail="Hub not found")
    await unlink_skills_from_hub_in_db(hub_id, request.skill_ids)
    return {"status": "skills unlinked"}


@router.post("/{hub_id}/courses")
async def link_courses(hub_id: int, request: LinkHubCoursesRequest):
    hub = await get_hub_from_db(hub_id)
    if not hub:
        raise HTTPException(status_code=404, detail="Hub not found")
    await link_courses_to_hub_in_db(hub_id, request.course_ids)
    return {"status": "courses linked"}


@router.delete("/{hub_id}/courses")
async def unlink_courses(hub_id: int, request: LinkHubCoursesRequest):
    hub = await get_hub_from_db(hub_id)
    if not hub:
        raise HTTPException(status_code=404, detail="Hub not found")
    await unlink_courses_from_hub_in_db(hub_id, request.course_ids)
    return {"status": "courses unlinked"}


@router.get("/{hub_id}/feed")
async def get_hub_feed(
    hub_id: int,
    sort: str = Query("newest", regex="^(newest|popular|unanswered)$"),
    post_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    hub = await get_hub_from_db(hub_id)
    if not hub:
        raise HTTPException(status_code=404, detail="Hub not found")
    return await get_hub_feed_from_db(hub_id, sort=sort, post_type=post_type, limit=limit, offset=offset)
