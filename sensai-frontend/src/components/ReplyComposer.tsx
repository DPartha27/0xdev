"use client";

import React, { useState } from "react";
import { createReply } from "@/lib/network-api";

interface ReplyComposerProps {
  postId: number;
  authorId: number;
  parentReplyId?: number;
  placeholder?: string;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export default function ReplyComposer({
  postId,
  authorId,
  parentReplyId,
  placeholder = "Write a reply…",
  onSuccess,
  onCancel,
}: ReplyComposerProps) {
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      const blocks = [
        { type: "paragraph", content: [{ type: "text", text: text.trim() }] },
      ];
      await createReply(postId, {
        author_id: authorId,
        blocks,
        parent_reply_id: parentReplyId,
      });
      setText("");
      onSuccess?.();
    } catch (err: any) {
      setError(err.message ?? "Failed to post reply.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={placeholder}
        rows={3}
        className="w-full px-3 py-2 text-sm rounded-lg border bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-700 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
      />
      {error && <p className="text-xs text-red-500">{error}</p>}
      <div className="flex justify-end gap-2">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-3 py-1.5 text-sm rounded-lg text-neutral-600 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={submitting || !text.trim()}
          className="px-4 py-1.5 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {submitting ? "Posting…" : "Reply"}
        </button>
      </div>
    </form>
  );
}
