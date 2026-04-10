"use client";

import { useState, useMemo } from "react";
import { Search, TrendingUp, Sparkles } from "lucide-react";
import { useTrendingTags, useRecommendedTags } from "@/lib/api";

interface TagsSidebarProps {
    orgId: number | null;
    selectedTag: string | null;
    onTagSelect: (slug: string | null) => void;
}

export default function TagsSidebar({ orgId, selectedTag, onTagSelect }: TagsSidebarProps) {
    const [searchQuery, setSearchQuery] = useState("");
    const { tags: trendingTags, isLoading: trendingLoading } = useTrendingTags(orgId);
    const { tags: recommendedTags, isLoading: recommendedLoading } = useRecommendedTags(orgId);

    const filteredTrending = useMemo(() => {
        const tags = searchQuery
            ? trendingTags.filter(t => t.name.toLowerCase().includes(searchQuery.toLowerCase()))
            : trendingTags;
        return tags.slice(0, 5);
    }, [trendingTags, searchQuery]);

    const filteredRecommended = useMemo(() => {
        const tags = searchQuery
            ? recommendedTags.filter(t => t.name.toLowerCase().includes(searchQuery.toLowerCase()))
            : recommendedTags;
        return tags.slice(0, 5);
    }, [recommendedTags, searchQuery]);

    const handleTagClick = (slug: string) => {
        onTagSelect(selectedTag === slug ? null : slug);
    };

    return (
        <div className="space-y-6">
            {/* Search */}
            <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search tags..."
                    className="w-full text-sm pl-9 pr-3 py-2.5 rounded-lg border border-gray-200 dark:border-[#35363a] bg-white dark:bg-[#111111] text-black dark:text-white focus:outline-none focus:ring-1 focus:ring-gray-400 placeholder:text-gray-400"
                />
            </div>

            {/* Active filter indicator */}
            {selectedTag && (
                <div className="flex items-center justify-between p-2 rounded-lg bg-gray-100 dark:bg-[#1a1a1a]">
                    <span className="text-xs text-gray-600 dark:text-gray-400">Filtering by:</span>
                    <button
                        onClick={() => onTagSelect(null)}
                        className="text-xs px-2 py-0.5 rounded-full bg-black dark:bg-white text-white dark:text-black cursor-pointer hover:opacity-90"
                    >
                        {selectedTag} &times;
                    </button>
                </div>
            )}

            {/* Recommended Tags */}
            <div>
                <div className="flex items-center gap-1.5 mb-3">
                    <Sparkles className="w-4 h-4 text-yellow-500" />
                    <h3 className="text-sm font-semibold text-black dark:text-white">Recommended For You</h3>
                </div>
                {recommendedLoading ? (
                    <div className="space-y-2">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="h-7 rounded-full bg-gray-100 dark:bg-[#222222] animate-pulse w-24" />
                        ))}
                    </div>
                ) : filteredRecommended.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                        {filteredRecommended.map(tag => (
                            <button
                                key={tag.id}
                                onClick={() => handleTagClick(tag.slug)}
                                className={`text-xs rounded-full px-3 py-1.5 transition-colors cursor-pointer ${
                                    selectedTag === tag.slug
                                        ? 'bg-black dark:bg-white text-white dark:text-black'
                                        : 'bg-gray-100 dark:bg-[#222222] text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-[#333333]'
                                }`}
                            >
                                {tag.name}
                            </button>
                        ))}
                    </div>
                ) : (
                    <p className="text-xs text-gray-400">No recommendations yet. Start learning to get personalized tags!</p>
                )}
            </div>

            {/* Trending Tags */}
            <div>
                <div className="flex items-center gap-1.5 mb-3">
                    <TrendingUp className="w-4 h-4 text-green-500" />
                    <h3 className="text-sm font-semibold text-black dark:text-white">Trending Now</h3>
                </div>
                {trendingLoading ? (
                    <div className="space-y-2">
                        {[1, 2, 3, 4].map(i => (
                            <div key={i} className="h-7 rounded-full bg-gray-100 dark:bg-[#222222] animate-pulse w-20" />
                        ))}
                    </div>
                ) : filteredTrending.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                        {filteredTrending.map(tag => (
                            <button
                                key={tag.id}
                                onClick={() => handleTagClick(tag.slug)}
                                className={`text-xs rounded-full px-3 py-1.5 transition-colors cursor-pointer ${
                                    selectedTag === tag.slug
                                        ? 'bg-black dark:bg-white text-white dark:text-black'
                                        : 'bg-gray-100 dark:bg-[#222222] text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-[#333333]'
                                }`}
                            >
                                {tag.name}
                                {tag.recent_posts && (
                                    <span className="ml-1 text-[10px] opacity-60">{tag.recent_posts}</span>
                                )}
                            </button>
                        ))}
                    </div>
                ) : (
                    <p className="text-xs text-gray-400">No trending tags yet. Be the first to post!</p>
                )}
            </div>
        </div>
    );
}
