Learning Network Platform — Hubs, Reputation & Knowledge Graphs
Context
SensAI is an AI-first LMS built with FastAPI + SQLite (raw SQL/aiosqlite) on the backend and Next.js 15 + React 19 + Tailwind + Radix UI on the frontend. Currently, all learning interactions are user-to-AI (chat within tasks) — there is no peer-to-peer discussion, no skill taxonomy, no reputation system, and no knowledge persistence layer. The badges and tags tables were previously dropped.

This plan introduces a collaborative knowledge ecosystem that transforms isolated learning into persistent, discoverable, cross-cohort knowledge — while rewarding quality contributions over volume.

Phase 1: Skills & Knowledge Graph Foundation
Why first: Skills are the connective tissue linking hubs, posts, tasks, and users. Every subsequent phase depends on them.

Backend
New files:

sensai-backend/src/api/db/skill.py — CRUD queries
sensai-backend/src/api/routes/skill.py — API endpoints
New tables (add to db/__init__.py, constants to config.py):

Table	Purpose
skills	Org-scoped skill taxonomy with hierarchical parent_skill_id (e.g., "Graphs" under "DSA")
task_skills	Many-to-many linking existing tasks to skills
user_skills	Per-user proficiency tracking (0-100 score, evidence count)
Key schema details:

skills(id, org_id, name, slug, description, parent_skill_id, created_at, updated_at, deleted_at) — UNIQUE(org_id, slug)
task_skills(id, task_id, skill_id) — UNIQUE(task_id, skill_id), FK to existing tasks
user_skills(id, user_id, skill_id, proficiency_level, evidence_count) — UNIQUE(user_id, skill_id)
API routes (/skills):

Method	Path	Description
GET	/skills/?org_id={id}	List skills (flat or tree)
POST	/skills/	Create skill
GET	/skills/{skill_id}	Skill detail + linked hubs/posts/tasks
PUT	/skills/{skill_id}	Update skill
DELETE	/skills/{skill_id}	Soft-delete
GET	/skills/{skill_id}/graph	Knowledge graph: related posts, tasks, hubs
GET	/skills/user/{user_id}	User skill profile
POST	/skills/tasks	Bulk-link skills to tasks
Frontend
New file: src/types/network.ts — all new TypeScript interfaces New component: SkillTag.tsx, SkillTagPicker.tsx (autocomplete multi-select)

Modify
config.py — add skills_table_name, task_skills_table_name, user_skills_table_name
db/__init__.py — add create_skills_table(), create_task_skills_table(), create_user_skills_table()
db/migration.py — add migration function for existing databases
main.py — register skill router
Phase 2: Topic Hubs
New files:

sensai-backend/src/api/db/hub.py
sensai-backend/src/api/routes/hub.py
New tables
Table	Purpose
hubs	Org-scoped discussion spaces (name, slug, description, icon, visibility: public/private/archived)
hub_members	Membership with roles: member/moderator/owner
hub_skills	Links hubs to skills
hub_courses	Links hubs to existing courses
Key schema: hubs(id, org_id, name, slug, description, icon, visibility, created_by, ...) — UNIQUE(org_id, slug), FK to organizations and users

API routes (/hubs)
Method	Path	Description
GET	/hubs/?org_id={id}	List hubs
POST	/hubs/	Create hub
GET	/hubs/{hub_id}	Hub detail (member count, skills, courses)
PUT	/hubs/{hub_id}	Update hub
DELETE	/hubs/{hub_id}	Soft-delete
POST	/hubs/{hub_id}/members	Add members
DELETE	/hubs/{hub_id}/members	Remove members
PUT	/hubs/{hub_id}/members/{user_id}/role	Promote to moderator
POST/DELETE	/hubs/{hub_id}/skills	Link/unlink skills
POST/DELETE	/hubs/{hub_id}/courses	Link/unlink courses
GET	/hubs/{hub_id}/feed	Paginated post feed with filters
Frontend routes
src/app/school/[id]/network/
  page.tsx                          # Hub listing
  layout.tsx                        # NetworkContext provider + hub sidebar
  [hubSlug]/
    page.tsx                        # Hub detail with post feed
    settings/page.tsx               # Hub settings (moderators)
    posts/new/page.tsx              # Create post
    posts/[postId]/page.tsx         # Single post view
  search/page.tsx                   # Cross-hub search
  profile/[userId]/page.tsx         # User skill & reputation profile

src/app/school/admin/[id]/network/
  page.tsx                          # Moderation dashboard
  hubs/new/page.tsx                 # Create hub
  hubs/[hubSlug]/page.tsx           # Admin hub management
