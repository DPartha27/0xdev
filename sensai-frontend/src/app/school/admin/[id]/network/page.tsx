"use client";

import React from "react";
import { useParams } from "next/navigation";
import { Header } from "@/components/layout/header";
import { useAuth } from "@/lib/auth";
import { useSchools } from "@/lib/api";
import ModerationQueueView from "@/components/ModerationQueueView";
import { useReputationLeaderboard } from "@/lib/network-api";
import ReputationBadge from "@/components/ReputationBadge";
import Link from "next/link";

export default function AdminNetworkPage() {
  const params = useParams();
  const schoolId = params.id as string;
  const { user } = useAuth();
  const { schools } = useSchools();

  const school = schools?.find(
    (s) => s.id === schoolId || s.slug === schoolId
  );
  const orgId = school ? parseInt(school.id) : null;
  const isAdmin = school?.role === "owner" || school?.role === "admin";

  const { leaderboard, isLoading: lbLoading } = useReputationLeaderboard(orgId);

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-white dark:bg-black flex items-center justify-center">
        <p className="text-neutral-500">Admin access required</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-black">
      <div className="hidden sm:block">
        <Header showCreateCourseButton={false} />
      </div>
      <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
            Network Admin
          </h1>
          <Link
            href={`/school/${schoolId}/network`}
            className="text-sm text-blue-600 hover:underline"
          >
            View as member →
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Moderation queue */}
          <div className="rounded-xl border bg-white dark:bg-neutral-900 p-5">
            <h2 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
              Moderation Queue
            </h2>
            {orgId && user?.id && (
              <ModerationQueueView
                orgId={orgId}
                reviewerId={parseInt(user.id.toString())}
              />
            )}
          </div>

          {/* Reputation leaderboard */}
          <div className="rounded-xl border bg-white dark:bg-neutral-900 p-5">
            <h2 className="font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
              Reputation Leaderboard
            </h2>
            {lbLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div
                    key={i}
                    className="h-10 rounded bg-neutral-100 dark:bg-neutral-800 animate-pulse"
                  />
                ))}
              </div>
            ) : (
              <div className="divide-y divide-neutral-100 dark:divide-neutral-800">
                {leaderboard.slice(0, 10).map((entry, idx) => (
                  <div
                    key={entry.user_id}
                    className="flex items-center justify-between py-2.5"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-bold text-neutral-400 w-6">
                        {idx + 1}
                      </span>
                      <Link
                        href={`/school/${schoolId}/network/profile/${entry.user_id}`}
                        className="text-sm font-medium text-neutral-700 dark:text-neutral-300 hover:text-blue-600"
                      >
                        User #{entry.user_id}
                      </Link>
                    </div>
                    <div className="flex items-center gap-2">
                      <ReputationBadge level={entry.level} size="xs" />
                      <span className="text-sm font-bold tabular-nums text-neutral-700 dark:text-neutral-300">
                        {entry.total_points.toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
