// ── Reputation ─────────────────────────────────────────────────────────────────

export type ReputationLevel =
  | "newcomer"
  | "contributor"
  | "active_learner"
  | "trusted_member"
  | "subject_expert"
  | "community_leader";

export const REPUTATION_LEVEL_LABELS: Record<ReputationLevel, string> = {
  newcomer: "Newcomer",
  contributor: "Contributor",
  active_learner: "Active Learner",
  trusted_member: "Trusted Member",
  subject_expert: "Subject Expert",
  community_leader: "Community Leader",
};

export const REPUTATION_LEVEL_THRESHOLDS: Record<ReputationLevel, number> = {
  newcomer: 0,
  contributor: 50,
  active_learner: 100,
  trusted_member: 300,
  subject_expert: 750,
  community_leader: 1500,
};

// ── Skills ─────────────────────────────────────────────────────────────────────

export interface Skill {
  id: number;
  org_id: number;
  name: string;
  slug: string;
  description?: string;
  parent_skill_id?: number;
  created_at?: string;
  updated_at?: string;
}

export interface UserSkillEntry {
  skill_id: number;
  skill_name: string;
  slug: string;
  description?: string;
  parent_skill_id?: number;
  proficiency_level: number;
  evidence_count: number;
  updated_at?: string;
}

export interface SkillGraphData {
  tasks: { id: number; title: string; type: string }[];
  hubs: { id: number; name: string; slug: string; description?: string }[];
  posts: {
    id: number;
    title: string;
    post_type: string;
    upvote_count: number;
    reply_count: number;
  }[];
}

// ── Hubs ───────────────────────────────────────────────────────────────────────

export type HubVisibility = "public" | "private" | "archived";
export type HubMemberRole = "member" | "moderator" | "owner";

export interface Hub {
  id: number;
  org_id: number;
  name: string;
  slug: string;
  description?: string;
  icon?: string;
  visibility: HubVisibility;
  created_by: number;
  member_count: number;
  post_count: number;
  skills: Skill[];
  created_at?: string;
  updated_at?: string;
}

// ── Posts ──────────────────────────────────────────────────────────────────────

export type PostType = "thread" | "question" | "note" | "poll";
export type PostStatus = "draft" | "published" | "closed" | "archived";
export type PostLifecycleStatus = "active" | "stale" | "archived" | "evergreen";
export type PostRelationType = "related" | "explains" | "extends";

export interface PostAuthor {
  id: number;
  name: string;
  reputation?: number;
  level?: ReputationLevel;
}

export interface PollOption {
  id: number;
  post_id: number;
  text: string;
  position: number;
  vote_count: number;
}

export interface PostSummary {
  id: number;
  hub_id: number;
  author_id: number;
  author_name: string;
  post_type: PostType;
  title: string;
  status: PostStatus;
  lifecycle_status: PostLifecycleStatus;
  is_pinned: boolean;
  upvote_count: number;
  downvote_count: number;
  reply_count: number;
  view_count: number;
  has_accepted_answer: boolean;
  skills?: Skill[];
  created_at?: string;
  updated_at?: string;
}

export interface Reply {
  id: number;
  post_id: number;
  parent_reply_id?: number;
  author_id: number;
  author_name: string;
  blocks?: any[];
  upvote_count: number;
  downvote_count: number;
  is_accepted: boolean;
  endorsement_count: number;
  created_at?: string;
  updated_at?: string;
  // Client-side state
  user_vote?: number | null;
}

export interface PostDetail extends PostSummary {
  blocks?: any[];
  replies: Reply[];
  linked_tasks: { id: number; title: string; type: string; relation_type: string }[];
  is_bookmarked: boolean;
  user_vote?: number | null;
  poll_options?: PollOption[];
}

// ── Reputation ─────────────────────────────────────────────────────────────────

export interface UserReputation {
  user_id: number;
  org_id: number;
  total_points: number;
  level: ReputationLevel;
  updated_at?: string;
}

export interface ReputationEvent {
  id: number;
  event_type: string;
  points: number;
  source_type?: string;
  source_id?: number;
  created_at?: string;
}

// ── Moderation ─────────────────────────────────────────────────────────────────

export type FlagReason =
  | "spam"
  | "offensive"
  | "off_topic"
  | "misinformation"
  | "other";

export type FlagStatus = "pending" | "actioned" | "dismissed";

export interface Flag {
  id: number;
  reporter_id: number;
  target_type: "post" | "reply";
  target_id: number;
  reason: FlagReason;
  description?: string;
  status: FlagStatus;
  reviewed_by?: number;
  reviewed_at?: string;
  action_taken?: string;
  created_at?: string;
}

// ── Search ─────────────────────────────────────────────────────────────────────

export type SearchResultType = "post" | "hub" | "skill";

export interface SearchResult {
  type: SearchResultType;
  id: number;
  title: string;
  snippet: string;
  hub_name?: string;
  score: number;
}

// ── Network context ────────────────────────────────────────────────────────────

export interface NetworkContextValue {
  activeHub: Hub | null;
  setActiveHub: (hub: Hub | null) => void;
  userHubRole: HubMemberRole | null;
  orgId: number | null;
}
