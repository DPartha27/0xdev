"use client";

import React, { useState } from "react";
import { ChevronUp, ChevronDown } from "lucide-react";

interface VoteButtonsProps {
  upvoteCount: number;
  downvoteCount: number;
  userVote?: number | null;  // +1, -1, or null
  onVote: (value: 1 | -1) => Promise<void>;
  disabled?: boolean;
  orientation?: "vertical" | "horizontal";
}

export default function VoteButtons({
  upvoteCount,
  downvoteCount,
  userVote,
  onVote,
  disabled = false,
  orientation = "vertical",
}: VoteButtonsProps) {
  const [localUpvotes, setLocalUpvotes] = useState(upvoteCount);
  const [localDownvotes, setLocalDownvotes] = useState(downvoteCount);
  const [localVote, setLocalVote] = useState(userVote ?? null);
  const [pending, setPending] = useState(false);

  async function handleVote(value: 1 | -1) {
    if (pending || disabled) return;

    // Optimistic update
    const prevVote = localVote;
    const prevUp = localUpvotes;
    const prevDown = localDownvotes;

    setLocalVote(localVote === value ? null : value);
    if (value === 1) {
      setLocalUpvotes((n) => (localVote === 1 ? n - 1 : n + 1));
      if (localVote === -1) setLocalDownvotes((n) => n - 1);
    } else {
      setLocalDownvotes((n) => (localVote === -1 ? n - 1 : n + 1));
      if (localVote === 1) setLocalUpvotes((n) => n - 1);
    }

    setPending(true);
    try {
      await onVote(value);
    } catch {
      // Revert on error
      setLocalVote(prevVote);
      setLocalUpvotes(prevUp);
      setLocalDownvotes(prevDown);
    } finally {
      setPending(false);
    }
  }

  const score = localUpvotes - localDownvotes;
  const isVertical = orientation === "vertical";

  return (
    <div
      className={`flex ${isVertical ? "flex-col items-center" : "flex-row items-center gap-2"} gap-1 select-none`}
    >
      <button
        type="button"
        onClick={() => handleVote(1)}
        disabled={disabled || pending}
        className={`p-1 rounded transition-colors ${
          localVote === 1
            ? "text-blue-600 bg-blue-50"
            : "text-neutral-400 hover:text-blue-600 hover:bg-blue-50"
        } disabled:opacity-40`}
        aria-label="Upvote"
      >
        <ChevronUp className="w-5 h-5" />
      </button>

      <span
        className={`text-sm font-semibold tabular-nums ${
          score > 0 ? "text-blue-600" : score < 0 ? "text-red-500" : "text-neutral-500"
        }`}
      >
        {score}
      </span>

      <button
        type="button"
        onClick={() => handleVote(-1)}
        disabled={disabled || pending}
        className={`p-1 rounded transition-colors ${
          localVote === -1
            ? "text-red-500 bg-red-50"
            : "text-neutral-400 hover:text-red-500 hover:bg-red-50"
        } disabled:opacity-40`}
        aria-label="Downvote"
      >
        <ChevronDown className="w-5 h-5" />
      </button>
    </div>
  );
}
