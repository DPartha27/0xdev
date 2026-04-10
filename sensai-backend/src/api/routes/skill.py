from fastapi import APIRouter, HTTPException
from typing import List
from api.db.skill import (
    create_skill as create_skill_in_db,
    get_skill as get_skill_from_db,
    get_skills_for_org as get_skills_for_org_from_db,
    update_skill as update_skill_in_db,
    delete_skill as delete_skill_in_db,
    link_skills_to_task as link_skills_to_task_in_db,
    unlink_skills_from_task as unlink_skills_from_task_in_db,
    get_user_skill_profile as get_user_skill_profile_from_db,
    get_skill_graph as get_skill_graph_from_db,
)
from api.models import (
    CreateSkillRequest,
    CreateSkillResponse,
    UpdateSkillRequest,
    SkillResponse,
    LinkSkillsToTaskRequest,
    UnlinkSkillsFromTaskRequest,
)

router = APIRouter()


@router.get("/", response_model=List[SkillResponse])
async def list_skills(org_id: int) -> List[SkillResponse]:
    return await get_skills_for_org_from_db(org_id)


@router.post("/", response_model=CreateSkillResponse)
async def create_skill(request: CreateSkillRequest) -> CreateSkillResponse:
    skill_id = await create_skill_in_db(
        org_id=request.org_id,
        name=request.name,
        slug=request.slug,
        description=request.description,
        parent_skill_id=request.parent_skill_id,
    )
    return {"id": skill_id}


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(skill_id: int) -> SkillResponse:
    skill = await get_skill_from_db(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.put("/{skill_id}")
async def update_skill(skill_id: int, request: UpdateSkillRequest):
    skill = await get_skill_from_db(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    await update_skill_in_db(
        skill_id=skill_id,
        name=request.name,
        description=request.description,
        parent_skill_id=request.parent_skill_id,
    )
    return {"status": "updated"}


@router.delete("/{skill_id}")
async def delete_skill(skill_id: int):
    skill = await get_skill_from_db(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    await delete_skill_in_db(skill_id)
    return {"status": "deleted"}


@router.get("/{skill_id}/graph")
async def get_skill_graph(skill_id: int):
    skill = await get_skill_from_db(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return await get_skill_graph_from_db(skill_id)


@router.get("/user/{user_id}")
async def get_user_skill_profile(user_id: int):
    return await get_user_skill_profile_from_db(user_id)


@router.post("/tasks/link")
async def link_skills_to_task(request: LinkSkillsToTaskRequest):
    await link_skills_to_task_in_db(
        task_id=request.task_id,
        skill_ids=request.skill_ids,
    )
    return {"status": "linked"}


@router.post("/tasks/unlink")
async def unlink_skills_from_task(request: UnlinkSkillsFromTaskRequest):
    await unlink_skills_from_task_in_db(
        task_id=request.task_id,
        skill_ids=request.skill_ids,
    )
    return {"status": "unlinked"}
