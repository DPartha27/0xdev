from fastapi import APIRouter, HTTPException
from typing import List, Dict
from api.db.network import (
    get_trending_tags as get_trending_tags_from_db,
    get_recommended_tags as get_recommended_tags_from_db,
    search_tags as search_tags_from_db,
    get_all_tags as get_all_tags_from_db,
    create_post as create_post_in_db,
    get_post_by_id as get_post_by_id_from_db,
    get_network_feed as get_network_feed_from_db,
    delete_post as delete_post_from_db,
    toggle_pin_post as toggle_pin_post_from_db,
    update_post as update_post_in_db,
    create_comment as create_comment_in_db,
    get_comments_for_post as get_comments_for_post_from_db,
    vote_on_target as vote_on_target_in_db,
    vote_on_poll as vote_on_poll_in_db,
    get_user_network_profile as get_user_network_profile_from_db,
    get_pending_posts as get_pending_posts_from_db,
    update_post_status as update_post_status_in_db,
    get_comment_author_and_org as get_comment_author_and_org_from_db,
    delete_comment as delete_comment_from_db,
    update_comment as update_comment_in_db,
    get_network_leaderboard as get_network_leaderboard_from_db,
    get_or_create_bot_user,
)
from api.reputation import recompute_user_badge, recompute_post_quality_score
from api.network_ai import ai_quality_check, ai_auto_tag, ai_summarize, ai_suggest_answer, ai_apply_suggestions
from api.models import (
    CreateNetworkPostRequest,
    UpdateNetworkPostRequest,
    CreateCommentRequest,
    UpdateCommentRequest,
    VoteRequest,
    PollVoteRequest,
    AICheckRequest,
    ApplySuggestionsRequest,
    ApproveRejectRequest,
)

router = APIRouter()


# ─── Tags ───


@router.get("/tags/trending")
async def get_trending_tags(org_id: int, days: int = 7, limit: int = 20) -> List[Dict]:
    return await get_trending_tags_from_db(org_id, days, limit)


@router.get("/tags/recommended")
async def get_recommended_tags(user_id: int, org_id: int, limit: int = 15) -> List[Dict]:
    return await get_recommended_tags_from_db(user_id, org_id, limit)


@router.get("/tags/search")
async def search_tags(org_id: int, q: str = "", limit: int = 20) -> List[Dict]:
    if not q:
        return await get_all_tags_from_db(org_id)
    return await search_tags_from_db(org_id, q, limit)


@router.get("/tags")
async def get_all_tags(org_id: int) -> List[Dict]:
    return await get_all_tags_from_db(org_id)


# ─── Posts / Feed ───


@router.post("/posts")
async def create_post(request: CreateNetworkPostRequest) -> Dict:
    # Determine status based on quality tier
    status = "published"
    if request.quality_tier == "medium":
        status = "pending_approval"
    elif request.quality_tier in ("low", "spam"):
        raise HTTPException(status_code=400, detail="Post quality is too low to publish. Please improve your content.")

    post = await create_post_in_db(
        org_id=request.org_id,
        author_id=request.author_id,
        post_type=request.post_type,
        title=request.title,
        blocks=request.blocks,
        content_text=request.content_text,
        code_content=request.code_content,
        coding_language=request.coding_language,
        image_url=request.image_url if request.post_type != "thread" else None,
        tag_names=request.tags,
        poll_options=request.poll_options,
        status=status,
    )
    # Recompute badge after creating post
    await recompute_user_badge(request.author_id, request.org_id)
    return post


