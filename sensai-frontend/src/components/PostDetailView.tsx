"use client";

import React, { useRef, useState } from "react";
import Link from "next/link";
import { ChevronLeft, Flag } from "lucide-react";
import type { PostDetail } from "@/types/network";
import PostTypeBadge from "./PostTypeBadge";
import SkillTag from "./SkillTag";
import VoteButtons from "./VoteButtons";
import BookmarkButton from "./BookmarkButton";
import ShareButton from "./ShareButton";
import ReplyList from "./ReplyList";
import ReplyComposer from "./ReplyComposer";
import PollDisplay from "./PollDisplay";
import { voteOnPost, acceptReply, flagContent } from "@/lib/network-api";

interface PostDetailViewProps {
  post: PostDetail;
  schoolId: string;
  hubSlug: string;
  currentUserId: number;
  onRefresh?: () => void;
}

function extractText(blocks?: any[]): string {
  if (!blocks) return "";
  return blocks
    .map((b: any) =>
      Array.isArray(b.content)
        ? b.content.map((c: any) => c.text ?? "").join("")
        : ""
    )
    .join("\n\n");
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

export default function PostDetailView({
  post,
  schoolId,
  hubSlug,
  currentUserId,
  onRefresh,
}: PostDetailViewProps) {
  const viewStartRef = useRef(Date.now());
  const [showFlagReason, setShowFlagReason] = useState(false);
  const [flagging, setFlagging] = useState(false);

  async function handlePostVote(value: 1 | -1) {
    const viewDuration = Date.now() - viewStartRef.current;
    await voteOnPost(post.id, currentUserId, value, viewDuration);
  }

  async function handleAcceptReply(replyId: number) {
    await acceptReply(post.id, replyId, currentUserId);
    onRefresh?.();
  }

  async function handleFlag(reason: string) {
    setFlagging(true);
    try {
      await flagContent("post", post.id, post.id, currentUserId, reason);
      setShowFlagReason(false);
    } finally {
      setFlagging(false);
    }
  }

  const bodyText = extractText(post.blocks);

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Breadcrumb */}
      <Link
        href={`/school/${schoolId}/network/${hubSlug}`}
        className="inline-flex items-center gap-1 text-sm text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200 transition-colors"
      >
        <ChevronLeft className="w-4 h-4" />
        Back to hub
      </Link>

      {/* Post */}
      <div className="rounded-xl border bg-white dark:bg-neutral-900 p-6">
        <div className="flex gap-4">
          {/* Vote column */}
          <div className="shrink-0">
            <VoteButtons
              upvoteCount={post.upvote_count}
              downvoteCount={post.downvote_count}
              userVote={post.user_vote}
              onVote={handlePostVote}
              orientation="vertical"
            />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <PostTypeBadge type={post.post_type} size="md" />
              {post.is_pinned && (
                <span className="text-xs bg-yellow-100 text-yellow-700 rounded-full px-2 py-0.5 font-medium">
                  Pinned
                </span>
              )}
              {post.lifecycle_status === "evergreen" && (
                <span className="text-xs bg-green-100 text-green-700 rounded-full px-2 py-0.5">
                  Evergreen
                </span>
              )}
            </div>

            <h1 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-2 leading-snug">
              {post.title}
            </h1>

            <div className="flex flex-wrap items-center gap-3 text-sm text-neutral-500 mb-4">
              <span className="font-medium text-neutral-700 dark:text-neutral-300">
                {post.author_name}
              </span>
              <span>{timeAgo(post.created_at)}</span>
              <span>{post.view_count} views</span>
            </div>

            {bodyText && (
              <div className="text-sm text-neutral-800 dark:text-neutral-200 whitespace-pre-wrap leading-relaxed mb-4">
                {bodyText}
              </div>
            )}

            {/* Poll */}
            {post.post_type === "poll" && post.poll_options && (
              <PollDisplay
                postId={post.id}
                userId={currentUserId}
                options={post.poll_options}
                userVotedOptionId={undefined}
                closed={post.status === "closed"}
                onVote={onRefresh}
              />
            )}

            {/* Skills */}
            {post.skills && post.skills.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-4">
                {post.skills.map((s) => (
                  <SkillTag key={s.id} skill={s} />
                ))}
              </div>
            )}

            {/* Linked tasks */}
            {post.linked_tasks && post.linked_tasks.length > 0 && (
              <div className="text-xs text-neutral-500 mb-4">
                <span className="font-medium">Linked tasks: </span>
                {post.linked_tasks.map((t, i) => (
                  <span key={t.id}>
                    {i > 0 && ", "}
                    <span className="text-neutral-700 dark:text-neutral-300">
                      {t.title}
                    </span>
                    <span className="text-neutral-400 ml-1">({t.relation_type})</span>
                  </span>
                ))}
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-wrap items-center gap-4 pt-2 border-t border-neutral-100 dark:border-neutral-800">
              <BookmarkButton
                postId={post.id}
                userId={currentUserId}
                isBookmarked={post.is_bookmarked}
              />
              <ShareButton
                url={typeof window !== "undefined" ? window.location.href : undefined}
              />
              <button
                type="button"
                onClick={() => setShowFlagReason(!showFlagReason)}
                className="flex items-center gap-1 text-xs text-neutral-400 hover:text-red-500 transition-colors"
              >
                <Flag className="w-3.5 h-3.5" />
                Flag
              </button>
            </div>

            {showFlagReason && (
              <div className="mt-3 flex flex-wrap gap-2">
                {(["spam", "offensive", "off_topic", "misinformation", "other"] as const).map(
                  (reason) => (
                    <button
                      key={reason}
                      type="button"
                      disabled={flagging}
                      onClick={() => handleFlag(reason)}
                      className="px-3 py-1 text-xs rounded-full border border-red-300 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-50 capitalize"
                    >
                      {reason.replace("_", " ")}
                    </button>
                  )
                )}
                <button
                  type="button"
                  onClick={() => setShowFlagReason(false)}
                  className="px-3 py-1 text-xs text-neutral-500 hover:text-neutral-700"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Replies */}
      <div className="rounded-xl border bg-white dark:bg-neutral-900 p-6 space-y-5">
        <h2 className="font-semibold text-neutral-900 dark:text-neutral-100">
          {post.reply_count} {post.reply_count === 1 ? "Reply" : "Replies"}
        </h2>

        <ReplyList
          replies={post.replies}
          postId={post.id}
          currentUserId={currentUserId}
          postAuthorId={post.author_id}
          isQuestionPost={post.post_type === "question"}
          onAccept={handleAcceptReply}
        />

        <div className="pt-2 border-t border-neutral-100 dark:border-neutral-800">
          <p className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-3">
            Add a reply
          </p>
          <ReplyComposer
            postId={post.id}
            authorId={currentUserId}
            onSuccess={onRefresh}
          />
        </div>
      </div>
    </div>
  );
}
