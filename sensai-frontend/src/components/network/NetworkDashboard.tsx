"use client";

import { useState, useEffect } from "react";
import { useSchools } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import NetworkFeed from "./NetworkFeed";
import TagsSidebar from "./TagsSidebar";

export default function NetworkDashboard() {
    const { schools } = useSchools();
    const { user } = useAuth();
    const [selectedTag, setSelectedTag] = useState<string | null>(null);
    const [orgId, setOrgId] = useState<number | null>(null);

    useEffect(() => {
        // Try from schools first
        if (schools && schools.length > 0) {
            setOrgId(Number(schools[0].id));
            return;
        }

        // Fallback: fetch all orgs from backend to find one with network posts
        fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/posts?org_id=0&limit=1`)
            .catch(() => {});

        // Try fetching the default org directly
        if (user?.id) {
            fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/users/${user.id}/orgs`)
                .then(res => res.ok ? res.json() : [])
                .then(data => {
                    if (data && data.length > 0) {
                        setOrgId(Number(data[0].id));
                    } else {
                        // Fallback: use org 1 (the seeded org)
                        setOrgId(1);
                    }
                })
                .catch(() => setOrgId(1));
        } else {
            // No user yet, default to org 1
            setOrgId(1);
        }
    }, [schools, user?.id]);

    return (
        <div className="flex flex-col lg:flex-row gap-6 max-w-7xl mx-auto px-4 sm:px-8 pt-6 pb-12">
            {/* Tags sidebar - shows on top for mobile, right side for desktop */}
            <div className="lg:hidden">
                <TagsSidebar orgId={orgId} selectedTag={selectedTag} onTagSelect={setSelectedTag} />
            </div>

            {/* Main feed */}
            <div className="flex-1 min-w-0">
                <NetworkFeed orgId={orgId} selectedTag={selectedTag} />
            </div>

            {/* Desktop sidebar */}
            <div className="hidden lg:block w-72 flex-shrink-0">
                <div className="sticky top-20">
                    <TagsSidebar orgId={orgId} selectedTag={selectedTag} onTagSelect={setSelectedTag} />
                </div>
            </div>
        </div>
    );
}
