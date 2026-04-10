"use client";

import { useRouter } from "next/navigation";
import { NetworkPost } from "@/types/network";
import BadgeIndicator from "./BadgeIndicator";
import { MessageSquare, HelpCircle, BarChart3, Code, Lightbulb, BookOpen, ChevronUp, ChevronDown, Pin } from "lucide-react";

interface PostCardProps {
    post: NetworkPost;
    onVote: (postId: number, voteType: string) => void;
}

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
    // SQLite stores UTC timestamps without a Z suffix — append it so JS parses as UTC
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

export default function PostCard({ post, onVote }: PostCardProps) {
    const router = useRouter();
    const config = postTypeConfig[post.post_type] || postTypeConfig.thread;
    const TypeIcon = config.icon;
    const authorName = `${post.author.first_name} ${post.author.last_name}`.trim() || post.author.email;
    const initials = post.author.first_name ? post.author.first_name.charAt(0).toUpperCase() : post.author.email.charAt(0).toUpperCase();

    const preview = post.content_text
        ? post.content_text.substring(0, 150) + (post.content_text.length > 150 ? '...' : '')
        : post.code_content
            ? post.code_content.substring(0, 100) + '...'
            : '';

    return (
        <div
            className="rounded-lg p-4 cursor-pointer transition-colors border border-gray-200 dark:border-[#35363a] bg-white dark:bg-[#111111] hover:bg-gray-50 dark:hover:bg-[#1a1a1a]"
            onClick={() => router.push(`/network/post/${post.id}`)}
        >
            {/* Header: author info + time */}
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-purple-700 flex items-center justify-center flex-shrink-0">
                        <span className="text-white text-xs font-medium">{initials}</span>
                    </div>
                    <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-sm font-medium text-black dark:text-white">{authorName}</span>
                        <BadgeIndicator tier={post.author.badge_tier} size="sm" />
                    </div>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
                    {post.is_pinned && <Pin className="w-3 h-3 text-yellow-500" />}
                    {timeAgo(post.created_at)}
                    {post.is_edited && <span className="text-gray-400 italic">(edited)</span>}
                </div>
            </div>

            {/* Post type badge */}
            <div className="flex items-center gap-1 mb-2">
                <TypeIcon className={`w-3.5 h-3.5 ${config.color}`} />
                <span className={`text-xs ${config.color}`}>{config.label}</span>
            </div>

            {/* Title */}
            <h3 className="text-base font-semibold text-black dark:text-white mb-1 line-clamp-2">{post.title}</h3>

            {/* Preview */}
            {preview && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">{preview}</p>
            )}

            {/* Tags */}
            {post.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-3">
                    {post.tags.map(tag => (
                        <span
                            key={tag.id}
                            className="text-xs rounded-full px-2 py-0.5 bg-gray-100 dark:bg-[#222222] text-gray-600 dark:text-gray-400"
                            onClick={(e) => e.stopPropagation()}
                        >
                            {tag.name}
                        </span>
                    ))}
                </div>
            )}

            {/* Footer: votes + comments */}
            <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                    <button
                        className={`p-0.5 rounded hover:bg-gray-100 dark:hover:bg-[#222222] transition-colors cursor-pointer ${post.user_vote === 'upvote' ? 'text-green-500' : ''}`}
                        onClick={() => onVote(post.id, 'upvote')}
                    >
                        <ChevronUp className="w-5 h-5" />
                    </button>
                    <span className="text-sm font-medium min-w-[20px] text-center">{post.upvote_count - post.downvote_count}</span>
                    <button
                        className={`p-0.5 rounded hover:bg-gray-100 dark:hover:bg-[#222222] transition-colors cursor-pointer ${post.user_vote === 'downvote' ? 'text-red-500' : ''}`}
                        onClick={() => onVote(post.id, 'downvote')}
                    >
                        <ChevronDown className="w-5 h-5" />
                    </button>
                </div>
                <div className="flex items-center gap-1">
                    <MessageSquare className="w-4 h-4" />
                    <span>{post.reply_count} {post.reply_count === 1 ? 'comment' : 'comments'}</span>
                </div>
            </div>
        </div>
    );
}
