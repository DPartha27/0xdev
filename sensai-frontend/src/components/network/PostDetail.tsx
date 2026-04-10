"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { NetworkPost, NetworkComment } from "@/types/network";
import BadgeIndicator from "./BadgeIndicator";
import CommentSection from "./CommentSection";
import { ArrowLeft, ChevronUp, ChevronDown, MessageSquare, HelpCircle, BarChart3, Code, Lightbulb, BookOpen, Eye, Pin, Trash2, Shield, Sparkles, Loader2, Pencil, X, Check } from "lucide-react";

interface PostDetailProps {
    postId: number;
}

const postTypeConfig: Record<string, { icon: React.ElementType; label: string; color: string }> = {
    thread: { icon: MessageSquare, label: 'Thread', color: 'text-blue-500' },
    question: { icon: HelpCircle, label: 'Question', color: 'text-green-500' },
    poll: { icon: BarChart3, label: 'Poll', color: 'text-purple-500' },
    code_snippet: { icon: Code, label: 'Code Snippet', color: 'text-orange-500' },
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

export default function PostDetail({ postId }: PostDetailProps) {
    const router = useRouter();
    const { user } = useAuth();
    const [post, setPost] = useState<NetworkPost | null>(null);
    const [comments, setComments] = useState<NetworkComment[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [aiAnswer, setAiAnswer] = useState<any>(null);
    const [aiAnswerLoading, setAiAnswerLoading] = useState(false);

    // Edit mode state
    const [isEditing, setIsEditing] = useState(false);
    const [editTitle, setEditTitle] = useState("");
    const [editContent, setEditContent] = useState("");
    const [editCode, setEditCode] = useState("");
    const [editLanguage, setEditLanguage] = useState("");
    const [editTags, setEditTags] = useState<string[]>([]);
    const [editTagInput, setEditTagInput] = useState("");
    const [isSaving, setIsSaving] = useState(false);

    const fetchPost = useCallback(async () => {
        try {
            const params = user?.id ? `?user_id=${user.id}` : '';
            const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/posts/${postId}${params}`);
            if (res.ok) {
                setPost(await res.json());
            }
        } catch (err) {
            console.error('Error fetching post:', err);
        }
    }, [postId, user?.id]);

    const fetchComments = useCallback(async () => {
        try {
            const params = user?.id ? `?user_id=${user.id}` : '';
            const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/posts/${postId}/comments${params}`);
            if (res.ok) {
                setComments(await res.json());
            }
        } catch (err) {
            console.error('Error fetching comments:', err);
        }
    }, [postId, user?.id]);

    useEffect(() => {
        Promise.all([fetchPost(), fetchComments()]).finally(() => setIsLoading(false));
    }, [fetchPost, fetchComments]);

    const handleVote = async (voteType: string) => {
        if (!user?.id || !post) return;
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/posts/${postId}/vote`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: user.id, vote_type: voteType }),
            });
            if (res.ok) {
                await fetchPost();
            }
        } catch (err) {
            console.error('Error voting:', err);
        }
    };

    const handlePollVote = async (optionId: number) => {
        if (!user?.id) return;
        try {
            await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/polls/${postId}/vote`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: user.id, option_id: optionId }),
            });
            await fetchPost();
        } catch (err) {
            console.error('Error voting on poll:', err);
        }
    };

    const handleDelete = async () => {
        if (!confirm('Are you sure you want to delete this post?')) return;
        try {
            await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/posts/${postId}`, { method: 'DELETE' });
            router.push('/network');
        } catch (err) {
            console.error('Error deleting post:', err);
        }
    };

    const handlePin = async () => {
        try {
            await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/posts/${postId}/pin`, { method: 'POST' });
            await fetchPost();
        } catch (err) {
            console.error('Error pinning post:', err);
        }
    };

    const handleAiAnswer = async () => {
        if (!post) return;
        setAiAnswerLoading(true);
        setAiAnswer(null);
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/ai/suggest-answer`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    post_type: post.post_type,
                    title: post.title,
                    content_text: post.content_text,
                    code_content: post.code_content,
                }),
            });
            if (res.ok) {
                setAiAnswer(await res.json());
            }
        } catch (err) {
            console.error('AI answer failed:', err);
        } finally {
            setAiAnswerLoading(false);
        }
    };

    const startEditing = () => {
        if (!post) return;
        setEditTitle(post.title);
        setEditContent(post.content_text || "");
        setEditCode(post.code_content || "");
        setEditLanguage(post.coding_language || "javascript");
        setEditTags(post.tags.map(t => t.name));
        setIsEditing(true);
    };

    const cancelEditing = () => {
        setIsEditing(false);
        setEditTagInput("");
    };

    const saveEdit = async () => {
        if (!editTitle.trim()) return;
        setIsSaving(true);
        try {
            const body: any = {
                title: editTitle.trim(),
                content_text: editContent || null,
                tags: editTags,
            };
            if (editCode.trim()) {
                body.code_content = editCode;
                body.coding_language = editLanguage;
            } else {
                body.code_content = "";
                body.coding_language = null;
            }

            const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/posts/${postId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            if (res.ok) {
                setIsEditing(false);
                await fetchPost();
            }
        } catch (err) {
            console.error('Error saving edit:', err);
        } finally {
            setIsSaving(false);
        }
    };

    const addEditTag = (name: string) => {
        const trimmed = name.trim();
        if (trimmed && !editTags.includes(trimmed)) {
            setEditTags([...editTags, trimmed]);
        }
        setEditTagInput("");
    };

    if (isLoading) {
        return (
            <div className="max-w-3xl mx-auto px-4 sm:px-8 pt-6 pb-12">
                <div className="animate-pulse space-y-4">
                    <div className="h-6 w-32 bg-gray-200 dark:bg-[#333333] rounded" />
                    <div className="h-8 w-3/4 bg-gray-200 dark:bg-[#333333] rounded" />
                    <div className="h-40 w-full bg-gray-200 dark:bg-[#333333] rounded" />
                </div>
            </div>
        );
    }

    if (!post) {
        return (
            <div className="max-w-3xl mx-auto px-4 sm:px-8 pt-6 pb-12 text-center">
                <h2 className="text-xl font-medium text-gray-600 dark:text-gray-400">Post not found</h2>
                <button onClick={() => router.push('/network')} className="mt-4 text-sm text-gray-500 hover:text-black dark:hover:text-white cursor-pointer">
                    Back to Network
                </button>
            </div>
        );
    }

    const config = postTypeConfig[post.post_type] || postTypeConfig.thread;
    const TypeIcon = config.icon;
    const authorName = `${post.author.first_name} ${post.author.last_name}`.trim() || post.author.email;
    const initials = post.author.first_name ? post.author.first_name.charAt(0).toUpperCase() : 'U';
    const isMentor = post.author.network_role === 'mentor';
    const isAuthor = user?.id === post.author.id;
    const totalVotes = post.poll_options?.reduce((sum, o) => sum + o.vote_count, 0) || 0;

    return (
        <div className="max-w-3xl mx-auto px-4 sm:px-8 pt-6 pb-12">
            {/* Back */}
            <button
                onClick={() => router.push('/network')}
                className="flex items-center gap-1 text-sm text-gray-500 hover:text-black dark:hover:text-white mb-6 cursor-pointer"
            >
                <ArrowLeft className="w-4 h-4" />
                Back to Network
            </button>

            {/* Post header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-purple-700 flex items-center justify-center flex-shrink-0">
                        <span className="text-white text-sm font-medium">{initials}</span>
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <span className="font-medium text-black dark:text-white">{authorName}</span>
                            <BadgeIndicator tier={post.author.badge_tier} size="md" />
                            {isMentor && <Shield className="w-3.5 h-3.5 text-blue-500" />}
                        </div>
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                            <TypeIcon className={`w-3.5 h-3.5 ${config.color}`} />
                            <span>{config.label}</span>
                            <span>&middot;</span>
                            <span>{timeAgo(post.created_at)}</span>
                            <span>&middot;</span>
                            <Eye className="w-3 h-3" />
                            <span>{post.view_count}</span>
                        </div>
                    </div>
                </div>

                {/* Admin actions */}
                {(isAuthor || isMentor) && !isEditing && (
                    <div className="flex items-center gap-2">
                        {isAuthor && (
                            <button onClick={startEditing} className="p-2 text-gray-400 hover:text-blue-500 cursor-pointer" title="Edit post">
                                <Pencil className="w-4 h-4" />
                            </button>
                        )}
                        <button onClick={handlePin} className="p-2 text-gray-400 hover:text-yellow-500 cursor-pointer" title="Pin post">
                            <Pin className={`w-4 h-4 ${post.is_pinned ? 'text-yellow-500' : ''}`} />
                        </button>
                        <button onClick={handleDelete} className="p-2 text-gray-400 hover:text-red-500 cursor-pointer" title="Delete post">
                            <Trash2 className="w-4 h-4" />
                        </button>
                    </div>
                )}
            </div>

            {/* Title */}
            {isEditing ? (
                <input
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    className="w-full text-2xl font-bold p-2 mb-4 rounded-lg border border-gray-300 dark:border-[#35363a] bg-white dark:bg-[#111111] text-black dark:text-white focus:outline-none focus:ring-1 focus:ring-gray-400"
                />
            ) : (
                <h1 className="text-2xl font-bold text-black dark:text-white mb-4">{post.title}</h1>
            )}

            {/* Content */}
            {isEditing ? (
                <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className="w-full text-sm p-3 mb-4 rounded-lg border border-gray-300 dark:border-[#35363a] bg-white dark:bg-[#111111] text-black dark:text-white resize-none focus:outline-none focus:ring-1 focus:ring-gray-400"
                    rows={6}
                    placeholder="Post content..."
                />
            ) : post.content_text ? (
                <div className="text-base text-gray-700 dark:text-gray-300 mb-4 whitespace-pre-wrap leading-relaxed">
                    {post.content_text}
                </div>
            ) : null}

            {/* Code content */}
            {isEditing ? (
                <div className="mb-4">
                    <div className="flex items-center justify-between mb-1">
                        <label className="text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-1.5">
                            <Code className="w-3.5 h-3.5" />
                            Code Snippet <span className="text-xs text-gray-400 font-normal">(optional)</span>
                        </label>
                        <select
                            value={editLanguage}
                            onChange={(e) => setEditLanguage(e.target.value)}
                            className="text-xs bg-gray-100 dark:bg-[#222222] border border-gray-300 dark:border-[#35363a] rounded px-2 py-1 text-black dark:text-white"
                        >
                            <option value="javascript">JavaScript</option>
                            <option value="python">Python</option>
                            <option value="java">Java</option>
                            <option value="typescript">TypeScript</option>
                            <option value="cpp">C++</option>
                            <option value="html">HTML</option>
                            <option value="css">CSS</option>
                            <option value="sql">SQL</option>
                        </select>
                    </div>
                    <textarea
                        value={editCode}
                        onChange={(e) => setEditCode(e.target.value)}
                        className="w-full text-sm p-3 rounded-lg border font-mono border-gray-200 dark:border-[#35363a] bg-gray-50 dark:bg-[#1a1a1a] text-black dark:text-white resize-none focus:outline-none focus:ring-1 focus:ring-gray-400"
                        rows={8}
                        placeholder="Paste code here..."
                    />
                </div>
            ) : post.code_content ? (
                <div className="mb-4">
                    <div className="flex items-center justify-between px-3 py-1.5 bg-gray-200 dark:bg-[#2a2a2a] rounded-t-lg">
                        <span className="text-xs font-medium text-gray-600 dark:text-gray-400">{post.coding_language || 'code'}</span>
                    </div>
                    <pre className="text-sm bg-gray-100 dark:bg-[#1a1a1a] rounded-b-lg p-4 overflow-x-auto border border-gray-200 dark:border-[#35363a]">
                        <code>{post.code_content}</code>
                    </pre>
                </div>
            ) : null}

            {/* Poll */}
            {post.post_type === 'poll' && post.poll_options && (
                <div className="mb-4 space-y-2">
                    {post.poll_options.map(opt => {
                        const pct = totalVotes > 0 ? Math.round((opt.vote_count / totalVotes) * 100) : 0;
                        return (
                            <button
                                key={opt.id}
                                onClick={() => handlePollVote(opt.id)}
                                className={`w-full text-left p-3 rounded-lg border cursor-pointer transition-colors relative overflow-hidden ${
                                    opt.user_voted
                                        ? 'border-black dark:border-white'
                                        : 'border-gray-200 dark:border-[#35363a] hover:border-gray-400 dark:hover:border-gray-600'
                                }`}
                            >
                                <div
                                    className="absolute inset-0 bg-gray-100 dark:bg-[#1a1a1a] transition-all"
                                    style={{ width: `${pct}%` }}
                                />
                                <div className="relative flex justify-between items-center">
                                    <span className="text-sm text-black dark:text-white">{opt.option_text}</span>
                                    <span className="text-xs text-gray-500">{pct}% ({opt.vote_count})</span>
                                </div>
                            </button>
                        );
                    })}
                    <p className="text-xs text-gray-400">{totalVotes} total votes</p>
                </div>
            )}

            {/* Tags */}
            {isEditing ? (
                <div className="mb-4">
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 block">Tags</label>
                    <div className="flex flex-wrap gap-1.5 mb-2">
                        {editTags.map(tag => (
                            <span key={tag} className="flex items-center gap-1 text-xs rounded-full px-2.5 py-1 bg-gray-100 dark:bg-[#222222] text-gray-700 dark:text-gray-300">
                                {tag}
                                <button onClick={() => setEditTags(editTags.filter(t => t !== tag))} className="cursor-pointer hover:text-red-500">
                                    <X className="w-3 h-3" />
                                </button>
                            </span>
                        ))}
                    </div>
                    <input
                        value={editTagInput}
                        onChange={(e) => setEditTagInput(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter' && editTagInput.trim()) { e.preventDefault(); addEditTag(editTagInput); } }}
                        placeholder="Type a tag and press Enter..."
                        className="w-full text-sm p-2 rounded-lg border border-gray-200 dark:border-[#35363a] bg-white dark:bg-[#111111] text-black dark:text-white focus:outline-none focus:ring-1 focus:ring-gray-400"
                    />
                </div>
            ) : post.tags.length > 0 ? (
                <div className="flex flex-wrap gap-1.5 mb-4">
                    {post.tags.map(tag => (
                        <span key={tag.id} className="text-xs rounded-full px-2.5 py-1 bg-gray-100 dark:bg-[#222222] text-gray-600 dark:text-gray-400">
                            {tag.name}
                        </span>
                    ))}
                </div>
            ) : null}

            {/* Save/Cancel bar for edit mode */}
            {isEditing && (
                <div className="flex gap-2 mb-4">
                    <button
                        onClick={saveEdit}
                        disabled={isSaving || !editTitle.trim()}
                        className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg bg-black dark:bg-white text-white dark:text-black hover:opacity-90 disabled:opacity-50 cursor-pointer"
                    >
                        {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                        {isSaving ? 'Saving...' : 'Save Changes'}
                    </button>
                    <button
                        onClick={cancelEditing}
                        className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg text-gray-500 hover:text-black dark:hover:text-white cursor-pointer"
                    >
                        <X className="w-4 h-4" />
                        Cancel
                    </button>
                </div>
            )}

            {/* Vote bar */}
            <div className="flex items-center gap-4 py-3 border-t border-b border-gray-200 dark:border-[#35363a] mb-2">
                <div className="flex items-center gap-1">
                    <button
                        className={`p-1 rounded hover:bg-gray-100 dark:hover:bg-[#222222] cursor-pointer ${post.user_vote === 'upvote' ? 'text-green-500' : 'text-gray-500'}`}
                        onClick={() => handleVote('upvote')}
                    >
                        <ChevronUp className="w-6 h-6" />
                    </button>
                    <span className="text-base font-semibold text-black dark:text-white min-w-[24px] text-center">
                        {post.upvote_count - post.downvote_count}
                    </span>
                    <button
                        className={`p-1 rounded hover:bg-gray-100 dark:hover:bg-[#222222] cursor-pointer ${post.user_vote === 'downvote' ? 'text-red-500' : 'text-gray-500'}`}
                        onClick={() => handleVote('downvote')}
                    >
                        <ChevronDown className="w-6 h-6" />
                    </button>
                </div>
                <div className="flex items-center gap-1 text-sm text-gray-500">
                    <MessageSquare className="w-4 h-4" />
                    <span>{post.reply_count} comments</span>
                </div>
            </div>

            {/* AI Suggest Answer — only for question posts */}
            {post.post_type === 'question' && (
                <div className="my-4">
                    {!aiAnswer && (
                        <button
                            onClick={handleAiAnswer}
                            disabled={aiAnswerLoading}
                            className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-dashed border-purple-300 dark:border-purple-700 text-purple-700 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/20 disabled:opacity-50 cursor-pointer transition-colors"
                        >
                            {aiAnswerLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                            {aiAnswerLoading ? 'AI is thinking...' : 'Get AI-suggested answer'}
                        </button>
                    )}
                    {aiAnswer && (
                        <div className="p-4 rounded-lg border border-purple-200 dark:border-purple-800 bg-purple-50/50 dark:bg-purple-900/10">
                            <div className="flex items-center gap-2 mb-2">
                                <Sparkles className="w-4 h-4 text-purple-500" />
                                <span className="text-sm font-semibold text-purple-700 dark:text-purple-400">AI-Suggested Answer</span>
                            </div>
                            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap mb-3">{aiAnswer.answer}</p>
                            {aiAnswer.code_example && (
                                <div>
                                    <div className="flex items-center justify-between px-3 py-1 bg-gray-200 dark:bg-[#2a2a2a] rounded-t-lg">
                                        <span className="text-xs font-medium text-gray-600 dark:text-gray-400">{aiAnswer.coding_language || 'code'}</span>
                                    </div>
                                    <pre className="text-sm bg-gray-100 dark:bg-[#1a1a1a] rounded-b-lg p-3 overflow-x-auto border border-gray-200 dark:border-[#35363a]">
                                        <code>{aiAnswer.code_example}</code>
                                    </pre>
                                </div>
                            )}
                            <button
                                onClick={() => setAiAnswer(null)}
                                className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 mt-2 cursor-pointer"
                            >
                                Dismiss
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* Comments */}
            <CommentSection
                postId={postId}
                comments={comments}
                onCommentAdded={() => { fetchComments(); fetchPost(); }}
            />
        </div>
    );
}
