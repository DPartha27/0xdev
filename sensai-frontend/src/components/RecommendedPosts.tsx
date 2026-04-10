import React from "react";
import Link from "next/link";
import { Sparkles } from "lucide-react";
import { useRecommendedPosts } from "@/lib/network-api";
import PostTypeBadge from "./PostTypeBadge";

interface RecommendedPostsProps {
  userId: number;
  orgId: number;
  schoolId: string;
  limit?: number;
}

export default function RecommendedPosts({
  userId,
  orgId,
  schoolId,
  limit = 5,
}: RecommendedPostsProps) {
  const { posts } = useRecommendedPosts(userId, orgId);
  const displayPosts = posts.slice(0, limit);

  return (
    <div className="rounded-xl border bg-white dark:bg-neutral-900 p-4">
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="w-4 h-4 text-purple-500" />
        <h2 className="font-semibold text-sm text-neutral-900 dark:text-neutral-100">
          Recommended for you
        </h2>
      </div>

      {displayPosts.length === 0 ? (
        <p className="text-xs text-neutral-500">
          Join hubs and tag skills to get personalized recommendations.
        </p>
      ) : (
        <div className="space-y-1">
          {displayPosts.map((post) => (
            <Link
              key={post.id}
              href={`/school/${schoolId}/network/post/${post.id}`}
              className="flex items-start gap-2.5 p-2 rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors group"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <PostTypeBadge type={post.post_type} size="sm" />
                </div>
                <p className="text-xs font-medium text-neutral-700 dark:text-neutral-300 line-clamp-2 group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors">
                  {post.title}
                </p>
                <p className="text-xs text-neutral-400 mt-0.5">
                  by {post.author_name}
                </p>
              </div>
              <span className="text-xs text-neutral-400 shrink-0 tabular-nums">
                {post.upvote_count - post.downvote_count} pts
              </span>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
