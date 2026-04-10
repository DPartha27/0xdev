"use client";

import React, { useState } from "react";
import { Search, X } from "lucide-react";
import { useNetworkSearch } from "@/lib/network-api";
import type { SearchResult, SearchResultType } from "@/types/network";
import SearchResultsList from "./SearchResultsList";

interface NetworkSearchBarProps {
  orgId: number;
  schoolId: string;
}

const TYPE_FILTERS: { value: SearchResultType | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "post", label: "Posts" },
  { value: "hub", label: "Hubs" },
  { value: "skill", label: "Skills" },
];

export default function NetworkSearchBar({
  orgId,
  schoolId,
}: NetworkSearchBarProps) {
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<SearchResultType | "all">("all");
  const [open, setOpen] = useState(false);

  const { results, isLoading } = useNetworkSearch(
    query,
    orgId,
    typeFilter !== "all" ? typeFilter : undefined
  );

  function handleClear() {
    setQuery("");
    setOpen(false);
  }

  return (
    <div className="relative w-full max-w-xl">
      {/* Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(Boolean(e.target.value));
          }}
          onFocus={() => query && setOpen(true)}
          placeholder="Search posts, hubs, skills…"
          className="w-full pl-9 pr-8 py-2 text-sm rounded-xl border bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {query && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-neutral-400 hover:text-neutral-600"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Dropdown */}
      {open && (
        <div className="absolute top-full left-0 right-0 mt-1 z-50 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded-xl shadow-xl overflow-hidden">
          {/* Type filter */}
          <div className="flex gap-1 p-2 border-b border-neutral-100 dark:border-neutral-800">
            {TYPE_FILTERS.map((f) => (
              <button
                key={f.value}
                type="button"
                onClick={() => setTypeFilter(f.value as any)}
                className={`px-3 py-1 text-xs rounded-md transition-colors ${
                  typeFilter === f.value
                    ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                    : "text-neutral-500 hover:bg-neutral-100 dark:hover:bg-neutral-800"
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          <div className="max-h-80 overflow-y-auto">
            <SearchResultsList
              results={results}
              isLoading={isLoading}
              schoolId={schoolId}
              onSelect={handleClear}
            />
          </div>
        </div>
      )}
    </div>
  );
}
