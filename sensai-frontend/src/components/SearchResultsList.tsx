import React from "react";
import Link from "next/link";
import type { SearchResult } from "@/types/network";
import { MessageSquare, Hash, Tag } from "lucide-react";

interface SearchResultsListProps {
  results: SearchResult[];
  isLoading?: boolean;
  schoolId: string;
  onSelect?: () => void;
}

const TYPE_ICONS = {
  post: MessageSquare,
  hub: Hash,
  skill: Tag,
};

const TYPE_LABELS = {
  post: "Post",
  hub: "Hub",
  skill: "Skill",
};

function getHref(result: SearchResult, schoolId: string): string {
  if (result.type === "hub") {
    return `/school/${schoolId}/network/${result.title
      .toLowerCase()
      .replace(/\s+/g, "-")}`;
  }
  if (result.type === "post") {
    const hubSlug = result.hub_name
      ? result.hub_name.toLowerCase().replace(/\s+/g, "-")
      : "unknown";
    return `/school/${schoolId}/network/${hubSlug}/posts/${result.id}`;
  }
  return `/school/${schoolId}/network`;
}

export default function SearchResultsList({
  results,
  isLoading,
  schoolId,
  onSelect,
}: SearchResultsListProps) {
  if (isLoading) {
    return (
      <div className="p-4 space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={i}
            className="h-12 rounded-lg bg-neutral-100 dark:bg-neutral-800 animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="p-6 text-center text-sm text-neutral-500">
        No results found.
      </div>
    );
  }

  return (
    <div>
      {results.map((result) => {
        const Icon = TYPE_ICONS[result.type];
        return (
          <Link
            key={`${result.type}-${result.id}`}
            href={getHref(result, schoolId)}
            onClick={onSelect}
            className="flex items-start gap-3 px-4 py-3 hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors"
          >
            <Icon className="w-4 h-4 text-neutral-400 mt-0.5 shrink-0" />
            <div className="min-w-0">
              <p className="text-sm font-medium text-neutral-800 dark:text-neutral-200 truncate">
                {result.title}
              </p>
              <p className="text-xs text-neutral-500 truncate">
                {TYPE_LABELS[result.type]}
                {result.hub_name && ` · ${result.hub_name}`}
              </p>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
