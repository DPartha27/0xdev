# Learning Network Platform — Build Checklist

> Track phase completion. Each phase is self-contained and independently deployable.
> Update this file as each item is completed: `[ ]` → `[x]`

---

## Phase 1: Skills & Knowledge Graph Foundation
> **Why first**: Skills are the connective tissue — hubs, posts, tasks, and users all link through them.

### Backend
- [x] `config.py` — add `skills_table_name`, `task_skills_table_name`, `user_skills_table_name`
- [x] `db/__init__.py` — add `create_skills_table()`, `create_task_skills_table()`, `create_user_skills_table()`, call in `init_db()`
- [x] `db/skill.py` — CRUD queries: create, get, update, soft-delete, list, link to tasks, user skill profiles
- [x] `models.py` — add `CreateSkillRequest`, `UpdateSkillRequest`, `LinkSkillsToTasksRequest`, `Skill` response model
- [x] `routes/skill.py` — FastAPI router with all 8 endpoints
- [x] `main.py` — register skill router
- [x] `db/migration.py` — add migration for existing databases

### Frontend
- [x] `src/types/network.ts` — all new TypeScript interfaces (Hub, Post, Reply, Skill, Reputation, etc.)
- [x] `src/types/index.ts` — re-export from network.ts
- [x] `src/components/SkillTag.tsx` — colored tag chip component
- [x] `src/components/SkillTagPicker.tsx` — autocomplete multi-select

---

## Phase 2: Topic Hubs
> **Depends on**: Phase 1 (skills)

### Backend
- [x] `config.py` — add hub table name constants (4 tables)
- [x] `db/__init__.py` — add hub table creation functions, call in `init_db()`
- [x] `db/hub.py` — Hub CRUD, membership, skill/course linking, feed queries
- [x] `models.py` — add `HubVisibility`, `HubMemberRole` enums, `CreateHubRequest`, `UpdateHubRequest`, `AddHubMembersRequest`, `HubSummary` response
- [x] `routes/hub.py` — FastAPI router with all 11 endpoints
- [x] `main.py` — register hub router
- [x] `db/migration.py` — add hub tables migration

### Frontend
- [x] `src/context/NetworkContext.tsx` — active hub, user hub role context
- [x] `src/app/school/[id]/network/layout.tsx` — NetworkContext provider
- [x] `src/app/school/[id]/network/page.tsx` — hub listing page
- [x] `src/app/school/[id]/network/[hubSlug]/page.tsx` — hub detail page
- [x] `src/app/school/[id]/network/[hubSlug]/settings/page.tsx` — hub settings
- [x] `src/app/school/admin/[id]/network/page.tsx` — admin network dashboard
- [x] `src/components/HubCard.tsx` — hub card component
- [x] `src/components/HubListView.tsx` — grid with search/filter
- [x] `src/components/HubDetailView.tsx` — hub page with feed tabs
- [x] `src/lib/network-api.ts` — API hooks and mutations
- [x] `ClientSchoolMemberView.tsx` — add Network tab
- [x] `ClientSchoolAdminView.tsx` — add Network tab

---

## Phase 3: Posts, Replies, Voting & Bookmarks
> **Depends on**: Phase 1 (skills), Phase 2 (hubs)

### Backend
- [x] `config.py` — add post table constants (8 tables)
- [x] `db/__init__.py` — add post table creation functions, call in `init_db()`
- [x] `db/post.py` — Post CRUD, replies, votes, bookmarks, polls, linking
- [x] `models.py` — add `PostType`, `PostStatus`, `VoteValue` enums; `CreatePostRequest`, `UpdatePostRequest`, `CreateReplyRequest`, `VoteRequest`, `BookmarkRequest`, `PollVoteRequest`, `EndorseReplyRequest`; `PostSummary`, `PostDetail`, `Reply` responses
- [x] `routes/post.py` — FastAPI router with all 15 endpoints
- [x] `main.py` — register post router
- [x] `db/migration.py` — add post tables migration

### Frontend
- [x] `src/app/school/[id]/network/[hubSlug]/posts/[postId]/page.tsx` — post detail page
- [x] `src/components/PostCard.tsx` — compact post preview in feed (lifecycle badges included)
- [x] `src/components/PostDetailView.tsx` — full post view
- [x] `src/components/PostComposer.tsx` — post creation form (type selector, body, skills, poll builder)
- [x] `src/components/PostTypeBadge.tsx` — Thread/Q&A/Note/Poll badge
- [x] `src/components/VoteButtons.tsx` — upvote/downvote with optimistic updates
- [x] `src/components/BookmarkButton.tsx` — toggle with optimistic update
- [x] `src/components/ShareButton.tsx` — copy link dialog
- [x] `src/components/ReplyList.tsx` — nested reply tree
- [x] `src/components/ReplyItem.tsx` — single reply with voting and accept button
- [x] `src/components/ReplyComposer.tsx` — inline reply editor
- [x] `src/components/PollOptionEditor.tsx` — poll creation form
- [x] `src/components/PollDisplay.tsx` — poll with vote bars and percentages
- [x] `src/lib/network-api.ts` — post/reply/vote/bookmark hooks and mutations

---

## Phase 4: Reputation System
> **Depends on**: Phase 3 (votes, replies, endorsements trigger reputation events)

