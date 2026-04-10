"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Search, Plus, ShieldCheck } from "lucide-react";
import { useNetworkFeed } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import PostCard from "./PostCard";

interface NetworkFeedProps {
    orgId: number | null;
    selectedTag: string | null;
    userRole?: string;
}

type FilterType = 'for_you' | 'recent' | 'popular' | 'unanswered';

export default function NetworkFeed({ orgId, selectedTag, userRole }: NetworkFeedProps) {
    const router = useRouter();
    const { user } = useAuth();
    const [activeFilter, setActiveFilter] = useState<FilterType>('for_you');
    const [searchQuery, setSearchQuery] = useState("");
    const [debouncedSearch, setDebouncedSearch] = useState("");
    const timerRef = useRef<NodeJS.Timeout | null>(null);

    const { posts, isLoading, setPosts } = useNetworkFeed(orgId, activeFilter, selectedTag || undefined, debouncedSearch || undefined);

    // Debounce search
    useEffect(() => {
        if (timerRef.current) clearTimeout(timerRef.current);
        timerRef.current = setTimeout(() => {
            setDebouncedSearch(searchQuery);
        }, 300);
        return () => { if (timerRef.current) clearTimeout(timerRef.current); };
    }, [searchQuery]);

    const handleVote = async (postId: number, voteType: string) => {
        if (!user?.id) return;
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/posts/${postId}/vote`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: user.id, vote_type: voteType }),
            });
            if (res.ok) {
                const result = await res.json();
                setPosts(prev => prev.map(p => {
                    if (p.id !== postId) return p;
                    const oldVote = p.user_vote;
                    let upvotes = p.upvote_count;
                    let downvotes = p.downvote_count;

                    if (result.action === 'removed') {
                        if (oldVote === 'upvote') upvotes--;
                        else if (oldVote === 'downvote') downvotes--;
                    } else if (result.action === 'changed') {
                        if (result.vote_type === 'upvote') { upvotes++; downvotes--; }
                        else { downvotes++; upvotes--; }
                    } else {
                        if (result.vote_type === 'upvote') upvotes++;
                        else downvotes++;
                    }

                    return { ...p, user_vote: result.vote_type, upvote_count: Math.max(0, upvotes), downvote_count: Math.max(0, downvotes) };
                }));
            }
        } catch (err) {
            console.error('Error voting:', err);
        }
    };

    const filters: { key: FilterType; label: string }[] = [
        { key: 'for_you', label: 'For You' },
        { key: 'recent', label: 'Recent' },
        { key: 'popular', label: 'Popular' },
        { key: 'unanswered', label: 'Unanswered' },
    ];

    return (
        <div className="flex-1 min-w-0">
            {/* Search bar */}
            <div className="relative mb-4">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search posts, questions, topics..."
                    className="w-full text-sm pl-9 pr-3 py-3 rounded-lg border border-gray-200 dark:border-[#35363a] bg-white dark:bg-[#111111] text-black dark:text-white focus:outline-none focus:ring-1 focus:ring-gray-400 placeholder:text-gray-400"
                />
            </div>

            {/* Filters + Create button */}
            <div className="flex items-center justify-between mb-4">
                <div className="inline-flex rounded-lg p-1 bg-[#e5e7eb] dark:bg-[#222222]">
                    {filters.map(f => (
                        <button
                            key={f.key}
                            className={`px-3 py-1.5 rounded-md text-xs font-medium cursor-pointer transition-colors ${
                                activeFilter === f.key
                                    ? 'bg-white dark:bg-[#333333] text-black dark:text-white'
                                    : 'text-[#4b5563] dark:text-[#9ca3af] hover:text-black dark:hover:text-white'
                            }`}
                            onClick={() => setActiveFilter(f.key)}
                        >
                            {f.label}
                        </button>
                    ))}
                </div>
                <div className="flex items-center gap-2">
                    {(userRole === 'mentor' || userRole === 'master') && (
                        <button
                            onClick={() => router.push('/network/mentor-dashboard')}
                            className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg border border-purple-300 dark:border-purple-700 text-purple-700 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20 cursor-pointer transition-colors"
                        >
                            <ShieldCheck className="w-4 h-4" />
                            <span className="hidden sm:inline">Review</span>
                        </button>
                    )}
                    <button
                        onClick={() => router.push('/network/create')}
                        className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg bg-black dark:bg-white text-white dark:text-black hover:opacity-90 cursor-pointer"
                    >
                        <Plus className="w-4 h-4" />
                        <span className="hidden sm:inline">Create Post</span>
                    </button>
                </div>
            </div>

            {/* Posts list */}
            {isLoading ? (
                <div className="space-y-4">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="rounded-lg p-4 border border-gray-200 dark:border-[#35363a] bg-white dark:bg-[#111111] animate-pulse">
                            <div className="flex items-center gap-2 mb-3">
                                <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-[#333333]" />
                                <div className="h-4 w-24 bg-gray-200 dark:bg-[#333333] rounded" />
                            </div>
                            <div className="h-5 w-3/4 bg-gray-200 dark:bg-[#333333] rounded mb-2" />
                            <div className="h-4 w-1/2 bg-gray-200 dark:bg-[#333333] rounded" />
                        </div>
                    ))}
                </div>
            ) : posts.length > 0 ? (
                <div className="space-y-3">
                    {posts.map(post => (
                        <PostCard key={post.id} post={post} onVote={handleVote} />
                    ))}
                </div>
            ) : (
                <div className="text-center py-12">
                    <h3 className="text-lg font-medium text-gray-600 dark:text-gray-400 mb-2">
                        No posts yet
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-500 mb-4">
                        Be the first to share your knowledge!
                    </p>
                    <button
                        onClick={() => router.push('/network/create')}
                        className="px-6 py-3 text-sm font-medium rounded-full bg-black dark:bg-white text-white dark:text-black hover:opacity-90 cursor-pointer"
                    >
                        Create a post
                    </button>
                </div>
            )}
        </div>
    );
}
