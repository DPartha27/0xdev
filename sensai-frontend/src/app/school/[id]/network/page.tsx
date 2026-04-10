"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Header } from "@/components/layout/header";
import { useAuth } from "@/lib/auth";
import { useSchools } from "@/lib/api";
import { useHubs, createHub } from "@/lib/network-api";
import HubListView from "@/components/HubListView";
import NetworkSearchBar from "@/components/NetworkSearchBar";
import TrendingFeed from "@/components/TrendingFeed";
import RecommendedPosts from "@/components/RecommendedPosts";

export default function NetworkPage() {
  const params = useParams();
  const router = useRouter();
  const schoolId = params.id as string;
  const { user } = useAuth();
  const { schools } = useSchools();

  // Resolve orgId from schools list using schoolId param
  const school = schools?.find(
    (s) => s.id === schoolId || s.slug === schoolId
  );
  const orgId = school ? parseInt(school.id) : null;

  const isAdmin = school?.role === "owner" || school?.role === "admin";

  const { hubs, isLoading, refetch } = useHubs(orgId);
  const [showCreateForm, setShowCreateForm] = useState(false);

  // Simple hub creation dialog (inline for now)
  const [newHubName, setNewHubName] = useState("");
  const [creating, setCreating] = useState(false);

  async function handleCreateHub() {
    if (!newHubName.trim() || !orgId || !user?.id) return;
    setCreating(true);
    try {
      await createHub({
        org_id: orgId,
        name: newHubName.trim(),
        slug: newHubName.trim().toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, ""),
        created_by: parseInt(user.id.toString()),
      });
      setNewHubName("");
      setShowCreateForm(false);
      refetch();
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="min-h-screen bg-white dark:bg-black">
      <div className="hidden sm:block">
        <Header showCreateCourseButton={false} />
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Page header */}
        <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
              Network
            </h1>
            <p className="text-sm text-neutral-500 mt-0.5">
              Discuss, ask questions, and share knowledge with your cohort
            </p>
          </div>
          {orgId && (
            <div className="sm:ml-auto">
              <NetworkSearchBar orgId={orgId} schoolId={schoolId} />
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Hub listing */}
          <div className="lg:col-span-2">
            {showCreateForm && isAdmin && (
              <div className="mb-4 p-4 rounded-xl border bg-white dark:bg-neutral-900">
                <h3 className="font-medium mb-3 text-sm">Create a new hub</h3>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newHubName}
                    onChange={(e) => setNewHubName(e.target.value)}
                    placeholder="Hub name"
                    className="flex-1 px-3 py-2 text-sm rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    onKeyDown={(e) => e.key === "Enter" && handleCreateHub()}
                  />
                  <button
                    type="button"
                    disabled={creating || !newHubName.trim()}
                    onClick={handleCreateHub}
                    className="px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    {creating ? "Creating…" : "Create"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="px-3 py-2 text-sm rounded-lg text-neutral-600 hover:bg-neutral-100 dark:hover:bg-neutral-800"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            <HubListView
              hubs={hubs}
              schoolId={schoolId}
              isLoading={isLoading}
              canCreate={isAdmin}
              onCreateHub={() => setShowCreateForm(true)}
            />
          </div>

          {/* Sidebar */}
          {orgId && (
            <div className="space-y-4">
              <TrendingFeed orgId={orgId} schoolId={schoolId} />
              {user?.id && (
                <RecommendedPosts
                  userId={parseInt(user.id.toString())}
                  orgId={orgId}
                  schoolId={schoolId}
                />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