New components
HubCard.tsx — card for hub listing (reuse existing ui/card.tsx)
HubListView.tsx — grid of HubCards with search/filter
HubDetailView.tsx — hub page with tabs (Feed / Popular / Unanswered)
Navigation integration
Add "Network" tab in ClientSchoolMemberView.tsx alongside cohort content
Add "Network" section in ClientSchoolAdminView.tsx for moderation
Use header centerSlot for breadcrumbs: School > Network > Hub > Post
Phase 3: Posts, Replies, Voting & Bookmarks (Core Content)
New files:

sensai-backend/src/api/db/post.py
sensai-backend/src/api/routes/post.py
New tables
Table	Purpose
posts	All content types: thread, question, note, poll. Uses blocks JSON column (same pattern as tasks.blocks)
post_skills	Links posts to skills (knowledge graph)
post_tasks	Links posts to tasks with relation_type: related/explains/extends
replies	Comments/answers with single-level nesting via parent_reply_id
votes	Polymorphic: target_type (post/reply) + target_id, value +1/-1, UNIQUE(user_id, target_type, target_id)
bookmarks	Per-user saved posts
poll_options	Options for poll-type posts
poll_votes	One vote per user per poll via UNIQUE(user_id, post_id)
Key design decisions
Denormalized counts on posts (upvote_count, downvote_count, reply_count, view_count) — avoids COUNT(*) on every feed load, updated atomically via UPDATE posts SET upvote_count = upvote_count + 1
Single-level reply nesting — parent_reply_id allows reply-to-reply but no deeper (keeps UI and queries manageable, like Stack Overflow)
Blocks JSON — reuses the existing Block pattern from tasks for rich content
Q&A accepted answers — posts.accepted_reply_id + replies.is_accepted for the Q&A workflow
API routes (/posts)
Method	Path	Description
POST	/posts/	Create post (thread/question/note/poll)
GET	/posts/{post_id}	Post with replies, user vote state, bookmark state
PUT	/posts/{post_id}	Update post
DELETE	/posts/{post_id}	Soft-delete
POST	/posts/{post_id}/replies	Add reply
PUT/DELETE	/posts/{post_id}/replies/{reply_id}	Edit/delete reply
POST	/posts/{post_id}/replies/{reply_id}/accept	Accept answer (Q&A, author only)
POST	/posts/{post_id}/vote	Upvote/downvote post
POST	/posts/{post_id}/replies/{reply_id}/vote	Upvote/downvote reply
POST	/posts/{post_id}/bookmark	Toggle bookmark
POST	/posts/{post_id}/skills	Tag with skills
POST	/posts/{post_id}/tasks	Link to tasks
POST	/posts/{post_id}/poll/vote	Cast poll vote
POST	/posts/{post_id}/replies/{reply_id}/endorse	Mentor endorsement
POST	/posts/{post_id}/flag	Flag for moderation
Frontend components
Post components:

PostCard.tsx — compact preview in feed (title, author, vote count, reply count, skill tags)
PostDetailView.tsx — full view with BlockNote content (readOnly mode)
PostComposer.tsx — creation form: type selector, title, BlockNoteEditor, skill picker, poll builder
PostTypeBadge.tsx — colored badge for Thread/Q&A/Note/Poll
Voting & interaction:

VoteButtons.tsx — upvote/downvote pair with optimistic updates (update local state immediately, fire API in background, revert on error)
BookmarkButton.tsx — toggle with toast feedback
ShareButton.tsx — copy link dialog
Reply components:

ReplyList.tsx — nested reply tree
ReplyItem.tsx — single reply with voting, accept button (Q&A)
ReplyComposer.tsx — inline editor (lightweight BlockNote or textarea+markdown)
Poll components:

PollOptionEditor.tsx — for creation
PollDisplay.tsx — rendered poll with voting bars and percentages
Reusable existing components
Existing	Reused For
BlockNoteEditor	PostComposer, PostDetailView, ReplyItem
ui/card.tsx	HubCard, PostCard
ui/tabs.tsx (Radix)	Hub feed tabs
ui/avatar.tsx	Author display
ConfirmationDialog.tsx	Delete confirmations
Toast.tsx	Vote/bookmark/flag feedback
Phase 4: Reputation System
New files:

