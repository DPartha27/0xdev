"use client";

import React, { useState } from "react";
import { Plus, Settings } from "lucide-react";
import type { Hub, PostSummary, PostType, Skill } from "@/types/network";
import PostCard from "./PostCard";
import PostComposer from "./PostComposer";
import SkillTag from "./SkillTag";
import { useHubPosts } from "@/lib/network-api";

interface HubDetailViewProps {
  hub: Hub;
  schoolId: string;
  currentUserId: number;
  canManage?: boolean;
  availableSkills: Skill[];
}

type SortMode = "newest" | "popular" | "unanswered";
type FilterType = PostType | "all";

const SORT_LABELS: Record<SortMode, string> = {
  newest: "Newest",
  popular: "Popular",
  unanswered: "Unanswered",
};

const TYPE_LABELS: Record<FilterType, string> = {
  all: "All",
  thread: "Threads",
  question: "Q&A",
  note: "Notes",
  poll: "Polls",
};

export default function HubDetailView({
  hub,
  schoolId,
  currentUserId,
  canManage,
  availableSkills,
}: HubDetailViewProps) {
  const [sort, setSort] = useState<SortMode>("newest");
  const [typeFilter, setTypeFilter] = useState<FilterType>("all");
  const [showComposer, setShowComposer] = useState(false);

  const { posts, isLoading, refetch } = useHubPosts(
    hub.id,
    sort,
    typeFilter !== "all" ? typeFilter : undefined
  );

  function handlePostSuccess(postId: number) {
    setShowComposer(false);
    refetch();
  }

  return (
    <div className="space-y-5">
      {/* Hub header */}
      <div className="rounded-xl border bg-white dark:bg-neutral-900 p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            {hub.icon && (
              <span className="text-3xl leading-none">{hub.icon}</span>
            )}
            <div>
              <h1 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
                {hub.name}
              </h1>
              {hub.description && (
                <p className="text-sm text-neutral-500 mt-0.5">
                  {hub.description}
                </p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={() => setShowComposer(!showComposer)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Post
            </button>
            {canManage && (
              <a
                href={`/school/${schoolId}/network/${hub.slug}/settings`}
                className="p-2 rounded-lg text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
                title="Hub settings"
              >
                <Settings className="w-4 h-4" />
              </a>
            )}
          </div>
        </div>

        {hub.skills.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-neutral-100 dark:border-neutral-800">
            {hub.skills.map((s) => (
              <SkillTag key={s.id} skill={s} />
            ))}
          </div>
        )}

        <div className="flex gap-4 mt-3 pt-3 border-t border-neutral-100 dark:border-neutral-800 text-xs text-neutral-500">
          <span>{hub.member_count} members</span>
          <span>{hub.post_count} posts</span>
        </div>
      </div>

      {/* Post composer */}
      {showComposer && (
        <PostComposer
          hubId={hub.id}
          orgId={hub.org_id}
          authorId={currentUserId}
          availableSkills={availableSkills}
          onSuccess={handlePostSuccess}
          onCancel={() => setShowComposer(false)}
        />
      )}

      {/* Filter bar */}
      <div className="flex flex-col sm:flex-row gap-2 sm:items-center">
        {/* Sort tabs */}
        <div className="flex gap-1">
          {(Object.keys(SORT_LABELS) as SortMode[]).map((s) => (
            <button
              key={s}
              onClick={() => setSort(s)}
              className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                sort === s
                  ? "bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 font-medium"
                  : "text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800"
              }`}
            >
              {SORT_LABELS[s]}
            </button>
          ))}
        </div>

        {/* Type filter */}
        <div className="flex gap-1 sm:ml-auto">
          {(Object.keys(TYPE_LABELS) as FilterType[]).map((t) => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                typeFilter === t
                  ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 font-medium"
                  : "text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800"
              }`}
            >
              {TYPE_LABELS[t]}
            </button>
          ))}
        </div>
      </div>

      {/* Post feed */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="rounded-xl border bg-neutral-100 dark:bg-neutral-800 animate-pulse h-24"
            />
          ))}
        </div>
      ) : posts.length === 0 ? (
        <div className="py-16 text-center text-neutral-500">
          <p>No posts yet.</p>
          <button
            type="button"
            onClick={() => setShowComposer(true)}
            className="mt-2 text-blue-600 hover:underline text-sm"
          >
            Be the first to post!
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {posts.map((post) => (
            <PostCard
              key={post.id}
              post={post}
              schoolId={schoolId}
              hubSlug={hub.slug}
            />
          ))}
        </div>
      )}
    </div>
  );
}
