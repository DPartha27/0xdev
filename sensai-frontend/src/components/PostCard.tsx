import React from "react";
import Link from "next/link";
import { MessageSquare, Eye, CheckCircle } from "lucide-react";
import type { PostSummary } from "@/types/network";
import PostTypeBadge from "./PostTypeBadge";
import SkillTag from "./SkillTag";

interface PostCardProps {
  post: PostSummary;
  schoolId: string;
  hubSlug: string;
}

function timeAgo(dateStr?: string) {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

export default function PostCard({ post, schoolId, hubSlug }: PostCardProps) {
  const score = post.upvote_count - post.downvote_count;

  return (
    <Link
      href={`/school/${schoolId}/network/${hubSlug}/posts/${post.id}`}
      className="block rounded-xl border bg-white dark:bg-neutral-900 hover:shadow-md transition-shadow p-4"
    >
      <div className="flex gap-3">
        {/* Vote score column */}
        <div className="flex flex-col items-center justify-start gap-0.5 shrink-0 pt-0.5">
          <span
            className={`text-sm font-bold tabular-nums ${
              score > 0
                ? "text-blue-600"
                : score < 0
                ? "text-red-500"
                : "text-neutral-400"
            }`}
          >
            {score}
          </span>
          <span className="text-xs text-neutral-400">votes</span>
        </div>

        {/* Main content */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1.5">
            <PostTypeBadge type={post.post_type} />
            {post.is_pinned && (
              <span className="text-xs bg-yellow-100 text-yellow-700 rounded-full px-2 py-0.5 font-medium">
                Pinned
              </span>
            )}
            {post.lifecycle_status === "stale" && (
              <span className="text-xs bg-neutral-100 text-neutral-500 rounded-full px-2 py-0.5">
                Stale
              </span>
            )}
            {post.lifecycle_status === "evergreen" && (
              <span className="text-xs bg-green-100 text-green-700 rounded-full px-2 py-0.5">
                Evergreen
              </span>
            )}
          </div>

          <h3 className="font-medium text-neutral-900 dark:text-neutral-100 text-sm leading-snug mb-1.5 line-clamp-2">
            {post.title}
          </h3>

          {post.skills && post.skills.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-2">
              {post.skills.slice(0, 3).map((s) => (
                <SkillTag key={s.id} skill={s} />
              ))}
              {post.skills.length > 3 && (
                <span className="text-xs text-neutral-400">
                  +{post.skills.length - 3}
                </span>
              )}
            </div>
          )}

          <div className="flex flex-wrap items-center gap-3 text-xs text-neutral-500">
            <span>{post.author_name}</span>
            <span>{timeAgo(post.created_at)}</span>
            <span className="flex items-center gap-0.5">
              <MessageSquare className="w-3.5 h-3.5" />
              {post.reply_count}
            </span>
            <span className="flex items-center gap-0.5">
              <Eye className="w-3.5 h-3.5" />
              {post.view_count}
            </span>
            {post.has_accepted_answer && (
              <CheckCircle className="w-3.5 h-3.5 text-green-500" />
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}
