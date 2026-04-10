"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { useSchools } from "@/lib/api";
import { UserNetworkProfile, NetworkPost } from "@/types/network";
import BadgeIndicator from "./BadgeIndicator";
import PostCard from "./PostCard";
import {
    ArrowLeft,
    Trophy,
    BookOpen,
    MessageSquare,
    ThumbsUp,
    ThumbsDown,
    PenLine,
    TrendingUp,
    Shield,
    Star,
} from "lucide-react";

const BADGE_TIERS = [
    { threshold: 0, name: "Bronze 1" },
    { threshold: 50, name: "Bronze 2" },
    { threshold: 120, name: "Bronze 3" },
    { threshold: 200, name: "Silver 1" },
    { threshold: 300, name: "Silver 2" },
    { threshold: 420, name: "Silver 3" },
    { threshold: 550, name: "Gold 1" },
    { threshold: 700, name: "Gold 2" },
    { threshold: 870, name: "Gold 3" },
    { threshold: 1050, name: "Platinum 1" },
    { threshold: 1250, name: "Platinum 2" },
    { threshold: 1470, name: "Platinum 3" },
    { threshold: 1700, name: "Diamond 1" },
    { threshold: 1950, name: "Diamond 2" },
    { threshold: 2220, name: "Diamond 3" },
    { threshold: 2500, name: "God" },
];

function getNextTier(currentScore: number) {
    for (const tier of BADGE_TIERS) {
        if (currentScore < tier.threshold) {
            return tier;
        }
    }
    return null; // already at max
}

function getCurrentTierIndex(tierName: string) {
    return BADGE_TIERS.findIndex((t) => t.name === tierName);
}

function getProgressToNextTier(score: number) {
    let prevThreshold = 0;
    for (const tier of BADGE_TIERS) {
        if (score < tier.threshold) {
            const range = tier.threshold - prevThreshold;
            const progress = score - prevThreshold;
            return { percent: Math.round((progress / range) * 100), nextTier: tier.name, pointsNeeded: tier.threshold - score };
        }
        prevThreshold = tier.threshold;
    }
    return { percent: 100, nextTier: null, pointsNeeded: 0 };
}

const roleConfig: Record<string, { label: string; color: string; icon: React.ElementType }> = {
    mentor: { label: "Mentor", color: "text-purple-600 dark:text-purple-400 bg-purple-100 dark:bg-purple-900/30 border-purple-300 dark:border-purple-700", icon: Shield },
    master: { label: "Master", color: "text-yellow-600 dark:text-yellow-400 bg-yellow-100 dark:bg-yellow-900/30 border-yellow-300 dark:border-yellow-700", icon: Star },
    newbie: { label: "Newbie", color: "text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 border-gray-300 dark:border-gray-600", icon: TrendingUp },
};

