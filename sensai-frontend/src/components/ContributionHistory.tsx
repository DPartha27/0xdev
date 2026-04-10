import React from "react";
import type { ReputationEvent } from "@/types/network";

interface ContributionHistoryProps {
  events: ReputationEvent[];
  isLoading?: boolean;
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
  return new Date(dateStr!).toLocaleDateString();
}

function formatEventType(type: string): string {
  return type
    .split("_")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export default function ContributionHistory({
  events,
  isLoading,
}: ContributionHistoryProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="h-10 rounded-lg bg-neutral-100 dark:bg-neutral-800 animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <p className="text-sm text-neutral-500 text-center py-6">
        No reputation events yet.
      </p>
    );
  }

  return (
    <div className="divide-y divide-neutral-100 dark:divide-neutral-800">
      {events.map((event) => (
        <div
          key={event.id}
          className="flex items-center justify-between py-2.5 text-sm"
        >
          <div>
            <p className="font-medium text-neutral-800 dark:text-neutral-200">
              {formatEventType(event.event_type)}
            </p>
            <p className="text-xs text-neutral-400">{timeAgo(event.created_at)}</p>
          </div>
          <span
            className={`font-bold tabular-nums ${
              event.points > 0 ? "text-green-600" : "text-red-500"
            }`}
          >
            {event.points > 0 ? "+" : ""}
            {event.points}
          </span>
        </div>
      ))}
    </div>
  );
}
