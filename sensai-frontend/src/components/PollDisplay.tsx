"use client";

import React, { useState } from "react";
import type { PollOption } from "@/types/network";
import { votePoll } from "@/lib/network-api";

interface PollDisplayProps {
  postId: number;
  userId: number;
  options: PollOption[];
  userVotedOptionId?: number | null;
  closed?: boolean;
  onVote?: (optionId: number) => void;
}

export default function PollDisplay({
  postId,
  userId,
  options,
  userVotedOptionId,
  closed,
  onVote,
}: PollDisplayProps) {
  const [localVote, setLocalVote] = useState<number | null>(
    userVotedOptionId ?? null
  );
  const [localCounts, setLocalCounts] = useState<Record<number, number>>(
    Object.fromEntries(options.map((o) => [o.id, o.vote_count]))
  );
  const [pending, setPending] = useState(false);

  const totalVotes = Object.values(localCounts).reduce((a, b) => a + b, 0);
  const hasVoted = localVote !== null;
  const showResults = hasVoted || closed;

  async function handleVote(optionId: number) {
    if (pending || hasVoted || closed) return;
    const prev = { ...localCounts };
    setLocalVote(optionId);
    setLocalCounts((c) => ({ ...c, [optionId]: (c[optionId] ?? 0) + 1 }));
    setPending(true);
    try {
      await votePoll(postId, userId, optionId);
      onVote?.(optionId);
    } catch {
      setLocalVote(null);
      setLocalCounts(prev);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="space-y-2 my-3">
      {options.map((opt) => {
        const count = localCounts[opt.id] ?? 0;
        const pct = totalVotes > 0 ? Math.round((count / totalVotes) * 100) : 0;
        const isVoted = localVote === opt.id;

        return (
          <button
            key={opt.id}
            type="button"
            disabled={showResults || pending}
            onClick={() => handleVote(opt.id)}
            className={`relative w-full text-left rounded-lg border overflow-hidden transition-colors ${
              showResults
                ? "cursor-default"
                : "hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/10"
            } ${
              isVoted
                ? "border-blue-500"
                : "border-neutral-200 dark:border-neutral-700"
            }`}
          >
            {showResults && (
              <div
                className={`absolute inset-y-0 left-0 transition-all duration-500 ${
                  isVoted ? "bg-blue-100 dark:bg-blue-900/30" : "bg-neutral-100 dark:bg-neutral-800"
                }`}
                style={{ width: `${pct}%` }}
              />
            )}
            <div className="relative flex items-center justify-between px-3 py-2 text-sm">
              <span
                className={`font-medium ${
                  isVoted ? "text-blue-700 dark:text-blue-400" : ""
                }`}
              >
                {opt.text}
              </span>
              {showResults && (
                <span className="text-xs text-neutral-500 tabular-nums">
                  {pct}%{" "}
                  <span className="text-neutral-400">({count})</span>
                </span>
              )}
            </div>
          </button>
        );
      })}

      <p className="text-xs text-neutral-400 mt-1">
        {totalVotes} vote{totalVotes !== 1 ? "s" : ""}
        {closed && " · Poll closed"}
        {!showResults && !closed && " · Click to vote"}
      </p>
    </div>
  );
}
