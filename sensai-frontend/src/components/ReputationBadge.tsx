import React from "react";
import type { ReputationLevel } from "@/types/network";
import { REPUTATION_LEVEL_LABELS } from "@/types/network";

interface ReputationBadgeProps {
  level: ReputationLevel;
  points?: number;
  size?: "xs" | "sm" | "md";
}

const LEVEL_COLORS: Record<ReputationLevel, string> = {
  newcomer: "bg-neutral-100 text-neutral-500 dark:bg-neutral-800 dark:text-neutral-400",
  contributor: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400",
  active_learner: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  trusted_member: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
  subject_expert: "bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
  community_leader: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-500",
};

const LEVEL_ICONS: Record<ReputationLevel, string> = {
  newcomer: "○",
  contributor: "◑",
  active_learner: "◕",
  trusted_member: "★",
  subject_expert: "✦",
  community_leader: "⬡",
};

export default function ReputationBadge({
  level,
  points,
  size = "sm",
}: ReputationBadgeProps) {
  const color = LEVEL_COLORS[level] ?? LEVEL_COLORS.newcomer;
  const icon = LEVEL_ICONS[level] ?? "○";
  const label = REPUTATION_LEVEL_LABELS[level] ?? "Newcomer";

  const sizeClass =
    size === "xs"
      ? "text-xs px-1.5 py-0.5 gap-1"
      : size === "md"
      ? "text-sm px-3 py-1 gap-1.5"
      : "text-xs px-2 py-0.5 gap-1";

  return (
    <span
      className={`inline-flex items-center rounded-full font-medium select-none ${color} ${sizeClass}`}
      title={label}
    >
      <span aria-hidden="true">{icon}</span>
      {size !== "xs" && <span>{label}</span>}
      {points !== undefined && (
        <span className="opacity-70 tabular-nums">{points.toLocaleString()}</span>
      )}
    </span>
  );
}