sensai-backend/src/api/db/reputation.py
sensai-backend/src/api/routes/reputation.py
New tables
Table	Purpose
reputation_events	Immutable append-only log of all point changes (user_id, org_id, event_type, points, source_type, source_id, granted_by)
user_reputation	Materialized cache: total_points, level per user per org. UNIQUE(user_id, org_id)
endorsements	Mentor endorsements on replies (endorser_id, reply_id, skill_id). UNIQUE(endorser_id, reply_id)
vote_audit	Tracks voter→recipient pairs for anti-gaming detection
content_quality	AI quality scores per post (clarity, relevance, helpfulness, originality, composite)
Point Actions
Action	Points	Anti-Gaming Rule
Post upvoted	+5	Max 200pts/day from upvotes
Reply upvoted	+10	Max 200pts/day from upvotes
Post/reply downvoted	-2	—
Answer accepted (Q&A)	+25	Only question author can accept
Mentor endorsement	+50	Only mentor/expert role can endorse
Content flagged & removed	-50	After moderation review
Casting a downvote	-1	Costs voter 1 point (discourages frivolous)
Stale content decay	-1/30 days	On content >90 days with no activity
Quality-Over-Quantity Formula
quality_ratio = (votes_received + 2*accepted_answers + 5*endorsements) / max(1, total_posts + total_comments)
effective_reputation = raw_points * clamp(quality_ratio, 0.5, 2.0)
Reputation Tiers & Progressive Privileges
Tier	Name	Threshold	Unlocks
0	Newcomer	0	View, post, comment
1	Contributor	50	Upvote, create polls
2	Active Learner	100	Downvote, flag content
3	Trusted Member	300	Suggest edits to others' posts
4	Subject Expert	750	Close/reopen Q&A, pin posts
5	Community Leader	1500	Access moderation queue
Anti-Gaming Measures
Vote ring detection: Daily background job builds directed vote graph per org, detects strongly connected components where users exclusively vote on each other (>80% mutual over 7 days) — flags for admin review
Rate limits: 10 posts/day, 30 comments/day, 40 votes/day (enforced via in-memory cache)
Diminishing returns: First 10 upvotes on a post earn full points, 11-20 earn 50%, beyond 20 earn 0
Fast-vote detection: Votes cast within 2 seconds of opening a post earn 0 reputation for author
AI quality scoring: Background gpt-4.1-mini evaluation on post creation — posts scoring <0.3 earn 0 rep, >0.7 earn 1.5x multiplier (~$0.001/eval)
New member cooldown: Votes from users who joined <24h ago carry 0 reputation weight
Content Ranking Formula (for feed ordering)
score = (upvotes - downvotes)
        + 10 * is_accepted_answer
        + 20 * is_mentor_endorsed
        + ai_quality_score * 5
        - log2(max(1, hours_since_posted / 24))
API routes (/reputation)
Method	Path	Description
GET	/reputation/user/{user_id}?org_id={id}	User reputation summary
GET	/reputation/leaderboard?org_id={id}	Org reputation leaderboard
GET	/reputation/user/{user_id}/history?org_id={id}	Event history
Frontend components
ReputationBadge.tsx — inline tier icon + points next to usernames
ReputationCard.tsx — expanded profile with level, contribution history
ContributionHistory.tsx — timeline/chart
Integration with existing leaderboard
Extend GET /cohorts/{cohort_id}/leaderboard in routes/cohort.py to include reputation_score
Extend TopPerformers.tsx Performer interface with reputationScore and tier fields
Phase 5: Moderation & Content Curation
New files:

sensai-backend/src/api/db/moderation.py
sensai-backend/src/api/routes/moderation.py
New table
Table	Purpose
flags	Content flagging: reporter_id, target_type/id, reason (spam/offensive/off_topic/misinformation/other), status (pending/reviewed/actioned/dismissed), reviewed_by, action_taken
API routes (/moderation)
Method	Path	Description
GET	/moderation/queue?org_id={id}	Pending flags (moderators/admins)
PUT	/moderation/flags/{flag_id}/review	Review: dismiss/hide/delete/warn
GET	/moderation/stats?org_id={id}	Moderation stats
Frontend
FlagContentDialog.tsx — Radix Dialog for flagging (reuse ConfirmationDialog pattern)
ModerationQueueView.tsx — list of flagged items with action buttons
MentorPickButton.tsx — star/feature toggle for mentors
Phase 6: Search & Discovery
New files:

