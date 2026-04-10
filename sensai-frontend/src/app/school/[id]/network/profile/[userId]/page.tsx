"use client";

import React from "react";
import { useParams } from "next/navigation";
import { Header } from "@/components/layout/header";
import { useSchools } from "@/lib/api";
import { useUserReputation, useReputationHistory } from "@/lib/network-api";
import ReputationCard from "@/components/ReputationCard";
import ContributionHistory from "@/components/ContributionHistory";

export default function UserProfilePage() {
  const params = useParams();
  const schoolId = params.id as string;
  const userId = parseInt(params.userId as string);
  const { schools } = useSchools();

  const school = schools?.find(
    (s) => s.id === schoolId || s.slug === schoolId
  );
  const orgId = school ? parseInt(school.id) : null;

  const { reputation, isLoading: repLoading } = useUserReputation(userId, orgId);
  const { history, isLoading: histLoading } = useReputationHistory(userId, orgId);

  return (
    <div className="min-h-screen bg-white dark:bg-black">
      <div className="hidden sm:block">
        <Header showCreateCourseButton={false} />
      </div>
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
          User Profile
        </h1>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {repLoading ? (
            <div className="rounded-xl border bg-neutral-100 dark:bg-neutral-800 animate-pulse h-48" />
          ) : reputation ? (
            <ReputationCard reputation={reputation} />
          ) : (
            <div className="rounded-xl border bg-white dark:bg-neutral-900 p-5 text-sm text-neutral-500">
              No reputation data yet.
            </div>
          )}

          <div className="rounded-xl border bg-white dark:bg-neutral-900 p-5">
            <h2 className="font-semibold text-sm text-neutral-900 dark:text-neutral-100 mb-3">
              Contribution History
            </h2>
            <ContributionHistory
              events={history}
              isLoading={histLoading}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
