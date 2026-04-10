"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Header } from "@/components/layout/header";
import { useAuth } from "@/lib/auth";
import { useSchools } from "@/lib/api";
import { useSkills } from "@/lib/network-api";
import HubDetailView from "@/components/HubDetailView";
import type { Hub } from "@/types/network";

export default function HubPage() {
  const params = useParams();
  const schoolId = params.id as string;
  const hubSlug = params.hubSlug as string;
  const { user } = useAuth();
  const { schools } = useSchools();

  const school = schools?.find(
    (s) => s.id === schoolId || s.slug === schoolId
  );
  const orgId = school ? parseInt(school.id) : null;
  const isAdmin = school?.role === "owner" || school?.role === "admin";

  const { skills } = useSkills(orgId);
  const [hub, setHub] = useState<Hub | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!orgId) return;
    setLoading(true);
    fetch(
      `${process.env.NEXT_PUBLIC_BACKEND_URL}/hubs/?org_id=${orgId}`
    )
      .then((r) => r.json())
      .then((hubs: Hub[]) => {
        const found = hubs.find((h) => h.slug === hubSlug);
        if (!found) throw new Error("Hub not found");
        setHub(found);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [orgId, hubSlug]);

  if (loading) {
    return (
      <div className="min-h-screen bg-white dark:bg-black">
        <div className="hidden sm:block">
          <Header showCreateCourseButton={false} />
        </div>
        <div className="flex justify-center items-center py-24">
          <div className="w-10 h-10 border-t-2 border-b-2 rounded-full animate-spin border-neutral-400" />
        </div>
      </div>
    );
  }

  if (error || !hub) {
    return (
      <div className="min-h-screen bg-white dark:bg-black flex items-center justify-center">
        <p className="text-neutral-500">{error ?? "Hub not found"}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-black">
      <div className="hidden sm:block">
        <Header showCreateCourseButton={false} />
      </div>
      <div className="max-w-5xl mx-auto px-4 py-8">
        <HubDetailView
          hub={hub}
          schoolId={schoolId}
          currentUserId={user?.id ? parseInt(user.id.toString()) : 0}
          canManage={isAdmin}
          availableSkills={skills}
        />
      </div>
    </div>
  );
}
