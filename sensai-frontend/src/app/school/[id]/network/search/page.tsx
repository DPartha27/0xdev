"use client";

import React, { Suspense } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { Header } from "@/components/layout/header";
import { useSchools } from "@/lib/api";
import { useNetworkSearch } from "@/lib/network-api";
import SearchResultsList from "@/components/SearchResultsList";
import NetworkSearchBar from "@/components/NetworkSearchBar";

function SearchResults({
  orgId,
  schoolId,
}: {
  orgId: number;
  schoolId: string;
}) {
  const searchParams = useSearchParams();
  const query = searchParams.get("q") ?? "";
  const type = searchParams.get("type") ?? undefined;
  const { results, isLoading } = useNetworkSearch(query, orgId, type);

  return (
    <div>
      {query && (
        <p className="text-sm text-neutral-500 mb-4">
          {isLoading ? "Searching…" : `${results.length} results for "${query}"`}
        </p>
      )}
      <SearchResultsList
        results={results}
        isLoading={isLoading}
        schoolId={schoolId}
      />
    </div>
  );
}

export default function SearchPage() {
  const params = useParams();
  const schoolId = params.id as string;
  const { schools } = useSchools();

  const school = schools?.find(
    (s) => s.id === schoolId || s.slug === schoolId
  );
  const orgId = school ? parseInt(school.id) : null;

  return (
    <div className="min-h-screen bg-white dark:bg-black">
      <div className="hidden sm:block">
        <Header showCreateCourseButton={false} />
      </div>
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
          Search Network
        </h1>

        {orgId && (
          <NetworkSearchBar orgId={orgId} schoolId={schoolId} />
        )}

        {orgId && (
          <Suspense fallback={<div className="text-sm text-neutral-500">Loading…</div>}>
            <SearchResults orgId={orgId} schoolId={schoolId} />
          </Suspense>
        )}
      </div>
    </div>
  );
}
