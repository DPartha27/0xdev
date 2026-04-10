"use client";

import React, { useState } from "react";
import { CheckCircle, ChevronDown, ChevronUp, MessageSquare } from "lucide-react";
import type { Reply } from "@/types/network";
import VoteButtons from "./VoteButtons";
import ReplyComposer from "./ReplyComposer";
import { voteOnReply } from "@/lib/network-api";

interface ReplyItemProps {
  reply: Reply;
  postId: number;
  authorId: number;
  isPostAuthor?: boolean;
  isQuestionPost?: boolean;
  onAccept?: (replyId: number) => void;
  depth?: number;
}

function extractText(blocks?: any[]): string {
  if (!blocks) return "";
  return blocks
    .map((b: any) => {
      if (b.content) {
        return b.content.map((c: any) => c.text ?? "").join("");
      }
      return "";
    })
    .join("\n");
}

function timeAgo(dateStr?: string) {
  if (!dateStr) return "";
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function ReplyItem({
  reply,
  postId,
  authorId,
  isPostAuthor,
  isQuestionPost,
  onAccept,
  depth = 0,
}: ReplyItemProps) {
  const [showReplyComposer, setShowReplyComposer] = useState(false);
  const [localVote, setLocalVote] = useState(reply.user_vote ?? null);
  const [localUp, setLocalUp] = useState(reply.upvote_count);
  const [localDown, setLocalDown] = useState(reply.downvote_count);

  const text = extractText(reply.blocks);

  async function handleVote(value: 1 | -1) {
    await voteOnReply(postId, reply.id, authorId, value);
    setLocalVote((prev) => (prev === value ? null : value));
    if (value === 1) {
      setLocalUp((n) => (localVote === 1 ? n - 1 : n + 1));
      if (localVote === -1) setLocalDown((n) => n - 1);
    } else {
      setLocalDown((n) => (localVote === -1 ? n - 1 : n + 1));
      if (localVote === 1) setLocalUp((n) => n - 1);
    }
  }

  return (
    <div
      className={`flex gap-3 ${depth > 0 ? "ml-8 pl-4 border-l border-neutral-200 dark:border-neutral-700" : ""}`}
    >
      {/* Votes */}
      <div className="shrink-0 pt-1">
        <VoteButtons
          upvoteCount={localUp}
          downvoteCount={localDown}
          userVote={localVote}
          onVote={handleVote}
          orientation="vertical"
        />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-center gap-2 mb-1 text-xs text-neutral-500">
          <span className="font-medium text-neutral-700 dark:text-neutral-300">
            {reply.author_name}
          </span>
          <span>{timeAgo(reply.created_at)}</span>
          {reply.is_accepted && (
            <span className="flex items-center gap-0.5 text-green-600 font-medium">
              <CheckCircle className="w-3.5 h-3.5" />
              Accepted
            </span>
          )}
          {reply.endorsement_count > 0 && (
            <span className="text-purple-600 font-medium">
              ✦ {reply.endorsement_count} endorsement{reply.endorsement_count > 1 ? "s" : ""}
            </span>
          )}
        </div>

        <div className="text-sm text-neutral-800 dark:text-neutral-200 whitespace-pre-wrap leading-relaxed mb-2">
          {text}
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {depth === 0 && (
            <button
              type="button"
              onClick={() => setShowReplyComposer(!showReplyComposer)}
              className="flex items-center gap-1 text-xs text-neutral-500 hover:text-blue-600 transition-colors"
            >
              <MessageSquare className="w-3.5 h-3.5" />
              Reply
            </button>
          )}

          {isPostAuthor && isQuestionPost && !reply.is_accepted && (
            <button
              type="button"
              onClick={() => onAccept?.(reply.id)}
              className="flex items-center gap-1 text-xs text-green-600 hover:text-green-700 transition-colors font-medium"
            >
              <CheckCircle className="w-3.5 h-3.5" />
              Accept answer
            </button>
          )}
        </div>

        {showReplyComposer && (
          <div className="mt-3">
            <ReplyComposer
              postId={postId}
              authorId={authorId}
              parentReplyId={reply.id}
              placeholder="Reply to this answer…"
              onSuccess={() => setShowReplyComposer(false)}
              onCancel={() => setShowReplyComposer(false)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