@router.get("/posts")
async def get_feed(
    org_id: int,
    user_id: int | None = None,
    filter: str = "recent",
    tag: str | None = None,
    q: str | None = None,
    post_type: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> List[Dict]:
    return await get_network_feed_from_db(
        org_id=org_id,
        user_id=user_id,
        filter_type=filter,
        tag_slug=tag,
        search=q,
        post_type=post_type,
        limit=limit,
        offset=offset,
    )


@router.get("/posts/pending")
async def get_pending_posts(org_id: int, mentor_id: int) -> List[Dict]:
    """Get posts awaiting mentor approval. Only mentors can access."""
    profile = await get_user_network_profile_from_db(mentor_id, org_id)
    if profile.get("network_role") not in ("mentor", "master"):
        raise HTTPException(status_code=403, detail="Only mentors can view pending posts")
    return await get_pending_posts_from_db(org_id)


@router.get("/posts/{post_id}")
async def get_post(post_id: int, user_id: int | None = None) -> Dict:
    post = await get_post_by_id_from_db(post_id, user_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.put("/posts/{post_id}")
async def update_post(post_id: int, request: UpdateNetworkPostRequest) -> Dict:
    post = await update_post_in_db(
        post_id=post_id,
        title=request.title,
        content_text=request.content_text,
        code_content=request.code_content,
        coding_language=request.coding_language,
        tag_names=request.tags,
    )
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.delete("/posts/{post_id}")
async def delete_post(post_id: int):
    result = await delete_post_from_db(post_id)
    if not result:
        raise HTTPException(status_code=404, detail="Post not found")
    # Recompute badge since posts_count changed
    await recompute_user_badge(result["author_id"], result["org_id"])
    return {"success": True}


@router.post("/posts/{post_id}/pin")
async def pin_post(post_id: int):
    await toggle_pin_post_from_db(post_id)
    return {"success": True}


# ─── Comments ───


@router.post("/posts/{post_id}/comments")
async def add_comment(post_id: int, request: CreateCommentRequest) -> Dict:
    # Check relevance before allowing the comment
    post = await get_post_by_id_from_db(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    from api.utils.comment_relevance import check_comment_relevance
    relevance = check_comment_relevance(
        post_title=post["title"],
        post_content=post.get("content_text"),
        post_code=post.get("code_content"),
        comment_text=request.content,
        comment_code=request.code_content,
    )
    if not relevance["relevant"]:
        raise HTTPException(status_code=422, detail=relevance["reason"])

    comment = await create_comment_in_db(
        post_id=post_id,
        author_id=request.author_id,
        content=request.content,
        code_content=request.code_content,
        coding_language=request.coding_language,
        image_url=request.image_url,
        parent_comment_id=request.parent_comment_id,
    )
    # Recompute badge after commenting (comments contribute to contribution_score)
    await recompute_user_badge(request.author_id, post["org_id"])
    # Recompute post quality_score since reply_count changed
    await recompute_post_quality_score(post_id)
    return comment


@router.get("/posts/{post_id}/comments")
async def get_comments(post_id: int, user_id: int | None = None) -> List[Dict]:
    return await get_comments_for_post_from_db(post_id, user_id)


@router.delete("/comments/{comment_id}")
async def delete_comment(comment_id: int):
    result = await delete_comment_from_db(comment_id)
    if not result:
        raise HTTPException(status_code=404, detail="Comment not found")
    # Recompute badge since comments_count changed
    await recompute_user_badge(result["author_id"], result["org_id"])
    # Recompute post quality_score since reply_count changed
    await recompute_post_quality_score(result["post_id"])
    return {"success": True}


@router.put("/comments/{comment_id}")
async def edit_comment(comment_id: int, request: UpdateCommentRequest) -> Dict:
    comment = await update_comment_in_db(
        comment_id=comment_id,
        content=request.content,
        code_content=request.code_content,
        coding_language=request.coding_language,
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


# ─── Votes ───


@router.post("/posts/{post_id}/vote")
async def vote_post(post_id: int, request: VoteRequest) -> Dict:
    result = await vote_on_target_in_db(request.user_id, "post", post_id, request.vote_type)
    # Recompute badge for the post author and quality_score for the post
    post = await get_post_by_id_from_db(post_id)
    if post:
        await recompute_user_badge(post["author"]["id"], post["org_id"])
        await recompute_post_quality_score(post_id)
    return result


@router.post("/comments/{comment_id}/vote")
async def vote_comment(comment_id: int, request: VoteRequest) -> Dict:
    result = await vote_on_target_in_db(request.user_id, "comment", comment_id, request.vote_type)
    # Recompute badge for the comment author and parent post quality_score
    author_org = await get_comment_author_and_org_from_db(comment_id)
    if author_org:
        await recompute_user_badge(author_org[0], author_org[1])
        await recompute_post_quality_score(author_org[2])
    return result


@router.post("/polls/{post_id}/vote")
async def vote_poll(post_id: int, request: PollVoteRequest) -> Dict:
    return await vote_on_poll_in_db(request.user_id, request.option_id)


# ─── Profile ───


@router.get("/profile/{user_id}")
async def get_profile(user_id: int, org_id: int) -> Dict:
    return await get_user_network_profile_from_db(user_id, org_id)


@router.get("/profile/{user_id}/posts")
async def get_user_posts(user_id: int, org_id: int, limit: int = 10) -> List[Dict]:
    """Get recent posts by a specific user."""
    return await get_network_feed_from_db(
        org_id=org_id,
        user_id=user_id,
        filter_type="my_posts",
        limit=limit,
    )


@router.get("/leaderboard")
async def get_leaderboard(org_id: int, limit: int = 50) -> List[Dict]:
    return await get_network_leaderboard_from_db(org_id, limit)


# ─── Mentor Moderation ───


@router.post("/posts/{post_id}/approve")
async def approve_post(post_id: int, request: ApproveRejectRequest) -> Dict:
    """Mentor approves a pending post — sets status to published."""
    post = await get_post_by_id_from_db(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    profile = await get_user_network_profile_from_db(request.mentor_id, post["org_id"])
    if profile.get("network_role") not in ("mentor", "master"):
        raise HTTPException(status_code=403, detail="Only mentors can approve posts")

    updated = await update_post_status_in_db(post_id, "published")
    if not updated:
        raise HTTPException(status_code=404, detail="Post not found")
    # Recompute badge for post author now that their post is visible
    await recompute_user_badge(post["author"]["id"], post["org_id"])
    return updated


@router.post("/posts/{post_id}/reject")
async def reject_post(post_id: int, request: ApproveRejectRequest) -> Dict:
    """Mentor rejects a pending post."""
    post = await get_post_by_id_from_db(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    profile = await get_user_network_profile_from_db(request.mentor_id, post["org_id"])
    if profile.get("network_role") not in ("mentor", "master"):
        raise HTTPException(status_code=403, detail="Only mentors can reject posts")

    updated = await update_post_status_in_db(post_id, "rejected")
    if not updated:
        raise HTTPException(status_code=404, detail="Post not found")
    # Recompute badge since this post no longer counts
    await recompute_user_badge(post["author"]["id"], post["org_id"])
    return updated


# ─── AI Features ───


@router.post("/ai/quality-check")
async def quality_check(request: AICheckRequest) -> Dict:
    return await ai_quality_check(
        post_type=request.post_type,
        title=request.title,
        content=request.content_text,
        code_content=request.code_content,
        coding_language=request.coding_language,
        tags=request.tags,
    )


@router.post("/ai/auto-tag")
async def auto_tag(request: AICheckRequest) -> Dict:
    existing_tags = []
    if request.org_id:
        tags = await get_all_tags_from_db(request.org_id)
        existing_tags = [t["name"] for t in tags]
    return await ai_auto_tag(
        post_type=request.post_type,
        title=request.title,
        content=request.content_text,
        code_content=request.code_content,
        existing_tags=existing_tags,
    )


@router.post("/ai/summarize")
async def summarize(request: AICheckRequest) -> Dict:
    return await ai_summarize(
        title=request.title,
        content=request.content_text,
        code_content=request.code_content,
    )


@router.post("/ai/suggest-answer")
async def suggest_answer(request: AICheckRequest) -> Dict:
    return await ai_suggest_answer(
        title=request.title,
        content=request.content_text,
        code_content=request.code_content,
    )


@router.post("/ai/apply-suggestions")
async def apply_suggestions(request: ApplySuggestionsRequest) -> Dict:
    """Apply AI quality suggestions to improve a post's title, content, and tags."""
    return await ai_apply_suggestions(
        post_type=request.post_type,
        title=request.title,
        content=request.content_text,
        code_content=request.code_content,
        tags=request.tags,
        suggestions=request.suggestions,
    )


@router.post("/posts/{post_id}/ai-answer")
async def post_ai_answer_as_comment(post_id: int) -> Dict:
    """Call AI to generate an answer and post it as a comment from the SensAI Bot."""
    post = await get_post_by_id_from_db(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Generate AI answer
    ai_result = await ai_suggest_answer(
        title=post["title"],
        content=post.get("content_text"),
        code_content=post.get("code_content"),
    )

    # Get or create bot user
    bot_user_id = await get_or_create_bot_user()

    # Post as a comment from the bot
    comment = await create_comment_in_db(
        post_id=post_id,
        author_id=bot_user_id,
        content=ai_result["answer"],
        code_content=ai_result.get("code_example"),
        coding_language=ai_result.get("coding_language"),
    )

    return comment