sensai-backend/src/api/db/search.py
sensai-backend/src/api/routes/search.py
SQLite FTS5 Virtual Tables
CREATE VIRTUAL TABLE posts_fts USING fts5(title, content, tokenize='porter unicode61');
CREATE VIRTUAL TABLE skills_fts USING fts5(name, description, tokenize='porter unicode61');
CREATE VIRTUAL TABLE hubs_fts USING fts5(name, description, tokenize='porter unicode61');
FTS tables populated at application level (extract plain text from blocks JSON using existing construct_description_from_blocks utility in db/utils.py) on post/skill/hub create/update.

API routes (/search)
Method	Path	Description
GET	/search/?q={query}&org_id={id}&type={post|hub|skill}	Full-text search
GET	/search/trending?org_id={id}	Trending posts (by recent vote/reply velocity)
GET	/search/recommended?user_id={id}&org_id={id}	Posts matching user's skills/hubs
Frontend
NetworkSearchBar.tsx — search input with type filter
SearchResultsList.tsx — mixed results (posts, hubs, skills)
TrendingFeed.tsx — trending content section
RecommendedPosts.tsx — personalized recommendations sidebar
Phase 7: Knowledge Persistence & Anti-Dead-Forum
Content Lifecycle States
Active — default, visible in feed
Stale — no activity for 4 weeks, shown with indicator, hidden from default feed
Archived — no activity for 6 months, moved to Archive tab, still searchable
Evergreen — manually marked by Tier 4+ user or mentor, never goes stale
Preventing the Dead Forum
AI-seeded discussions: When a hub is created and linked to a course, auto-generate 2-3 discussion prompts from course content via gpt-4.1-mini
Weekly digest: Monday notification compiling "This week's top discussions" per hub
Mentor nudges: If a hub has <2 posts in a week, mentor gets prompted
Course integration prompts: After completing a task (quiz score >80%, assignment done), show: "Share your approach in [Hub]?" with one-click post creation
Cross-cohort knowledge reuse: Top 10 Evergreen posts from previous cohort cloned as read-only references into new cohort hubs
Scheduled jobs (add to scheduler.py)
Daily: Content staleness check, reputation decay for old content
Daily: Vote ring detection (anti-gaming)
Weekly (Monday 8am): Hub digest notifications
Weekly: Mentor inactivity nudges
Nightly: Reputation reconciliation (recalculate from events to catch drift)
Phase 8: Knowledge Graph Navigation (Frontend)
User skill profile page (/school/[id]/network/profile/[userId])
SkillProfileView.tsx — skill radar/list with linked courses and proficiency levels
KnowledgeGraphView.tsx — interactive graph showing skill→hub→post→task connections
Implementation options for graph visualization
Option A: Lightweight react-force-graph-2d library (~200KB) — interactive node-link diagram
Option B: Custom SVG + framer-motion — no new dependency, more work
Recommendation: Option A for faster delivery, can replace later
API Layer (Frontend)
New file: src/lib/network-api.ts

Following the pattern in src/lib/api.ts — custom hooks using useAuth(), direct fetch() against backend.

Hooks
useHubs(schoolId), useHub(hubSlug), useHubPosts(hubId, filters)
usePost(postId), usePostReplies(postId)
useUserReputation(userId), useUserSkillProfile(userId)
useNetworkSearch(query, filters), useTrendingPosts(schoolId)
useModerationQueue(schoolId)
Mutations
createHub, createPost, updatePost, deletePost
voteOnPost, voteOnReply, createReply, bookmarkPost
flagContent, resolveFlag, featurePost, votePoll
State management
NetworkContext (src/context/NetworkContext.tsx) — active hub, user hub role, provided via layout
Optimistic updates for votes/bookmarks (local state → API → revert on error)
IndexedDB for post/reply drafts (extend existing pattern)
localStorage for feed sort preference, recent searches
Real-Time Updates Strategy
Phase 1 (MVP — polling)
Poll hub feed every 30s with "N new posts" banner
Poll post replies every 15s
Phase 2 (WebSocket)
Extend existing ConnectionManager in websockets.py with hub-scoped connections
Events: new_post, new_reply, vote_update, post_featured
useNetworkSocket(hubId) hook for live updates
New Pydantic Models (add to models.py)
Enums
HubVisibility, HubMemberRole, PostType, PostStatus, VoteValue, FlagReason, FlagStatus, ReputationLevel

Request models
CreateHubRequest, UpdateHubRequest, AddHubMembersRequest, CreatePostRequest, UpdatePostRequest, CreateReplyRequest, VoteRequest, BookmarkRequest, CreateSkillRequest, UpdateSkillRequest, LinkSkillsToTasksRequest, FlagContentRequest, ReviewFlagRequest, EndorseReplyRequest, SearchRequest, PollVoteRequest

