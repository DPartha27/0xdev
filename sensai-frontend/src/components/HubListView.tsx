"use client";

import React, { useState } from "react";
import { Search, Plus } from "lucide-react";
import type { Hub } from "@/types/network";
import HubCard from "./HubCard";

interface HubListViewProps {
  hubs: Hub[];
  schoolId: string;
  isLoading?: boolean;
  canCreate?: boolean;
  onCreateHub?: () => void;
}

export default function HubListView({
  hubs,
  schoolId,
  isLoading,
  canCreate,
  onCreateHub,
}: HubListViewProps) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"all" | "public" | "private">("all");

  const filtered = hubs.filter((h) => {
    const matchesQuery =
      !query ||
      h.name.toLowerCase().includes(query.toLowerCase()) ||
      h.description?.toLowerCase().includes(query.toLowerCase());
    const matchesFilter =
      filter === "all" || h.visibility === filter;
    return matchesQuery && matchesFilter;
  });

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-2 sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
          <input
            type="text"
            placeholder="Search hubs…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm rounded-lg border bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex gap-1 shrink-0">
          {(["all", "public", "private"] as const).map((v) => (
            <button
              key={v}
              onClick={() => setFilter(v)}
              className={`px-3 py-1.5 text-xs rounded-md capitalize transition-colors ${
                filter === v
                  ? "bg-neutral-900 dark:bg-white text-white dark:text-neutral-900 font-medium"
                  : "text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800"
              }`}
            >
              {v}
            </button>
          ))}
        </div>

        {canCreate && (
          <button
            onClick={onCreateHub}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors shrink-0"
          >
            <Plus className="w-4 h-4" />
            New Hub
          </button>
        )}
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="rounded-xl border bg-neutral-100 dark:bg-neutral-800 animate-pulse h-36"
            />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="py-16 text-center text-neutral-500">
          {query
            ? `No hubs match "${query}"`
            : "No hubs yet. Be the first to create one!"}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {filtered.map((hub) => (
            <HubCard key={hub.id} hub={hub} schoolId={schoolId} />
          ))}
        </div>
      )}
    </div>
  );
}