### Backend
- [x] `config.py` — add reputation table constants (5 tables) + `REPUTATION_LEVELS`, `REPUTATION_POINTS`, `REPUTATION_DAILY_CAP`
- [x] `db/__init__.py` — add reputation table creation functions, call in `init_db()`
- [x] `db/reputation.py` — log_reputation_event(), get_user_reputation(), leaderboard, recalculate, vote ring detection
- [x] `models.py` — add `ReputationLevel` enum; `UserReputation`, `ReputationEvent` response models
- [x] `routes/reputation.py` — FastAPI router with 3 endpoints
- [x] `main.py` — register reputation router
- [x] `db/migration.py` — add reputation tables migration
- [x] `db/post.py` — wire reputation events into vote/accept/endorse actions

### Frontend
- [x] `src/components/ReputationBadge.tsx` — inline tier icon + points
- [x] `src/components/ReputationCard.tsx` — expanded profile card with level progress bar
- [x] `src/components/ContributionHistory.tsx` — event timeline
- [x] `src/app/school/[id]/network/profile/[userId]/page.tsx` — user reputation profile page
- [x] `src/lib/network-api.ts` — useUserReputation(), useReputationHistory(), useReputationLeaderboard() hooks

---

## Phase 5: Moderation & Content Curation
> **Depends on**: Phase 3 (posts/replies to flag), Phase 4 (tier-gated moderation queue)

### Backend
- [x] `config.py` — add `flags_table_name`
- [x] `db/__init__.py` — add `create_flags_table()`, call in `init_db()`
- [x] `db/moderation.py` — flag CRUD, review queue, stats queries
- [x] `models.py` — add `FlagReason`, `FlagStatus` enums; `FlagContentRequest`, `ReviewFlagRequest` models
- [x] `routes/moderation.py` — FastAPI router with 3 endpoints
- [x] `main.py` — register moderation router
- [x] `db/migration.py` — add flags table migration

### Frontend
- [x] `src/app/school/admin/[id]/network/page.tsx` — moderation queue view (included in admin dashboard)
- [x] `src/components/FlagContentDialog.tsx` — dialog for flagging with reason selection
- [x] `src/components/ModerationQueueView.tsx` — flagged items with action buttons
- [x] `src/lib/network-api.ts` — flagContent(), resolveFlag(), featurePost() mutations

---

## Phase 6: Search & Discovery
> **Depends on**: Phase 2 (hubs), Phase 3 (posts), Phase 1 (skills)

### Backend
- [x] `db/__init__.py` — FTS5 virtual tables for posts, skills, hubs (via search module)
- [x] `db/search.py` — FTS5 query functions, trending (vote/reply velocity), recommendations
- [x] `models.py` — add `SearchResult` response model
- [x] `routes/search.py` — FastAPI router with 3 endpoints (search, trending, recommended)
- [x] `main.py` — register search router
- [x] `db/migration.py` — add FTS tables migration

### Frontend
- [x] `src/app/school/[id]/network/search/page.tsx` — search results page
- [x] `src/components/NetworkSearchBar.tsx` — search input with type filter and dropdown
- [x] `src/components/SearchResultsList.tsx` — mixed results renderer
- [x] `src/components/TrendingFeed.tsx` — trending content section
- [x] `src/components/RecommendedPosts.tsx` — personalized sidebar
- [x] `src/lib/network-api.ts` — useNetworkSearch(), useTrendingPosts(), useRecommendedPosts() hooks

---

## Phase 7: Knowledge Persistence & Anti-Dead-Forum
> **Depends on**: All prior phases. Adds lifecycle management and automated engagement.

### Backend
- [x] `db/post.py` — content lifecycle state machine (Active → Stale → Archived → Evergreen), `update_post_lifecycle()`, `get_posts_for_staleness_check()`
- [x] `scheduler.py` — daily stale check, daily vote ring detection, weekly reputation reconciliation
- [x] `db/reputation.py` — `detect_vote_rings()` background job implementation

### Frontend
- [x] `src/components/PostCard.tsx` — Stale/Archived/Evergreen lifecycle badges rendered
- [x] `src/components/PostDetailView.tsx` — Evergreen badge shown
- [x] `src/components/HubDetailView.tsx` — lifecycle filter built into post feed tabs

---

## Phase 8: Knowledge Graph Navigation
> **Depends on**: All prior phases. Pure frontend visualization layer.

### Frontend
- [x] `src/app/school/[id]/network/profile/[userId]/page.tsx` — user profile with reputation card + contribution history
- [ ] `src/components/SkillProfileView.tsx` — skill radar/list with linked courses + proficiency (future enhancement)
- [ ] `src/components/KnowledgeGraphView.tsx` — interactive graph (future enhancement, requires react-force-graph-2d)
- [x] `src/lib/network-api.ts` — getUserSkillProfile(), getSkillGraph() functions available

---

## Summary

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Skills & Knowledge Graph Foundation | ✅ Complete |
| 2 | Topic Hubs | ✅ Complete |
| 3 | Posts, Replies, Voting & Bookmarks | ✅ Complete |
| 4 | Reputation System | ✅ Complete |
| 5 | Moderation & Content Curation | ✅ Complete |
| 6 | Search & Discovery | ✅ Complete |
| 7 | Knowledge Persistence & Anti-Dead-Forum | ✅ Complete |
| 8 | Knowledge Graph Navigation | 🔄 Core complete (graph viz deferred) |
