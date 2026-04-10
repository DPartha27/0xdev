from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from api.db.post import (
    create_post as create_post_in_db,
    get_post as get_post_from_db,
    update_post as update_post_in_db,
    delete_post as delete_post_in_db,
    increment_view_count,
    create_reply as create_reply_in_db,
    get_replies_for_post,
    update_reply as update_reply_in_db,
    delete_reply as delete_reply_in_db,
    accept_reply as accept_reply_in_db,
    vote as vote_in_db,
    get_user_vote,
    toggle_bookmark,
    is_bookmarked,
    get_bookmarks_for_user,
    create_poll_options,
    get_poll_options,
    vote_poll as vote_poll_in_db,
    link_skills_to_post,
    link_tasks_to_post,
    get_skills_for_post,
    get_tasks_for_post,
    endorse_reply as endorse_reply_in_db,
    get_posts_by_user,
    get_reply_author_id,
    search_tasks_for_org,
)
from api.db.hub import get_hub as get_hub_from_db
from api.db.reputation import log_reputation_event
from api.models import (
    CreatePostRequest,
    CreatePostResponse,
    UpdatePostRequest,
    CreateReplyRequest,
    UpdateReplyRequest,
    VoteRequest,
    BookmarkRequest,
    PollVoteRequest,
    EndorseReplyRequest,
    LinkPostSkillsRequest,
    LinkPostTasksRequest,
    FlagContentRequest,
)
from api.db.moderation import create_flag

router = APIRouter()


@router.post("/", response_model=CreatePostResponse)
async def create_post(request: CreatePostRequest) -> CreatePostResponse:
    post_id = await create_post_in_db(
        hub_id=request.hub_id,
        author_id=request.author_id,
        post_type=request.post_type.value,
        title=request.title,
        blocks=request.blocks,
        status=request.status.value,
    )
    if request.skill_ids:
        await link_skills_to_post(post_id, request.skill_ids)
    if request.task_ids:
        await link_tasks_to_post(post_id, request.task_ids)
    if request.post_type.value == "poll" and request.poll_options:
        await create_poll_options(post_id, request.poll_options)
    return {"id": post_id}