Response models
HubSummary, PostSummary, PostDetail, Reply, UserReputation, UserSkillProfile, SearchResult, Skill

Migration Strategy
Add ~25 table name constants to config.py
Add create_*_table() functions to db/__init__.py in dependency order:
Phase 1: skills, task_skills, user_skills
Phase 2: hubs, hub_members, hub_skills, hub_courses
Phase 3: posts, replies, votes, bookmarks, poll_options, poll_votes, post_skills, post_tasks
Phase 4: reputation_events, user_reputation, endorsements, vote_audit, content_quality
Phase 5: flags
Phase 6: FTS5 virtual tables
Add migration function to migration.py using existing check_table_exists pattern
Register 6 new routers in main.py
Complete New Files Summary
Backend (12 new files)
File	Purpose
src/api/db/skill.py	Skill CRUD, linking, user profiles
src/api/db/hub.py	Hub CRUD, membership, linking
src/api/db/post.py	Post CRUD, replies, votes, bookmarks, polls
src/api/db/reputation.py	Reputation events, scoring, leaderboard
src/api/db/moderation.py	Flag CRUD, review queue
src/api/db/search.py	FTS5 queries, trending, recommendations
src/api/routes/skill.py	Skill API endpoints
src/api/routes/hub.py	Hub API endpoints
src/api/routes/post.py	Post API endpoints
src/api/routes/reputation.py	Reputation API endpoints
src/api/routes/moderation.py	Moderation API endpoints
src/api/routes/search.py	Search API endpoints
Frontend (~25 new files)
Category	Components
Types	types/network.ts
API	lib/network-api.ts
Context	context/NetworkContext.tsx
Hub	HubCard, HubListView, HubDetailView, HubSettingsView
Post	PostCard, PostDetailView, PostComposer, PostTypeBadge
Vote/Interact	VoteButtons, BookmarkButton, ShareButton
Reply	ReplyList, ReplyItem, ReplyComposer
Poll	PollOptionEditor, PollDisplay
Reputation	ReputationBadge, ReputationCard, ContributionHistory
Skill	SkillTag, SkillTagPicker, SkillProfileView, KnowledgeGraphView
Search	NetworkSearchBar, SearchResultsList, TrendingFeed, RecommendedPosts
Moderation	FlagContentDialog, ModerationQueueView, MentorPickButton
Pages	~12 new page.tsx files under network routes
Files to modify
File	Changes
sensai-backend/src/api/config.py	~25 new table name constants + reputation config
sensai-backend/src/api/db/__init__.py	~20 new create_*_table functions
sensai-backend/src/api/db/migration.py	Migration function for existing databases
sensai-backend/src/api/models.py	~30 new Pydantic models and enums
sensai-backend/src/api/main.py	6 new router registrations
sensai-backend/src/api/scheduler.py	5 new scheduled jobs
sensai-backend/src/api/routes/cohort.py	Extend leaderboard with reputation
sensai-frontend/src/types/index.ts	Re-export network types
sensai-frontend/src/components/TopPerformers.tsx	Add reputation display
sensai-frontend/src/components/header.tsx	Network navigation
sensai-frontend/src/app/school/[id]/ClientSchoolMemberView.tsx	Network entry point
Verification Plan
Backend testing
Run existing tests: pytest to ensure no regressions
Test table creation: Start app, verify all new tables created in SQLite
Test each API route group with curl/httpie:
Skills CRUD + linking to tasks
Hub CRUD + membership + feed
Post creation (all 4 types) + replies + voting + bookmarks
Poll creation and voting
Reputation: create posts/votes, verify points accumulate correctly
Search: create posts, verify FTS returns results
Moderation: flag content, review queue
Test anti-gaming: Verify rate limits, diminishing returns, vote ring detection
Test scheduled jobs: Run stale content check, digest generation
Frontend testing
Navigate to /school/[id]/network — hub listing renders
Create a hub, verify it appears in listing
Navigate into hub, create each post type (thread, Q&A, note, poll)
Test voting (optimistic update, revert on error)
Test reply creation and nesting
Test Q&A accept answer flow
Test search across hubs/posts/skills
Test reputation badge display next to usernames
Test moderation: flag content, review as admin
Test mobile responsiveness of all new views
Integration testing
End-to-end: Create skill → Create hub linked to skill → Create post tagged with skill → Vote on post → Verify reputation increases → Search finds the post
Cross-cohort: Mark post as Evergreen → Create new cohort → Verify reference appears
Knowledge graph: Create post linked to task → Navigate skill graph → Verify connections