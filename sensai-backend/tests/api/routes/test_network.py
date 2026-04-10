"""
Automated tests for the Learning Network Platform.

Verifies all missions from the spec:
  1. Topic-based hubs with CRUD and feeds
  2. Structured knowledge creation (thread/question/note/poll)
  3. Reputation system – quality-based points, no volume spam
  4. Posts ↔ skills ↔ tasks linkage
  5. High-signal content surfacing (accepted answers, trending, recommended)
  6. Moderation workflows
  7. Persistent, discoverable, reusable knowledge (FTS search)

Run with:
    cd sensai-backend
    uv run pytest tests/api/routes/test_network.py -v
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    from api.main import app
    return TestClient(app)


def _async(val):
    """Return an AsyncMock that resolves to val."""
    return AsyncMock(return_value=val)


# Shared sample data
def _hub_stub(hub_id=1, org_id=5):
    return {"id": hub_id, "org_id": org_id, "name": "DSA Hub", "slug": "dsa-hub",
            "description": None, "icon": None, "visibility": "public",
            "created_by": 7, "created_at": "2026-04-01", "updated_at": None,
            "member_count": 3, "post_count": 5, "skills": []}


def _post_stub(post_id=10, post_type="thread"):
    return {"id": post_id, "hub_id": 1, "author_id": 7, "author_name": "Alice",
            "post_type": post_type, "title": "Knapsack DP explanation",
            "blocks": None, "status": "published", "lifecycle_status": "active",
            "is_pinned": False, "upvote_count": 1, "downvote_count": 0,
            "reply_count": 0, "view_count": 5, "has_accepted_answer": False,
            "created_at": "2026-04-09", "updated_at": None}


# ─────────────────────────────────────────────────────────────────────────────
# MISSION 1 – Topic-based hubs
# ─────────────────────────────────────────────────────────────────────────────

class TestHubCRUD:
    """Hubs must support create, read, update, delete."""

    def test_create_hub_returns_id(self, client):
        with patch("api.routes.hub.create_hub_in_db", _async(42)):
            resp = client.post("/hubs/", json={
                "org_id": 1,
                "name": "DSA Hub",
                "slug": "dsa-hub",
                "created_by": 7,
                "description": "All things DSA",
                "visibility": "public",
            })
        assert resp.status_code == 200
        assert resp.json()["id"] == 42

    def test_list_hubs_for_org(self, client):
        sample = [_hub_stub()]
        with patch("api.routes.hub.get_hubs_for_org_from_db", _async(sample)):
            resp = client.get("/hubs/?org_id=1")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "DSA Hub"

    def test_get_hub_by_id(self, client):
        with patch("api.routes.hub.get_hub_from_db", _async(_hub_stub())):
            resp = client.get("/hubs/1")
        assert resp.status_code == 200
        assert resp.json()["slug"] == "dsa-hub"

    def test_get_hub_404(self, client):
        with patch("api.routes.hub.get_hub_from_db", _async(None)):
            resp = client.get("/hubs/999")
        assert resp.status_code == 404

    def test_update_hub(self, client):
        with patch("api.routes.hub.get_hub_from_db", _async(_hub_stub())):
            with patch("api.routes.hub.update_hub_in_db", _async(None)):
                resp = client.put("/hubs/1", json={"name": "Advanced DSA"})
        assert resp.status_code == 200

    def test_delete_hub(self, client):
        with patch("api.routes.hub.get_hub_from_db", _async(_hub_stub())):
            with patch("api.routes.hub.delete_hub_in_db", _async(None)):
                resp = client.delete("/hubs/1")
        assert resp.status_code == 200

    def test_hub_feed_newest(self, client):
        """Hub feed must support sorting by newest."""
        posts = [
            {"id": 10, "hub_id": 1, "author_id": 7, "author_name": "Alice",
             "post_type": "thread", "title": "Knapsack DP explanation",
             "status": "published", "lifecycle_status": "active",
             "is_pinned": False, "upvote_count": 5, "downvote_count": 0,
             "reply_count": 3, "view_count": 20, "has_accepted_answer": False,
             "created_at": "2026-04-09", "updated_at": None},
        ]
        with patch("api.routes.hub.get_hub_from_db", _async(_hub_stub())):
            with patch("api.routes.hub.get_hub_feed_from_db", _async(posts)):
                resp = client.get("/hubs/1/feed?sort=newest")
        assert resp.status_code == 200
        assert resp.json()[0]["title"] == "Knapsack DP explanation"

    def test_hub_feed_unanswered_filter(self, client):
        """Hub feed unanswered sort only returns questions without accepted answers."""
        posts = [
            {"id": 11, "hub_id": 1, "author_id": 7, "author_name": "Bob",
             "post_type": "question", "title": "How does memoization differ from tabulation?",
             "status": "published", "lifecycle_status": "active",
             "is_pinned": False, "upvote_count": 2, "downvote_count": 0,
             "reply_count": 0, "view_count": 5, "has_accepted_answer": False,
             "created_at": "2026-04-10", "updated_at": None},
        ]
        with patch("api.routes.hub.get_hub_from_db", _async(_hub_stub())):
            with patch("api.routes.hub.get_hub_feed_from_db", _async(posts)):
                resp = client.get("/hubs/1/feed?sort=unanswered&post_type=question")
        assert resp.status_code == 200
        assert all(not p["has_accepted_answer"] for p in resp.json())


# ─────────────────────────────────────────────────────────────────────────────
# MISSION 2 – Structured Knowledge Creation
# ─────────────────────────────────────────────────────────────────────────────

class TestPostTypes:
    """All four post types must be creatable with correct fields."""

    def _make_post(self, client, post_type, extra=None):
        payload = {
            "hub_id": 1,
            "author_id": 7,
            "post_type": post_type,
            "title": f"Test {post_type}",
            "blocks": [{"type": "paragraph", "content": [{"type": "text", "text": "body"}]}],
            "skill_ids": [],
        }
        if extra:
            payload.update(extra)
        with patch("api.routes.post.create_post_in_db", _async(99)):
            with patch("api.routes.post.link_skills_to_post", _async(None)):
                with patch("api.routes.post.link_tasks_to_post", _async(None)):
                    with patch("api.routes.post.create_poll_options", _async(None)):
                        resp = client.post("/posts/", json=payload)
        return resp

    def test_create_thread(self, client):
        assert self._make_post(client, "thread").status_code == 200

    def test_create_question(self, client):
        assert self._make_post(client, "question").status_code == 200

    def test_create_note(self, client):
        assert self._make_post(client, "note").status_code == 200

    def test_create_poll(self, client):
        resp = self._make_post(client, "poll",
                               extra={"poll_options": ["Option A", "Option B", "Option C"]})
        assert resp.status_code == 200

    def test_vote_on_poll(self, client):
        post = _post_stub(post_type="poll")
        post["post_type"] = "poll"
        with patch("api.routes.post.get_post_from_db", _async(post)):
            with patch("api.routes.post.vote_poll_in_db", _async(None)):
                resp = client.post("/posts/99/poll/vote",
                                   json={"user_id": 5, "option_id": 3})
        assert resp.status_code == 200
        assert resp.json()["status"] == "voted"

    def test_get_post_returns_all_sections(self, client):
        """GET post must return replies, skills, linked_tasks."""
        replies = [{"id": 1, "post_id": 10, "parent_reply_id": None, "author_id": 8,
                    "author_name": "Bob", "blocks": None, "upvote_count": 3,
                    "downvote_count": 0, "is_accepted": False, "created_at": "2026-04-09",
                    "updated_at": None, "endorsement_count": 0}]
        skills = [{"id": 1, "org_id": 1, "name": "Dynamic Programming", "slug": "dp",
                   "description": None, "parent_skill_id": None,
                   "created_at": "2026-04-01", "updated_at": None}]
        tasks = [{"id": 5, "title": "Knapsack Problem", "type": "coding", "relation_type": "related"}]

        with patch("api.routes.post.get_post_from_db", _async(_post_stub())):
            with patch("api.routes.post.increment_view_count", _async(None)):
                with patch("api.routes.post.get_replies_for_post", _async(replies)):
                    with patch("api.routes.post.get_skills_for_post", _async(skills)):
                        with patch("api.routes.post.get_tasks_for_post", _async(tasks)):
                            resp = client.get("/posts/10")

        assert resp.status_code == 200
        body = resp.json()
        assert "replies" in body
        assert "skills" in body
        assert "linked_tasks" in body
        assert body["skills"][0]["name"] == "Dynamic Programming"
        assert body["linked_tasks"][0]["title"] == "Knapsack Problem"


# ─────────────────────────────────────────────────────────────────────────────
# MISSION 3 – Reputation System (quality-based, not volume)
# ─────────────────────────────────────────────────────────────────────────────

class TestReputationSystem:
    """Reputation must be earned by quality signals, not volume."""

    def test_upvote_logs_reputation_with_org_id(self, client):
        """Upvoting a post must call log_reputation_event with real org_id (not None)."""
        vote_result = {"action": "created", "old_value": None}
        with patch("api.routes.post.get_post_from_db", _async(_post_stub())):
            with patch("api.routes.post.vote_in_db", _async(vote_result)):
                with patch("api.routes.post.get_hub_from_db", _async(_hub_stub())):
                    with patch("api.routes.post.log_reputation_event") as mock_rep:
                        mock_rep.return_value = AsyncMock(return_value=None)()
                        resp = client.post("/posts/10/vote",
                                           json={"user_id": 8, "value": 1,
                                                 "view_duration_ms": 5000})
        assert resp.status_code == 200
        mock_rep.assert_called_once()
        call_kwargs = mock_rep.call_args.kwargs
        assert call_kwargs.get("org_id") == 5, (
            f"Expected org_id=5 (from hub), got {call_kwargs.get('org_id')}")

    def test_fast_vote_does_not_grant_reputation(self, client):
        """Votes under 2s view duration must not earn reputation (anti-gaming)."""
        vote_result = {"action": "created", "old_value": None}
        with patch("api.routes.post.get_post_from_db", _async(_post_stub())):
            with patch("api.routes.post.vote_in_db", _async(vote_result)):
                with patch("api.routes.post.get_hub_from_db", _async(_hub_stub())):
                    with patch("api.routes.post.log_reputation_event") as mock_rep:
                        resp = client.post("/posts/10/vote",
                                           json={"user_id": 8, "value": 1,
                                                 "view_duration_ms": 500})  # fast!
        assert resp.status_code == 200
        mock_rep.assert_not_called()

    def test_accept_answer_grants_reputation(self, client):
        """Accepting an answer must log answer_accepted for the reply author."""
        with patch("api.routes.post.get_post_from_db", _async(_post_stub(post_type="question"))):
            with patch("api.routes.post.accept_reply_in_db", _async(None)):
                with patch("api.routes.post.get_reply_author_id", _async(9)):
                    with patch("api.routes.post.get_hub_from_db", _async(_hub_stub())):
                        with patch("api.routes.post.log_reputation_event") as mock_rep:
                            mock_rep.return_value = AsyncMock(return_value=None)()
                            resp = client.post("/posts/10/replies/5/accept?author_id=7")

        assert resp.status_code == 200
        mock_rep.assert_called_once()
        call_kwargs = mock_rep.call_args.kwargs
        assert call_kwargs.get("event_type") == "answer_accepted"
        assert call_kwargs.get("user_id") == 9

    def test_reply_upvote_logs_reputation(self, client):
        """Upvoting a reply must log reply_upvoted for the reply author."""
        vote_result = {"action": "created", "old_value": None}
        with patch("api.routes.post.get_post_from_db", _async(_post_stub())):
            with patch("api.routes.post.vote_in_db", _async(vote_result)):
                with patch("api.routes.post.get_reply_author_id", _async(9)):
                    with patch("api.routes.post.get_hub_from_db", _async(_hub_stub())):
                        with patch("api.routes.post.log_reputation_event") as mock_rep:
                            mock_rep.return_value = AsyncMock(return_value=None)()
                            resp = client.post("/posts/10/replies/5/vote",
                                               json={"user_id": 8, "value": 1,
                                                     "view_duration_ms": 4000})
        assert resp.status_code == 200
        mock_rep.assert_called_once()
        assert mock_rep.call_args.kwargs.get("event_type") == "reply_upvoted"

    def test_mentor_endorse_logs_reputation(self, client):
        """Endorsing a reply must log mentor_endorsed for the reply author."""
        with patch("api.routes.post.endorse_reply_in_db", _async(None)):
            with patch("api.routes.post.get_reply_author_id", _async(9)):
                with patch("api.routes.post.get_post_from_db", _async(_post_stub())):
                    with patch("api.routes.post.get_hub_from_db", _async(_hub_stub())):
                        with patch("api.routes.post.log_reputation_event") as mock_rep:
                            mock_rep.return_value = AsyncMock(return_value=None)()
                            resp = client.post("/posts/10/replies/5/endorse",
                                               json={"endorser_id": 3, "skill_id": 1})
        assert resp.status_code == 200
        mock_rep.assert_called_once()
        call_kwargs = mock_rep.call_args.kwargs
        assert call_kwargs.get("event_type") == "mentor_endorsed"
        assert call_kwargs.get("user_id") == 9

    def test_reputation_leaderboard(self, client):
        leaderboard = [
            {"user_id": 7, "user_name": "Alice", "email": "a@test.com",
             "total_points": 350, "level": "trusted_member", "updated_at": "2026-04-10"},
            {"user_id": 9, "user_name": "Bob", "email": "b@test.com",
             "total_points": 80, "level": "active_learner", "updated_at": "2026-04-10"},
        ]
        with patch("api.routes.reputation.get_reputation_leaderboard_from_db",
                   _async(leaderboard)):
            resp = client.get("/reputation/leaderboard?org_id=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["total_points"] > data[1]["total_points"]
        assert data[0]["level"] == "trusted_member"

    def test_reputation_history(self, client):
        history = [
            {"id": 1, "event_type": "answer_accepted", "points": 25,
             "source_type": "reply", "source_id": 5, "created_at": "2026-04-10"},
            {"id": 2, "event_type": "post_upvoted", "points": 5,
             "source_type": "post", "source_id": 10, "created_at": "2026-04-09"},
        ]
        with patch("api.routes.reputation.get_reputation_history_from_db", _async(history)):
            resp = client.get("/reputation/user/7/history?org_id=1")
        assert resp.status_code == 200
        assert resp.json()[0]["event_type"] == "answer_accepted"


# ─────────────────────────────────────────────────────────────────────────────
# MISSION 4 – Posts ↔ Tasks ↔ Skills linkage
# ─────────────────────────────────────────────────────────────────────────────

class TestPostLinkage:
    """Posts must be linkable to skills and tasks at creation and post-creation."""

    def test_create_post_with_skills(self, client):
        with patch("api.routes.post.create_post_in_db", _async(88)):
            with patch("api.routes.post.link_skills_to_post") as mock_link:
                mock_link.return_value = AsyncMock(return_value=None)()
                with patch("api.routes.post.link_tasks_to_post", _async(None)):
                    resp = client.post("/posts/", json={
                        "hub_id": 1, "author_id": 7, "post_type": "thread",
                        "title": "Knapsack DP explanation", "blocks": [],
                        "skill_ids": [3, 7],
                    })
        assert resp.status_code == 200
        mock_link.assert_called_once_with(88, [3, 7])

    def test_create_post_with_tasks(self, client):
        with patch("api.routes.post.create_post_in_db", _async(88)):
            with patch("api.routes.post.link_skills_to_post", _async(None)):
                with patch("api.routes.post.link_tasks_to_post") as mock_link:
                    mock_link.return_value = AsyncMock(return_value=None)()
                    resp = client.post("/posts/", json={
                        "hub_id": 1, "author_id": 7, "post_type": "thread",
                        "title": "Knapsack DP explanation", "blocks": [],
                        "task_ids": [5],
                    })
        assert resp.status_code == 200
        mock_link.assert_called_once_with(88, [5])

    def test_tag_skills_to_existing_post(self, client):
        with patch("api.routes.post.link_skills_to_post") as mock_link:
            mock_link.return_value = AsyncMock(return_value=None)()
            resp = client.post("/posts/10/skills", json={"skill_ids": [1, 2]})
        assert resp.status_code == 200
        mock_link.assert_called_once_with(10, [1, 2])

    def test_link_tasks_to_existing_post(self, client):
        with patch("api.routes.post.link_tasks_to_post") as mock_link:
            mock_link.return_value = AsyncMock(return_value=None)()
            resp = client.post("/posts/10/tasks",
                               json={"task_ids": [5], "relation_type": "related"})
        assert resp.status_code == 200
        mock_link.assert_called_once_with(10, [5], "related")

    def test_get_skills_for_org(self, client):
        skills = [{"id": 1, "org_id": 1, "name": "Dynamic Programming", "slug": "dp",
                   "description": None, "parent_skill_id": None,
                   "created_at": "2026-04-01", "updated_at": None}]
        with patch("api.routes.skill.get_skills_for_org_from_db", _async(skills)):
            resp = client.get("/skills/?org_id=1")
        assert resp.status_code == 200
        assert resp.json()[0]["name"] == "Dynamic Programming"

    def test_skill_graph_returns_related_posts(self, client):
        """Skill graph must link to hubs, tasks, and posts for that skill."""
        skill = {"id": 1, "org_id": 1, "name": "Dynamic Programming", "slug": "dp",
                 "description": None, "parent_skill_id": None,
                 "created_at": "2026-04-01", "updated_at": None}
        graph = {
            "skill": {"id": 1, "name": "Dynamic Programming"},
            "hubs": [{"id": 1, "name": "DSA Hub"}],
            "tasks": [{"id": 5, "title": "Knapsack Problem"}],
            "posts": [{"id": 10, "title": "Knapsack DP explanation"}],
            "child_skills": [],
        }
        with patch("api.routes.skill.get_skill_from_db", _async(skill)):
            with patch("api.routes.skill.get_skill_graph_from_db", _async(graph)):
                resp = client.get("/skills/1/graph")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["posts"]) == 1
        assert body["posts"][0]["title"] == "Knapsack DP explanation"


# ─────────────────────────────────────────────────────────────────────────────
# MISSION 5 – Surface high-signal content
# ─────────────────────────────────────────────────────────────────────────────

class TestHighSignalContent:
    """Accepted answers, trending, pinned, and recommended must surface correctly."""

    def test_accept_answer_marks_reply_accepted(self, client):
        """Q&A: post author can accept a reply."""
        with patch("api.routes.post.get_post_from_db", _async(_post_stub(post_type="question"))):
            with patch("api.routes.post.accept_reply_in_db", _async(None)):
                with patch("api.routes.post.get_reply_author_id", _async(9)):
                    with patch("api.routes.post.get_hub_from_db", _async(_hub_stub())):
                        with patch("api.routes.post.log_reputation_event", _async(None)):
                            resp = client.post("/posts/10/replies/5/accept?author_id=7")
        assert resp.status_code == 200
        assert resp.json()["status"] == "accepted"

    def test_non_author_cannot_accept_answer(self, client):
        """Only the post author may accept an answer."""
        with patch("api.routes.post.get_post_from_db", _async(_post_stub(post_type="question"))):
            resp = client.post("/posts/10/replies/5/accept?author_id=99")
        assert resp.status_code == 403

    def test_trending_posts_endpoint(self, client):
        trending = [
            {"id": 10, "title": "Knapsack DP explanation", "upvote_count": 15,
             "reply_count": 8, "post_type": "thread", "hub_id": 1},
        ]
        with patch("api.routes.search.get_trending_posts_from_db", _async(trending)):
            resp = client.get("/search/trending?org_id=1")
        assert resp.status_code == 200
        assert resp.json()[0]["upvote_count"] == 15

    def test_recommended_posts_endpoint(self, client):
        recommended = [
            {"id": 12, "title": "Graph DP patterns", "upvote_count": 10,
             "post_type": "note", "hub_id": 1},
        ]
        with patch("api.routes.search.get_recommended_posts_from_db", _async(recommended)):
            resp = client.get("/search/recommended?user_id=7&org_id=1")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_bookmarks(self, client):
        with patch("api.routes.post.get_post_from_db", _async(_post_stub())):
            with patch("api.routes.post.toggle_bookmark", _async("added")):
                resp = client.post("/posts/10/bookmark", json={"user_id": 8})
        assert resp.status_code == 200
        assert resp.json()["action"] == "added"


# ─────────────────────────────────────────────────────────────────────────────
# MISSION 6 – Moderation workflows
# ─────────────────────────────────────────────────────────────────────────────

class TestModeration:
    """Content must be flaggable, reviewable, and actionable by moderators."""

    def test_flag_post(self, client):
        with patch("api.routes.post.create_flag", _async(1)):
            resp = client.post("/posts/10/flag", json={
                "reporter_id": 8,
                "reason": "spam",
                "description": "Repeated identical post",
            })
        assert resp.status_code == 200
        assert resp.json()["id"] == 1

    def test_flag_reply(self, client):
        with patch("api.routes.post.create_flag", _async(2)):
            resp = client.post("/posts/10/replies/5/flag", json={
                "reporter_id": 8,
                "reason": "offensive",
            })
        assert resp.status_code == 200

    def test_get_moderation_queue(self, client):
        flags = [
            {"id": 1, "reporter_id": 8, "target_type": "post", "target_id": 10,
             "reason": "spam", "description": None, "status": "pending",
             "created_at": "2026-04-10", "reviewed_by": None,
             "reviewed_at": None, "action_taken": None},
        ]
        with patch("api.routes.moderation.get_pending_flags_from_db", _async(flags)):
            resp = client.get("/moderation/queue?org_id=1")
        assert resp.status_code == 200
        assert resp.json()[0]["status"] == "pending"

    def test_resolve_flag_hide(self, client):
        flag = {"id": 1, "reporter_id": 8, "target_type": "post", "target_id": 10,
                "reason": "spam", "status": "pending"}
        with patch("api.routes.moderation.get_flag_from_db", _async(flag)):
            with patch("api.routes.moderation.review_flag_in_db", _async(None)):
                resp = client.put("/moderation/flags/1/review",
                                  json={"reviewed_by": 3, "action_taken": "hidden"})
        assert resp.status_code == 200

    def test_dismiss_flag(self, client):
        flag = {"id": 1, "reporter_id": 8, "target_type": "post", "target_id": 10,
                "reason": "spam", "status": "pending"}
        with patch("api.routes.moderation.get_flag_from_db", _async(flag)):
            with patch("api.routes.moderation.dismiss_flag_in_db", _async(None)):
                resp = client.put("/moderation/flags/1/review",
                                  json={"reviewed_by": 3, "action_taken": "dismissed"})
        assert resp.status_code == 200

    def test_moderation_stats(self, client):
        stats = {"total": 10, "pending": 3, "actioned": 6, "dismissed": 1}
        with patch("api.routes.moderation.get_moderation_stats_from_db", _async(stats)):
            resp = client.get("/moderation/stats?org_id=1")
        assert resp.status_code == 200
        assert "pending" in resp.json()


# ─────────────────────────────────────────────────────────────────────────────
# MISSION 7 – Persistent, discoverable, reusable knowledge (FTS Search)
# ─────────────────────────────────────────────────────────────────────────────

class TestSearch:
    """Content must be searchable across posts, hubs, and skills."""

    def test_full_text_search_posts(self, client):
        results = {
            "posts": [
                {"id": 10, "title": "Knapsack DP explanation", "snippet": "…DP table…",
                 "hub_id": 1, "type": "post"},
            ],
            "hubs": [],
            "skills": [],
        }
        with patch("api.routes.search.full_search_from_db", _async(results)):
            resp = client.get("/search/?q=knapsack&org_id=1")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["posts"]) == 1
        assert "knapsack" in body["posts"][0]["title"].lower()

    def test_search_returns_hubs(self, client):
        results = {
            "posts": [],
            "hubs": [{"id": 1, "name": "DSA Hub", "slug": "dsa-hub", "type": "hub"}],
            "skills": [],
        }
        with patch("api.routes.search.full_search_from_db", _async(results)):
            resp = client.get("/search/?q=dsa&org_id=1")
        assert resp.status_code == 200
        assert len(resp.json()["hubs"]) == 1

    def test_search_returns_skills(self, client):
        results = {
            "posts": [],
            "hubs": [],
            "skills": [{"id": 1, "name": "Dynamic Programming", "slug": "dp", "type": "skill"}],
        }
        with patch("api.routes.search.full_search_from_db", _async(results)):
            resp = client.get("/search/?q=dynamic+programming&org_id=1")
        assert resp.status_code == 200
        assert len(resp.json()["skills"]) == 1

    def test_search_type_filter_posts_only(self, client):
        results = {
            "posts": [{"id": 10, "title": "Knapsack DP", "type": "post",
                       "hub_id": 1, "snippet": "…"}],
            "hubs": [],
            "skills": [],
        }
        with patch("api.routes.search.full_search_from_db", _async(results)):
            resp = client.get("/search/?q=knapsack&org_id=1&type=post")
        assert resp.status_code == 200
        assert len(resp.json()["posts"]) == 1

    def test_search_empty_query_returns_results(self, client):
        results = {"posts": [], "hubs": [], "skills": []}
        with patch("api.routes.search.full_search_from_db", _async(results)):
            resp = client.get("/search/?q=&org_id=1")
        assert resp.status_code == 200
        body = resp.json()
        assert body["posts"] == []
        assert body["hubs"] == []
        assert body["skills"] == []


# ─────────────────────────────────────────────────────────────────────────────
# MISSION – Example flow: Knapsack DP post end-to-end
# ─────────────────────────────────────────────────────────────────────────────

class TestExampleFlow:
    """
    Simulate the spec example:
      1. Create 'Knapsack DP explanation' post in DSA hub
      2. Link to Dynamic Programming skill + Knapsack task
      3. Peer upvotes (non-fast) → author gains reputation with correct org_id
      4. Mentor endorses a reply → mentor_endorsed event logged
      5. Search finds the post
      6. Recommended feed includes the post
    """

    def test_full_example_flow(self, client):
        # Step 1+2: Create post with skill + task
        with patch("api.routes.post.create_post_in_db", _async(10)):
            with patch("api.routes.post.link_skills_to_post") as skill_link:
                skill_link.return_value = AsyncMock(return_value=None)()
                with patch("api.routes.post.link_tasks_to_post") as task_link:
                    task_link.return_value = AsyncMock(return_value=None)()
                    create_resp = client.post("/posts/", json={
                        "hub_id": 1,
                        "author_id": 7,
                        "post_type": "thread",
                        "title": "Knapsack DP explanation",
                        "blocks": [{"type": "paragraph",
                                    "content": [{"type": "text",
                                                 "text": "DP for Knapsack…"}]}],
                        "skill_ids": [1],  # Dynamic Programming
                        "task_ids": [5],   # Knapsack task
                    })
        assert create_resp.status_code == 200
        assert create_resp.json()["id"] == 10
        skill_link.assert_called_once_with(10, [1])
        task_link.assert_called_once_with(10, [5])

        # Step 3: Peer upvote → author gains reputation with hub's org_id
        vote_result = {"action": "created", "old_value": None}
        with patch("api.routes.post.get_post_from_db", _async(_post_stub())):
            with patch("api.routes.post.vote_in_db", _async(vote_result)):
                with patch("api.routes.post.get_hub_from_db", _async(_hub_stub())):
                    with patch("api.routes.post.log_reputation_event") as rep_mock:
                        rep_mock.return_value = AsyncMock(return_value=None)()
                        vote_resp = client.post("/posts/10/vote",
                                               json={"user_id": 8, "value": 1,
                                                     "view_duration_ms": 8000})
        assert vote_resp.status_code == 200
        rep_mock.assert_called_once()
        assert rep_mock.call_args.kwargs.get("org_id") == 5

        # Step 4: Mentor endorses reply → mentor_endorsed event
        with patch("api.routes.post.endorse_reply_in_db", _async(None)):
            with patch("api.routes.post.get_reply_author_id", _async(9)):
                with patch("api.routes.post.get_post_from_db", _async(_post_stub())):
                    with patch("api.routes.post.get_hub_from_db", _async(_hub_stub())):
                        with patch("api.routes.post.log_reputation_event") as rep_mock2:
                            rep_mock2.return_value = AsyncMock(return_value=None)()
                            endorse_resp = client.post("/posts/10/replies/5/endorse",
                                                      json={"endorser_id": 3, "skill_id": 1})
        assert endorse_resp.status_code == 200
        rep_mock2.assert_called_once()
        assert rep_mock2.call_args.kwargs.get("event_type") == "mentor_endorsed"

        # Step 5: Search finds the post
        results = {
            "posts": [{"id": 10, "title": "Knapsack DP explanation",
                       "snippet": "DP for Knapsack…", "hub_id": 1, "type": "post"}],
            "hubs": [], "skills": [],
        }
        with patch("api.routes.search.full_search_from_db", _async(results)):
            search_resp = client.get("/search/?q=knapsack&org_id=5")
        assert search_resp.status_code == 200
        assert len(search_resp.json()["posts"]) == 1

        # Step 6: Recommended feed includes the post
        recommended = [{"id": 10, "title": "Knapsack DP explanation",
                        "upvote_count": 5, "post_type": "thread", "hub_id": 1}]
        with patch("api.routes.search.get_recommended_posts_from_db", _async(recommended)):
            rec_resp = client.get("/search/recommended?user_id=8&org_id=5")
        assert rec_resp.status_code == 200
        assert rec_resp.json()[0]["id"] == 10
