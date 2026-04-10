import React from "react";
import type { UserReputation, ReputationLevel } from "@/types/network";
import {
  REPUTATION_LEVEL_LABELS,
  REPUTATION_LEVEL_THRESHOLDS,
} from "@/types/network";
import ReputationBadge from "./ReputationBadge";

interface ReputationCardProps {
  reputation: UserReputation;
  userName?: string;
}

const LEVELS: ReputationLevel[] = [
  "newcomer",
  "contributor",
  "active_learner",
  "trusted_member",
  "subject_expert",
  "community_leader",
];

function getNextLevel(current: ReputationLevel): ReputationLevel | null {
  const idx = LEVELS.indexOf(current);
  return idx < LEVELS.length - 1 ? LEVELS[idx + 1] : null;
}

export default function ReputationCard({
  reputation,
  userName,
}: ReputationCardProps) {
  const next = getNextLevel(reputation.level);
  const nextThreshold = next ? REPUTATION_LEVEL_THRESHOLDS[next] : null;
  const currentThreshold = REPUTATION_LEVEL_THRESHOLDS[reputation.level];
  const progress = nextThreshold
    ? Math.min(
        100,
        ((reputation.total_points - currentThreshold) /
          (nextThreshold - currentThreshold)) *
          100
      )
    : 100;

  return (
    <div className="rounded-xl border bg-white dark:bg-neutral-900 p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          {userName && (
            <p className="font-semibold text-neutral-900 dark:text-neutral-100">
              {userName}
            </p>
          )}
          <p className="text-2xl font-bold text-neutral-900 dark:text-neutral-100 tabular-nums">
            {reputation.total_points.toLocaleString()}
            <span className="text-sm font-normal text-neutral-500 ml-1">
              pts
            </span>
          </p>
        </div>
        <ReputationBadge level={reputation.level} size="md" />
      </div>

      {/* Progress to next level */}
      {next && nextThreshold && (
        <div>
          <div className="flex justify-between text-xs text-neutral-500 mb-1">
            <span>{REPUTATION_LEVEL_LABELS[reputation.level]}</span>
            <span>
              {reputation.total_points}/{nextThreshold} →{" "}
              {REPUTATION_LEVEL_LABELS[next]}
            </span>
          </div>
          <div className="h-2 bg-neutral-100 dark:bg-neutral-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Level ladder */}
      <div className="space-y-1">
        {LEVELS.map((l) => {
          const isReached = REPUTATION_LEVEL_THRESHOLDS[l] <= reputation.total_points;
          const isCurrent = l === reputation.level;
          return (
            <div
              key={l}
              className={`flex items-center justify-between text-xs py-0.5 ${
                isCurrent
                  ? "font-semibold text-blue-600 dark:text-blue-400"
                  : isReached
                  ? "text-neutral-600 dark:text-neutral-400"
                  : "text-neutral-400 dark:text-neutral-600"
              }`}
            >
              <span>{REPUTATION_LEVEL_LABELS[l]}</span>
              <span className="tabular-nums">
                {REPUTATION_LEVEL_THRESHOLDS[l].toLocaleString()} pts
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
