import React from "react";
import type { Reply } from "@/types/network";
import ReplyItem from "./ReplyItem";

interface ReplyListProps {
  replies: Reply[];
  postId: number;
  currentUserId: number;
  postAuthorId: number;
  isQuestionPost?: boolean;
  onAccept?: (replyId: number) => void;
}

export default function ReplyList({
  replies,
  postId,
  currentUserId,
  postAuthorId,
  isQuestionPost,
  onAccept,
}: ReplyListProps) {
  // Split top-level vs nested
  const topLevel = replies.filter((r) => !r.parent_reply_id);
  const byParent: Record<number, Reply[]> = {};
  for (const r of replies) {
    if (r.parent_reply_id) {
      if (!byParent[r.parent_reply_id]) byParent[r.parent_reply_id] = [];
      byParent[r.parent_reply_id].push(r);
    }
  }

  // Sort: accepted first, then by upvotes
  const sorted = [...topLevel].sort((a, b) => {
    if (a.is_accepted !== b.is_accepted) return a.is_accepted ? -1 : 1;
    return b.upvote_count - a.upvote_count;
  });

  if (sorted.length === 0) {
    return (
      <p className="text-sm text-neutral-500 text-center py-6">
        No replies yet. Be the first to reply!
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {sorted.map((reply) => (
        <div key={reply.id} className="space-y-3">
          <ReplyItem
            reply={reply}
            postId={postId}
            authorId={currentUserId}
            isPostAuthor={currentUserId === postAuthorId}
            isQuestionPost={isQuestionPost}
            onAccept={onAccept}
            depth={0}
          />
          {byParent[reply.id]?.map((nested) => (
            <ReplyItem
              key={nested.id}
              reply={nested}
              postId={postId}
              authorId={currentUserId}
              isPostAuthor={currentUserId === postAuthorId}
              isQuestionPost={isQuestionPost}
              onAccept={onAccept}
              depth={1}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
