"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { useSchools } from "@/lib/api";
import { NetworkPost } from "@/types/network";
import BadgeIndicator from "./BadgeIndicator";
import { ArrowLeft, Check, X, MessageSquare, HelpCircle, BarChart3, Code, Lightbulb, BookOpen, Loader2, ShieldCheck, Inbox } from "lucide-react";

const postTypeConfig: Record<string, { icon: React.ElementType; label: string; color: string }> = {
    thread: { icon: MessageSquare, label: 'Thread', color: 'text-blue-500' },
    question: { icon: HelpCircle, label: 'Question', color: 'text-green-500' },
    poll: { icon: BarChart3, label: 'Poll', color: 'text-purple-500' },
    code_snippet: { icon: Code, label: 'Code', color: 'text-orange-500' },
    tip: { icon: Lightbulb, label: 'Tip', color: 'text-yellow-500' },
    explanation: { icon: BookOpen, label: 'Explanation', color: 'text-cyan-500' },
};

function timeAgo(dateString: string): string {
    const now = new Date();
    const normalized = dateString.endsWith('Z') ? dateString : dateString + 'Z';
    const date = new Date(normalized);
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    if (seconds < 0) return 'just now';
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
    return date.toLocaleDateString();
}

export default function MentorDashboard() {
    const router = useRouter();
    const { user } = useAuth();
    const { schools } = useSchools();
    const [orgId, setOrgId] = useState<number | null>(null);
    const [posts, setPosts] = useState<NetworkPost[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState<number | null>(null);

    useEffect(() => {
        if (schools && schools.length > 0) {
            setOrgId(Number(schools[0].id));
        } else if (user?.id) {
            fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/users/${user.id}/orgs`)
                .then(res => res.ok ? res.json() : [])
                .then(data => setOrgId(data?.length > 0 ? Number(data[0].id) : 1))
                .catch(() => setOrgId(1));
        } else {
            setOrgId(1);
        }
    }, [schools, user?.id]);

    useEffect(() => {
        if (!orgId || !user?.id) return;
        setIsLoading(true);
        fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/posts/pending?org_id=${orgId}&mentor_id=${user.id}`)
            .then(res => {
                if (!res.ok) throw new Error('Failed to fetch');
                return res.json();
            })
            .then(data => setPosts(data))
            .catch(() => setPosts([]))
            .finally(() => setIsLoading(false));
    }, [orgId, user?.id]);

    const handleAction = async (postId: number, action: 'approve' | 'reject') => {
        if (!user?.id) return;
        setActionLoading(postId);
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/posts/${postId}/${action}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mentor_id: user.id }),
            });
            if (res.ok) {
                setPosts(prev => prev.filter(p => p.id !== postId));
            }
        } catch (err) {
            console.error(`Failed to ${action} post:`, err);
        } finally {
            setActionLoading(null);
        }
    };

    return (
        <div className="max-w-4xl mx-auto px-4 sm:px-8 pt-6 pb-12">
            <button
                onClick={() => router.push('/network')}
                className="flex items-center gap-1 text-sm text-gray-500 hover:text-black dark:hover:text-white mb-6 cursor-pointer"
            >
                <ArrowLeft className="w-4 h-4" />
                Back to SenseNet
            </button>

            <div className="flex items-center gap-3 mb-6">
                <ShieldCheck className="w-6 h-6 text-purple-500" />
                <h1 className="text-2xl font-semibold text-black dark:text-white">Mentor Dashboard</h1>
            </div>

            <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                Review and approve posts from community members. Medium-quality posts require your approval before they appear in the feed.
            </p>

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
            ) : posts.length === 0 ? (
                <div className="text-center py-16">
                    <Inbox className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-600 dark:text-gray-400 mb-2">
                        No posts pending review
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-500">
                        All caught up! New posts that need approval will appear here.
                    </p>
                </div>
            ) : (
                <div className="space-y-4">
                    <div className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                        {posts.length} post{posts.length !== 1 ? 's' : ''} pending review
                    </div>
                    {posts.map(post => {
                        const config = postTypeConfig[post.post_type] || postTypeConfig.thread;
                        const TypeIcon = config.icon;
                        const authorName = `${post.author.first_name} ${post.author.last_name}`.trim() || post.author.email;
                        const initials = post.author.first_name ? post.author.first_name.charAt(0).toUpperCase() : post.author.email.charAt(0).toUpperCase();
                        const preview = post.content_text
                            ? post.content_text.substring(0, 200) + (post.content_text.length > 200 ? '...' : '')
                            : post.code_content
                                ? post.code_content.substring(0, 150) + '...'
                                : '';

                        return (
                            <div key={post.id} className="rounded-lg border border-yellow-200 dark:border-yellow-800/50 bg-white dark:bg-[#111111] overflow-hidden">
                                {/* Pending banner */}
                                <div className="px-4 py-2 bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-200 dark:border-yellow-800/50 flex items-center justify-between">
                                    <span className="text-xs font-medium text-yellow-700 dark:text-yellow-400">Pending Approval</span>
                                    <span className="text-xs text-yellow-600 dark:text-yellow-500">{timeAgo(post.created_at)}</span>
                                </div>

                                <div className="p-4">
                                    {/* Author */}
                                    <div className="flex items-center gap-2 mb-3">
                                        <div className="w-8 h-8 rounded-full bg-purple-700 flex items-center justify-center flex-shrink-0">
                                            <span className="text-white text-xs font-medium">{initials}</span>
                                        </div>
                                        <div className="flex items-center gap-1.5">
                                            <span className="text-sm font-medium text-black dark:text-white">{authorName}</span>
                                            <BadgeIndicator tier={post.author.badge_tier} size="sm" />
                                        </div>
                                    </div>

                                    {/* Post type */}
                                    <div className="flex items-center gap-1 mb-2">
                                        <TypeIcon className={`w-3.5 h-3.5 ${config.color}`} />
                                        <span className={`text-xs ${config.color}`}>{config.label}</span>
                                    </div>

                                    {/* Title & preview */}
                                    <h3 className="text-base font-semibold text-black dark:text-white mb-1">{post.title}</h3>
                                    {preview && (
                                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">{preview}</p>
                                    )}

                                    {/* Code preview */}
                                    {post.code_content && (
                                        <pre className="text-xs p-3 mb-3 rounded-lg bg-gray-50 dark:bg-[#1a1a1a] border border-gray-200 dark:border-[#35363a] overflow-x-auto max-h-32">
                                            <code>{post.code_content.substring(0, 300)}{post.code_content.length > 300 ? '...' : ''}</code>
                                        </pre>
                                    )}

                                    {/* Tags */}
                                    {post.tags.length > 0 && (
                                        <div className="flex flex-wrap gap-1.5 mb-4">
                                            {post.tags.map(tag => (
                                                <span key={tag.id} className="text-xs rounded-full px-2 py-0.5 bg-gray-100 dark:bg-[#222222] text-gray-600 dark:text-gray-400">
                                                    {tag.name}
                                                </span>
                                            ))}
                                        </div>
                                    )}

                                    {/* Action buttons */}
                                    <div className="flex items-center gap-3 pt-3 border-t border-gray-100 dark:border-[#222222]">
                                        <button
                                            onClick={() => handleAction(post.id, 'approve')}
                                            disabled={actionLoading === post.id}
                                            className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg bg-green-600 hover:bg-green-700 text-white disabled:opacity-50 cursor-pointer transition-colors"
                                        >
                                            {actionLoading === post.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                                            Approve
                                        </button>
                                        <button
                                            onClick={() => handleAction(post.id, 'reject')}
                                            disabled={actionLoading === post.id}
                                            className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg bg-red-600 hover:bg-red-700 text-white disabled:opacity-50 cursor-pointer transition-colors"
                                        >
                                            {actionLoading === post.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <X className="w-4 h-4" />}
                                            Reject
                                        </button>
                                        <button
                                            onClick={() => router.push(`/network/post/${post.id}`)}
                                            className="px-4 py-2 text-sm font-medium rounded-lg text-gray-500 hover:text-black dark:hover:text-white cursor-pointer transition-colors"
                                        >
                                            View Full Post
                                        </button>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
