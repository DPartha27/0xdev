"use client";

import { useAuth } from "./auth";
import { useCallback, useEffect, useState } from "react";
import type {
  Hub,
  PostSummary,
  PostDetail,
  Skill,
  UserReputation,
  UserSkillEntry,
  SkillGraphData,
  SearchResult,
  Flag,
  ReputationEvent,
} from "@/types/network";

const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "";

// ── Generic fetch helper ───────────────────────────────────────────────────────

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${backendUrl}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail?.detail ?? `Request failed: ${res.status}`);
  }
  return res.json();
}

// ── Skills ─────────────────────────────────────────────────────────────────────

export function useSkills(orgId: number | null) {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!orgId) return;
    setIsLoading(true);
    apiFetch<Skill[]>(`/skills/?org_id=${orgId}`)
      .then(setSkills)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [orgId]);

  return { skills, isLoading };
}

export async function createSkill(data: {
  org_id: number;
  name: string;
  slug: string;
  description?: string;
  parent_skill_id?: number;
}) {
  return apiFetch<{ id: number }>("/skills/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getSkillGraph(skillId: number): Promise<SkillGraphData> {
  return apiFetch<SkillGraphData>(`/skills/${skillId}/graph`);
}

export async function getUserSkillProfile(userId: number): Promise<UserSkillEntry[]> {
  return apiFetch<UserSkillEntry[]>(`/skills/user/${userId}`);
}

export async function linkSkillsToTask(taskId: number, skillIds: number[]) {
  return apiFetch("/skills/tasks/link", {
    method: "POST",
    body: JSON.stringify({ task_id: taskId, skill_ids: skillIds }),
  });
}

// ── Hubs ───────────────────────────────────────────────────────────────────────

export function useHubs(orgId: number | null) {
  const [hubs, setHubs] = useState<Hub[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const refetch = useCallback(() => {
    if (!orgId) return;
    setIsLoading(true);
    apiFetch<Hub[]>(`/hubs/?org_id=${orgId}`)
      .then(setHubs)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [orgId]);

  useEffect(() => { refetch(); }, [refetch]);

  return { hubs, isLoading, refetch };
}

export function useHub(hubId: number | null) {
  const [hub, setHub] = useState<Hub | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!hubId) return;
    setIsLoading(true);
    apiFetch<Hub>(`/hubs/${hubId}`)
      .then(setHub)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [hubId]);

  return { hub, isLoading };
}

export async function createHub(data: {
  org_id: number;
  name: string;
  slug: string;
  created_by: number;
  description?: string;
  icon?: string;
  visibility?: string;
  skill_ids?: number[];
  course_ids?: number[];
}) {
  return apiFetch<{ id: number }>("/hubs/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateHub(
  hubId: number,
  data: { name?: string; description?: string; icon?: string; visibility?: string }
) {
  return apiFetch(`/hubs/${hubId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteHub(hubId: number) {
  return apiFetch(`/hubs/${hubId}`, { method: "DELETE" });
}

// ── Hub Feed ───────────────────────────────────────────────────────────────────

export function useHubPosts(
  hubId: number | null,
  sort: "newest" | "popular" | "unanswered" = "newest",
  postType?: string
) {
  const [posts, setPosts] = useState<PostSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const refetch = useCallback(() => {
    if (!hubId) return;
    setIsLoading(true);
    const params = new URLSearchParams({ sort });
    if (postType) params.set("post_type", postType);
    apiFetch<PostSummary[]>(`/hubs/${hubId}/feed?${params}`)
      .then(setPosts)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [hubId, sort, postType]);

  useEffect(() => { refetch(); }, [refetch]);

  return { posts, isLoading, refetch };
}

// ── Posts ──────────────────────────────────────────────────────────────────────

export function usePost(postId: number | null, userId?: number) {
  const [post, setPost] = useState<PostDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const refetch = useCallback(() => {
    if (!postId) return;
    setIsLoading(true);
    const params = userId ? `?user_id=${userId}` : "";
    apiFetch<PostDetail>(`/posts/${postId}${params}`)
      .then(setPost)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [postId, userId]);

  useEffect(() => { refetch(); }, [refetch]);

  return { post, isLoading, refetch };
}

export interface TaskSearchResult {
  id: number;
  title: string;
  type: string;
}

export async function searchTasks(q: string, orgId: number): Promise<TaskSearchResult[]> {
  if (!q.trim()) return [];
  return apiFetch<TaskSearchResult[]>(
    `/posts/tasks/search?q=${encodeURIComponent(q)}&org_id=${orgId}`
  );
}

export async function createPost(data: {
  hub_id: number;
  author_id: number;
  post_type: string;
  title: string;
  blocks?: any[];
  skill_ids?: number[];
  task_ids?: number[];
  poll_options?: string[];
  status?: string;
}) {
  return apiFetch<{ id: number }>("/posts/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updatePost(
  postId: number,
  data: { title?: string; blocks?: any[]; status?: string }
) {
  return apiFetch(`/posts/${postId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deletePost(postId: number) {
  return apiFetch(`/posts/${postId}`, { method: "DELETE" });
}

// ── Replies ────────────────────────────────────────────────────────────────────

export async function createReply(
  postId: number,
  data: { author_id: number; blocks: any[]; parent_reply_id?: number }
) {
  return apiFetch<{ id: number }>(`/posts/${postId}/replies`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deleteReply(postId: number, replyId: number) {
  return apiFetch(`/posts/${postId}/replies/${replyId}`, { method: "DELETE" });
}

export async function acceptReply(postId: number, replyId: number, authorId: number) {
  return apiFetch(`/posts/${postId}/replies/${replyId}/accept?author_id=${authorId}`, {
    method: "POST",
  });
}

// ── Votes ──────────────────────────────────────────────────────────────────────

export async function voteOnPost(
  postId: number,
  userId: number,
  value: 1 | -1,
  viewDurationMs?: number
) {
  return apiFetch(`/posts/${postId}/vote`, {
    method: "POST",
    body: JSON.stringify({
      user_id: userId,
      value,
      view_duration_ms: viewDurationMs,
    }),
  });
}

export async function voteOnReply(
  postId: number,
  replyId: number,
  userId: number,
  value: 1 | -1
) {
  return apiFetch(`/posts/${postId}/replies/${replyId}/vote`, {
    method: "POST",
    body: JSON.stringify({ user_id: userId, value }),
  });
}

// ── Bookmarks ─────────────────────────────────────────────────────────────────

export async function bookmarkPost(postId: number, userId: number) {
  return apiFetch<{ action: "added" | "removed" }>(`/posts/${postId}/bookmark`, {
    method: "POST",
    body: JSON.stringify({ user_id: userId }),
  });
}

export function useUserBookmarks(userId: number | null) {
  const [posts, setPosts] = useState<PostSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!userId) return;
    setIsLoading(true);
    apiFetch<PostSummary[]>(`/users/${userId}/bookmarks`)
      .then(setPosts)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [userId]);

  return { posts, isLoading };
}

// ── Polls ──────────────────────────────────────────────────────────────────────

export async function votePoll(postId: number, userId: number, optionId: number) {
  return apiFetch(`/posts/${postId}/poll/vote`, {
    method: "POST",
    body: JSON.stringify({ user_id: userId, option_id: optionId }),
  });
}

// ── Endorsements ───────────────────────────────────────────────────────────────

export async function endorseReply(
  postId: number,
  replyId: number,
  endorserId: number,
  skillId?: number
) {
  return apiFetch(`/posts/${postId}/replies/${replyId}/endorse`, {
    method: "POST",
    body: JSON.stringify({ endorser_id: endorserId, skill_id: skillId }),
  });
}

// ── Reputation ─────────────────────────────────────────────────────────────────

export function useUserReputation(userId: number | null, orgId: number | null) {
  const [reputation, setReputation] = useState<UserReputation | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!userId || !orgId) return;
    setIsLoading(true);
    apiFetch<UserReputation>(`/reputation/user/${userId}?org_id=${orgId}`)
      .then(setReputation)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [userId, orgId]);

  return { reputation, isLoading };
}

export function useReputationLeaderboard(orgId: number | null) {
  const [leaderboard, setLeaderboard] = useState<UserReputation[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!orgId) return;
    setIsLoading(true);
    apiFetch<UserReputation[]>(`/reputation/leaderboard?org_id=${orgId}`)
      .then(setLeaderboard)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [orgId]);

  return { leaderboard, isLoading };
}

export function useReputationHistory(userId: number | null, orgId: number | null) {
  const [history, setHistory] = useState<ReputationEvent[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!userId || !orgId) return;
    setIsLoading(true);
    apiFetch<ReputationEvent[]>(`/reputation/user/${userId}/history?org_id=${orgId}`)
      .then(setHistory)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [userId, orgId]);

  return { history, isLoading };
}

// ── Moderation ─────────────────────────────────────────────────────────────────

export async function flagContent(
  targetType: "post" | "reply",
  targetId: number,
  postId: number,
  reporterId: number,
  reason: string,
  description?: string
) {
  if (targetType === "post") {
    return apiFetch(`/posts/${targetId}/flag`, {
      method: "POST",
      body: JSON.stringify({ reporter_id: reporterId, reason, description }),
    });
  }
  return apiFetch(`/posts/${postId}/replies/${targetId}/flag`, {
    method: "POST",
    body: JSON.stringify({ reporter_id: reporterId, reason, description }),
  });
}

export function useModerationQueue(orgId: number | null) {
  const [flags, setFlags] = useState<Flag[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const refetch = useCallback(() => {
    if (!orgId) return;
    setIsLoading(true);
    apiFetch<Flag[]>(`/moderation/queue?org_id=${orgId}`)
      .then(setFlags)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [orgId]);

  useEffect(() => { refetch(); }, [refetch]);

  return { flags, isLoading, refetch };
}

export async function resolveFlag(
  flagId: number,
  reviewedBy: number,
  actionTaken: string
) {
  return apiFetch(`/moderation/flags/${flagId}/review`, {
    method: "PUT",
    body: JSON.stringify({ reviewed_by: reviewedBy, action_taken: actionTaken }),
  });
}

export async function featurePost(postId: number, isEvergreen: boolean) {
  return apiFetch(`/posts/${postId}`, {
    method: "PUT",
    body: JSON.stringify({
      lifecycle_status: isEvergreen ? "evergreen" : "active",
    }),
  });
}

// ── Search ─────────────────────────────────────────────────────────────────────

export function useNetworkSearch(
  query: string,
  orgId: number | null,
  type?: string
) {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!query || !orgId) {
      setResults([]);
      return;
    }
    const timeout = setTimeout(() => {
      setIsLoading(true);
      const params = new URLSearchParams({ q: query, org_id: String(orgId) });
      if (type) params.set("type", type);
      apiFetch<SearchResult[]>(`/search/?${params}`)
        .then(setResults)
        .catch(console.error)
        .finally(() => setIsLoading(false));
    }, 300); // debounce 300ms
    return () => clearTimeout(timeout);
  }, [query, orgId, type]);

  return { results, isLoading };
}

export function useTrendingPosts(orgId: number | null) {
  const [posts, setPosts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!orgId) return;
    setIsLoading(true);
    apiFetch<any[]>(`/search/trending?org_id=${orgId}`)
      .then(setPosts)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [orgId]);

  return { posts, isLoading };
}

export function useRecommendedPosts(userId: number | null, orgId: number | null) {
  const [posts, setPosts] = useState<any[]>([]);

  useEffect(() => {
    if (!userId || !orgId) return;
    apiFetch<any[]>(`/search/recommended?user_id=${userId}&org_id=${orgId}`)
      .then(setPosts)
      .catch(console.error);
  }, [userId, orgId]);

  return { posts };
}
