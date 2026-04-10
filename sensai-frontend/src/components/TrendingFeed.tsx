import React from "react";
import Link from "next/link";
import type { PostSummary } from "@/types/network";
import { TrendingUp, MessageSquare } from "lucide-react";
import { useTrendingPosts } from "@/lib/network-api";

interface TrendingFeedProps {
  orgId: number;
  schoolId: string;
  limit?: number;
}

function timeAgo(dateStr?: string) {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const hours = Math.floor(diff / 3600000);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function TrendingFeed({
  orgId,
  schoolId,
  limit = 5,
}: TrendingFeedProps) {
  const { posts, isLoading } = useTrendingPosts(orgId);
  const displayPosts = posts.slice(0, limit);

  return (
    <div className="rounded-xl border bg-white dark:bg-neutral-900 p-4">
      <div className="flex items-center gap-2 mb-3">
        <TrendingUp className="w-4 h-4 text-orange-500" />
        <h2 className="font-semibold text-sm text-neutral-900 dark:text-neutral-100">
          Trending
        </h2>
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: limit }).map((_, i) => (
            <div
              key={i}
              className="h-10 rounded bg-neutral-100 dark:bg-neutral-800 animate-pulse"
            />
          ))}
        </div>
      ) : displayPosts.length === 0 ? (
        <p className="text-xs text-neutral-500">No trending posts yet.</p>
      ) : (
        <div className="space-y-1">
          {displayPosts.map((post, idx) => (
            <Link
              key={post.id}
              href={`/school/${schoolId}/network/post/${post.id}`}
              className="flex items-start gap-2.5 p-2 rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors group"
            >
              <span className="text-xs font-bold text-neutral-300 dark:text-neutral-600 w-4 shrink-0 mt-0.5">
                {idx + 1}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-neutral-700 dark:text-neutral-300 line-clamp-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                  {post.title}
                </p>
                <div className="flex items-center gap-2 mt-0.5 text-xs text-neutral-400">
                  <span>{post.upvote_count - post.downvote_count} pts</span>
                  <span className="flex items-center gap-0.5">
                    <MessageSquare className="w-3 h-3" />
                    {post.reply_count}
                  </span>
                  <span>{timeAgo(post.created_at)}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