export default function UserProfileDashboard() {
    const router = useRouter();
    const { user } = useAuth();
    const { schools } = useSchools();
    const [profile, setProfile] = useState<UserNetworkProfile | null>(null);
    const [recentPosts, setRecentPosts] = useState<NetworkPost[]>([]);
    const [orgId, setOrgId] = useState<number | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Resolve org
    useEffect(() => {
        if (schools && schools.length > 0) {
            setOrgId(Number(schools[0].id));
            return;
        }
        if (user?.id) {
            fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/users/${user.id}/orgs`)
                .then((res) => (res.ok ? res.json() : []))
                .then((data) => setOrgId(data?.[0]?.id ? Number(data[0].id) : 1))
                .catch(() => setOrgId(1));
        }
    }, [schools, user?.id]);

    // Fetch profile + recent posts
    useEffect(() => {
        if (!user?.id || !orgId) return;
        setIsLoading(true);

        Promise.all([
            fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/profile/${user.id}?org_id=${orgId}`).then((r) => (r.ok ? r.json() : null)),
            fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/profile/${user.id}/posts?org_id=${orgId}&limit=5`).then((r) => (r.ok ? r.json() : [])),
        ])
            .then(([profileData, postsData]) => {
                setProfile(profileData);
                setRecentPosts(postsData || []);
            })
            .catch(() => {})
            .finally(() => setIsLoading(false));
    }, [user?.id, orgId]);

    const handleVote = async (postId: number, voteType: string) => {
        if (!user?.id) return;
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/posts/${postId}/vote`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: user.id, vote_type: voteType }),
            });
            if (res.ok) {
                const result = await res.json();
                setRecentPosts((prev) =>
                    prev.map((p) => {
                        if (p.id !== postId) return p;
                        const oldVote = p.user_vote;
                        let upvotes = p.upvote_count;
                        let downvotes = p.downvote_count;
                        if (result.action === "removed") {
                            if (oldVote === "upvote") upvotes--;
                            else if (oldVote === "downvote") downvotes--;
                        } else if (result.action === "changed") {
                            if (result.vote_type === "upvote") { upvotes++; downvotes--; }
                            else { downvotes++; upvotes--; }
                        } else {
                            if (result.vote_type === "upvote") upvotes++;
                            else downvotes++;
                        }
                        return { ...p, user_vote: result.vote_type, upvote_count: Math.max(0, upvotes), downvote_count: Math.max(0, downvotes) };
                    })
                );
            }
        } catch {}
    };

    if (isLoading) {
        return (
            <div className="max-w-4xl mx-auto px-4 sm:px-8 pt-6 pb-12">
                <div className="animate-pulse space-y-6">
                    <div className="h-8 w-48 bg-gray-200 dark:bg-[#222] rounded" />
                    <div className="h-48 bg-gray-200 dark:bg-[#222] rounded-xl" />
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                        {[1, 2, 3, 4].map((i) => (
                            <div key={i} className="h-24 bg-gray-200 dark:bg-[#222] rounded-xl" />
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    if (!profile) {
        return (
            <div className="max-w-4xl mx-auto px-4 sm:px-8 pt-6 pb-12 text-center">
                <p className="text-gray-500">Could not load profile.</p>
            </div>
        );
    }

    const progress = getProgressToNextTier(profile.badge_score);
    const role = roleConfig[profile.network_role] || roleConfig.newbie;
    const RoleIcon = role.icon;
    const initials = `${profile.first_name?.[0] || ""}${profile.last_name?.[0] || ""}`.toUpperCase() || "?";

    return (
        <div className="max-w-4xl mx-auto px-4 sm:px-8 pt-6 pb-12">
            {/* Back */}
            <button
                onClick={() => router.push("/network")}
                className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-black dark:hover:text-white mb-6 cursor-pointer transition-colors"
            >
                <ArrowLeft className="w-4 h-4" />
                Back to SenseNet
            </button>

            {/* Hero card */}
            <div className="rounded-xl border border-gray-200 dark:border-[#35363a] bg-white dark:bg-[#111111] p-6 sm:p-8 mb-6">
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-5">
                    {/* Avatar */}
                    <div className="w-20 h-20 rounded-full bg-purple-600 flex items-center justify-center text-white text-2xl font-bold flex-shrink-0">
                        {initials}
                    </div>

                    <div className="flex-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-3 mb-1">
                            <h1 className="text-xl sm:text-2xl font-bold">
                                {profile.first_name} {profile.last_name}
                            </h1>
                            <BadgeIndicator tier={profile.badge_tier} size="lg" />
                            <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${role.color}`}>
                                <RoleIcon className="w-3 h-3" />
                                {role.label}
                            </span>
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">{profile.email}</p>

                        {/* Progress to next tier */}
                        <div className="max-w-md">
                            <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                                <span>{profile.badge_tier}</span>
                                <span>
                                    {progress.nextTier
                                        ? `${progress.pointsNeeded} pts to ${progress.nextTier}`
                                        : "Max tier reached"}
                                </span>
                            </div>
                            <div className="w-full h-2 bg-gray-200 dark:bg-[#333] rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-purple-500 to-blue-500 rounded-full transition-all duration-500"
                                    style={{ width: `${progress.percent}%` }}
                                />
                            </div>
                            <p className="text-xs text-gray-400 mt-1">
                                Total score: <span className="font-semibold text-gray-600 dark:text-gray-300">{profile.badge_score}</span>
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Score breakdown */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-6">
                <ScoreCard
                    icon={BookOpen}
                    label="Learning"
                    value={profile.learning_score}
                    max={500}
                    color="text-green-600 dark:text-green-400"
                    bgColor="bg-green-50 dark:bg-green-900/20"
                    description="Tasks completed"
                />
                <ScoreCard
                    icon={PenLine}
                    label="Contribution"
                    value={profile.contribution_score}
                    max={500}
                    color="text-blue-600 dark:text-blue-400"
                    bgColor="bg-blue-50 dark:bg-blue-900/20"
                    description="Posts, comments, upvotes"
                />
                <ScoreCard
                    icon={Trophy}
                    label="Endorsement"
                    value={profile.endorsement_score}
                    max={500}
                    color="text-amber-600 dark:text-amber-400"
                    bgColor="bg-amber-50 dark:bg-amber-900/20"
                    description="Mentor endorsements"
                />
                <ScoreCard
                    icon={ThumbsDown}
                    label="Penalty"
                    value={profile.downvote_penalty}
                    max={200}
                    color="text-red-500 dark:text-red-400"
                    bgColor="bg-red-50 dark:bg-red-900/20"
                    description="Downvotes received"
                    isNegative
                />
            </div>

            {/* Activity stats */}
            <div className="rounded-xl border border-gray-200 dark:border-[#35363a] bg-white dark:bg-[#111111] p-6 mb-6">
                <h2 className="text-base font-semibold mb-4">Activity</h2>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <ActivityStat icon={MessageSquare} label="Posts" value={profile.posts_count} />
                    <ActivityStat icon={MessageSquare} label="Comments" value={profile.comments_count} />
                    <ActivityStat icon={ThumbsUp} label="Upvotes Received" value={profile.upvotes_received} />
                    <ActivityStat icon={ThumbsDown} label="Downvotes Received" value={profile.downvotes_received} />
                </div>
                {profile.last_active_at && (
                    <p className="text-xs text-gray-400 mt-4">
                        Last active: {new Date(profile.last_active_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                    </p>
                )}
            </div>

            {/* Badge journey */}
            <div className="rounded-xl border border-gray-200 dark:border-[#35363a] bg-white dark:bg-[#111111] p-6 mb-6">
                <h2 className="text-base font-semibold mb-4">Badge Journey</h2>
                <div className="flex flex-wrap gap-2">
                    {BADGE_TIERS.map((tier, i) => {
                        const currentIdx = getCurrentTierIndex(profile.badge_tier);
                        const reached = i <= currentIdx;
                        return (
                            <div
                                key={tier.name}
                                className={`transition-opacity ${reached ? "opacity-100" : "opacity-30"}`}
                            >
                                <BadgeIndicator tier={tier.name} size="md" />
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* How scores work */}
            <div className="rounded-xl border border-gray-200 dark:border-[#35363a] bg-white dark:bg-[#111111] p-6 mb-6">
                <h2 className="text-base font-semibold mb-3">How Scoring Works</h2>
                <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                    <div className="flex items-start gap-2">
                        <BookOpen className="w-4 h-4 mt-0.5 text-green-500 flex-shrink-0" />
                        <span><strong className="text-gray-800 dark:text-gray-200">Learning:</strong> +10 pts per task completed (max 500)</span>
                    </div>
                    <div className="flex items-start gap-2">
                        <PenLine className="w-4 h-4 mt-0.5 text-blue-500 flex-shrink-0" />
                        <span><strong className="text-gray-800 dark:text-gray-200">Contribution:</strong> +5 per post, +3 per upvote received, +2 per comment (max 500)</span>
                    </div>
                    <div className="flex items-start gap-2">
                        <ThumbsDown className="w-4 h-4 mt-0.5 text-red-500 flex-shrink-0" />
                        <span><strong className="text-gray-800 dark:text-gray-200">Penalty:</strong> -2 per downvote received (max -200)</span>
                    </div>
                    <div className="flex items-start gap-2">
                        <TrendingUp className="w-4 h-4 mt-0.5 text-purple-500 flex-shrink-0" />
                        <span><strong className="text-gray-800 dark:text-gray-200">Role promotion:</strong> Reach Gold 1 (550 pts) to become a Master</span>
                    </div>
                </div>
            </div>

            {/* Recent posts */}
            {recentPosts.length > 0 && (
                <div>
                    <h2 className="text-base font-semibold mb-3">Recent Posts</h2>
                    <div className="space-y-3">
                        {recentPosts.map((post) => (
                            <PostCard key={post.id} post={post} onVote={handleVote} />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

function ScoreCard({
    icon: Icon,
    label,
    value,
    max,
    color,
    bgColor,
    description,
    isNegative = false,
}: {
    icon: React.ElementType;
    label: string;
    value: number;
    max: number;
    color: string;
    bgColor: string;
    description: string;
    isNegative?: boolean;
}) {
    const percent = Math.min(100, Math.round((value / max) * 100));
    return (
        <div className="rounded-xl border border-gray-200 dark:border-[#35363a] bg-white dark:bg-[#111111] p-4">
            <div className="flex items-center gap-2 mb-2">
                <div className={`w-8 h-8 rounded-lg ${bgColor} flex items-center justify-center`}>
                    <Icon className={`w-4 h-4 ${color}`} />
                </div>
                <span className="text-xs text-gray-500 dark:text-gray-400">{label}</span>
            </div>
            <p className={`text-xl font-bold ${isNegative && value > 0 ? "text-red-500" : ""}`}>
                {isNegative && value > 0 ? "-" : ""}
                {value}
                <span className="text-xs font-normal text-gray-400">/{max}</span>
            </p>
            <div className="w-full h-1.5 bg-gray-100 dark:bg-[#333] rounded-full mt-2 overflow-hidden">
                <div
                    className={`h-full rounded-full transition-all duration-500 ${isNegative ? "bg-red-400" : "bg-gradient-to-r from-purple-500 to-blue-500"}`}
                    style={{ width: `${percent}%` }}
                />
            </div>
            <p className="text-[10px] text-gray-400 mt-1">{description}</p>
        </div>
    );
}

function ActivityStat({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: number }) {
    return (
        <div className="text-center">
            <div className="flex items-center justify-center gap-1.5 text-gray-400 mb-1">
                <Icon className="w-3.5 h-3.5" />
                <span className="text-xs">{label}</span>
            </div>
            <p className="text-2xl font-bold">{value}</p>
        </div>
    );
}