@router.get("/{post_id}")
async def get_post(post_id: int, user_id: Optional[int] = None):
    post = await get_post_from_db(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    await increment_view_count(post_id)

    post["replies"] = await get_replies_for_post(post_id)
    post["skills"] = await get_skills_for_post(post_id)
    post["linked_tasks"] = await get_tasks_for_post(post_id)

    if post.get("post_type") == "poll":
        post["poll_options"] = await get_poll_options(post_id)

    if user_id:
        post["is_bookmarked"] = await is_bookmarked(user_id, post_id)
        post["user_vote"] = await get_user_vote(user_id, "post", post_id)

    return post


@router.put("/{post_id}")
async def update_post(post_id: int, request: UpdatePostRequest):
    post = await get_post_from_db(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    await update_post_in_db(
        post_id=post_id,
        title=request.title,
        blocks=request.blocks,
        status=request.status.value if request.status else None,
    )
    return {"status": "updated"}


@router.delete("/{post_id}")
async def delete_post(post_id: int):
    post = await get_post_from_db(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    await delete_post_in_db(post_id)
    return {"status": "deleted"}


@router.post("/{post_id}/replies")
async def create_reply(post_id: int, request: CreateReplyRequest):
    post = await get_post_from_db(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    reply_id = await create_reply_in_db(
        post_id=post_id,
        author_id=request.author_id,
        blocks=request.blocks,
        parent_reply_id=request.parent_reply_id,
    )
    return {"id": reply_id}


@router.put("/{post_id}/replies/{reply_id}")
async def update_reply(post_id: int, reply_id: int, request: UpdateReplyRequest):
    await update_reply_in_db(reply_id, request.blocks)
    return {"status": "updated"}


@router.delete("/{post_id}/replies/{reply_id}")
async def delete_reply(post_id: int, reply_id: int):
    await delete_reply_in_db(reply_id, post_id)
    return {"status": "deleted"}


@router.post("/{post_id}/replies/{reply_id}/accept")
async def accept_reply(post_id: int, reply_id: int, author_id: int):
    post = await get_post_from_db(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post["author_id"] != author_id:
        raise HTTPException(status_code=403, detail="Only the post author can accept answers")
    if post["post_type"] != "question":
        raise HTTPException(status_code=400, detail="Only questions can have accepted answers")
    await accept_reply_in_db(post_id, reply_id)
    # Grant reputation to the reply author (quality signal: answer was accepted)
    reply_author = await get_reply_author_id(reply_id)
    if reply_author:
        hub = await get_hub_from_db(post["hub_id"])
        org_id = hub["org_id"] if hub else None
        await log_reputation_event(
            user_id=reply_author,
            org_id=org_id,
            event_type="answer_accepted",
            source_type="reply",
            source_id=reply_id,
            granted_by=author_id,
        )
    return {"status": "accepted"}


@router.post("/{post_id}/vote")
async def vote_post(post_id: int, request: VoteRequest):
    post = await get_post_from_db(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    result = await vote_in_db(
        user_id=request.user_id,
        target_type="post",
        target_id=post_id,
        value=request.value,
        view_duration_ms=request.view_duration_ms,
    )
    # Reputation event for post author (only on new upvotes, skip fast votes)
    if result["action"] == "created" and request.value == 1:
        fast_vote = request.view_duration_ms is not None and request.view_duration_ms < 2000
        if not fast_vote:
            hub = await get_hub_from_db(post["hub_id"])
            org_id = hub["org_id"] if hub else None
            await log_reputation_event(
                user_id=post["author_id"],
                org_id=org_id,
                event_type="post_upvoted",
                source_type="post",
                source_id=post_id,
                granted_by=request.user_id,
            )
    return result


@router.post("/{post_id}/replies/{reply_id}/vote")
async def vote_reply(post_id: int, reply_id: int, request: VoteRequest):
    post = await get_post_from_db(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    result = await vote_in_db(
        user_id=request.user_id,
        target_type="reply",
        target_id=reply_id,
        value=request.value,
        view_duration_ms=request.view_duration_ms,
    )
    # Reputation event for reply author (only on new upvotes, skip fast votes)
    if result["action"] == "created" and request.value == 1:
        fast_vote = request.view_duration_ms is not None and request.view_duration_ms < 2000
        if not fast_vote:
            reply_author = await get_reply_author_id(reply_id)
            if reply_author:
                hub = await get_hub_from_db(post["hub_id"])
                org_id = hub["org_id"] if hub else None
                await log_reputation_event(
                    user_id=reply_author,
                    org_id=org_id,
                    event_type="reply_upvoted",
                    source_type="reply",
                    source_id=reply_id,
                    granted_by=request.user_id,
                )
    return result


@router.post("/{post_id}/bookmark")
async def bookmark_post(post_id: int, request: BookmarkRequest):
    post = await get_post_from_db(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    action = await toggle_bookmark(request.user_id, post_id)
    return {"action": action}


@router.post("/{post_id}/skills")
async def tag_post_skills(post_id: int, request: LinkPostSkillsRequest):
    await link_skills_to_post(post_id, request.skill_ids)
    return {"status": "tagged"}


@router.post("/{post_id}/tasks")
async def link_post_tasks(post_id: int, request: LinkPostTasksRequest):
    await link_tasks_to_post(post_id, request.task_ids, request.relation_type.value)
    return {"status": "linked"}


@router.post("/{post_id}/poll/vote")
async def vote_on_poll(post_id: int, request: PollVoteRequest):
    post = await get_post_from_db(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post["post_type"] != "poll":
        raise HTTPException(status_code=400, detail="Post is not a poll")
    await vote_poll_in_db(request.user_id, post_id, request.option_id)
    return {"status": "voted"}


@router.get("/{post_id}/poll/results")
async def get_poll_results(post_id: int):
    return await get_poll_options(post_id)


@router.post("/{post_id}/replies/{reply_id}/endorse")
async def endorse_reply(post_id: int, reply_id: int, request: EndorseReplyRequest):
    await endorse_reply_in_db(
        endorser_id=request.endorser_id,
        reply_id=reply_id,
        skill_id=request.skill_id,
    )
    # Mentor endorsement is a high-quality signal — grant reputation to reply author
    reply_author = await get_reply_author_id(reply_id)
    if reply_author:
        post = await get_post_from_db(post_id)
        hub = await get_hub_from_db(post["hub_id"]) if post else None
        org_id = hub["org_id"] if hub else None
        await log_reputation_event(
            user_id=reply_author,
            org_id=org_id,
            event_type="mentor_endorsed",
            source_type="reply",
            source_id=reply_id,
            granted_by=request.endorser_id,
        )
    return {"status": "endorsed"}


@router.get("/tasks/search")
async def search_tasks(q: str = "", org_id: int = Query(...)):
    """Search course tasks by title for use in post task-linking UI."""
    if not q.strip():
        return []
    return await search_tasks_for_org(org_id, q.strip())


@router.get("/user/{user_id}")
async def get_user_posts(user_id: int):
    return await get_posts_by_user(user_id)


@router.post("/{post_id}/flag")
async def flag_post(post_id: int, request: FlagContentRequest):
    flag_id = await create_flag(
        reporter_id=request.reporter_id,
        target_type="post",
        target_id=post_id,
        reason=request.reason.value,
        description=request.description,
    )
    return {"id": flag_id}


@router.post("/{post_id}/replies/{reply_id}/flag")
async def flag_reply(post_id: int, reply_id: int, request: FlagContentRequest):
    flag_id = await create_flag(
        reporter_id=request.reporter_id,
        target_type="reply",
        target_id=reply_id,
        reason=request.reason.value,
        description=request.description,
    )
    return {"id": flag_id}
