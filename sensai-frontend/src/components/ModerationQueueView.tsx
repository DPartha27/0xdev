"use client";

import React, { useState } from "react";
import type { Flag } from "@/types/network";
import { useModerationQueue, resolveFlag } from "@/lib/network-api";
import { CheckCircle, XCircle, Eye, Trash2 } from "lucide-react";

interface ModerationQueueViewProps {
  orgId: number;
  reviewerId: number;
}

const ACTION_LABELS: Record<string, { label: string; color: string }> = {
  dismiss: { label: "Dismiss", color: "text-neutral-600" },
  hide: { label: "Hide", color: "text-orange-600" },
  delete: { label: "Delete", color: "text-red-600" },
  warn: { label: "Warn User", color: "text-yellow-600" },
};

export default function ModerationQueueView({
  orgId,
  reviewerId,
}: ModerationQueueViewProps) {
  const { flags, isLoading, refetch } = useModerationQueue(orgId);
  const [actionPending, setActionPending] = useState<number | null>(null);

  async function handleAction(flagId: number, action: string) {
    setActionPending(flagId);
    try {
      await resolveFlag(flagId, reviewerId, action);
      refetch();
    } finally {
      setActionPending(null);
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={i}
            className="h-20 rounded-xl bg-neutral-100 dark:bg-neutral-800 animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (flags.length === 0) {
    return (
      <div className="py-16 text-center text-neutral-500">
        <CheckCircle className="w-10 h-10 mx-auto mb-2 text-green-500" />
        <p>No pending flags. Queue is clear!</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-neutral-500">
        {flags.length} pending flag{flags.length !== 1 ? "s" : ""}
      </p>
      {flags.map((flag) => (
        <div
          key={flag.id}
          className="rounded-xl border bg-white dark:bg-neutral-900 p-4"
        >
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <span className="text-xs font-medium bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 px-2 py-0.5 rounded-full capitalize">
                  {flag.target_type}
                </span>
                <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full capitalize">
                  {flag.reason.replace("_", " ")}
                </span>
              </div>
              <p className="text-xs text-neutral-500">
                Reported {flag.created_at ? new Date(flag.created_at).toLocaleDateString() : ""}
                {flag.description && (
                  <span className="block mt-0.5 italic">"{flag.description}"</span>
                )}
              </p>
            </div>

            <div className="flex flex-wrap gap-1.5 shrink-0">
              {Object.entries(ACTION_LABELS).map(([action, { label, color }]) => (
                <button
                  key={action}
                  type="button"
                  disabled={actionPending === flag.id}
                  onClick={() => handleAction(flag.id, action)}
                  className={`px-3 py-1 text-xs rounded-full border transition-colors disabled:opacity-50 ${color} border-current hover:bg-neutral-50 dark:hover:bg-neutral-800`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
