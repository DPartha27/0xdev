"use client";

import { useState } from "react";
import { NetworkComment } from "@/types/network";
import BadgeIndicator from "./BadgeIndicator";
import { ChevronUp, Reply, Code, Bot, Trash2, AlertTriangle } from "lucide-react";

interface CommentCardProps {
    comment: NetworkComment;
    currentUserId?: number;
    onVote: (commentId: number, voteType: string) => void;
    onReply: (commentId: number, content: string, codeContent?: string, codingLanguage?: string) => Promise<boolean>;
    onDelete?: (commentId: number) => void;
    depth?: number;
}

function timeAgo(dateString: string): string {
    const now = new Date();
    const normalized = dateString.endsWith('Z') ? dateString : dateString + 'Z';
    const date = new Date(normalized);
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    if (seconds < 0) return 'now';
    if (seconds < 60) return 'now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
    return `${Math.floor(seconds / 86400)}d`;
}

export default function CommentCard({ comment, currentUserId, onVote, onReply, onDelete, depth = 0 }: CommentCardProps) {
    const [showReply, setShowReply] = useState(false);
    const [replyText, setReplyText] = useState("");
    const [isCodeReply, setIsCodeReply] = useState(false);
    const [codeLanguage, setCodeLanguage] = useState("javascript");
    const [replyError, setReplyError] = useState<string | null>(null);
    const [isSubmittingReply, setIsSubmittingReply] = useState(false);
    const isOwner = currentUserId === comment.author.id;
    const isBot = comment.author.email === "sensai-bot@sensai.internal";
    const authorName = isBot ? "SensAI Bot" : (`${comment.author.first_name} ${comment.author.last_name}`.trim() || comment.author.email);
    const initials = isBot ? "" : (comment.author.first_name ? comment.author.first_name.charAt(0).toUpperCase() : 'U');

    const handleSubmitReply = async () => {
        if (!replyText.trim()) return;
        setReplyError(null);
        setIsSubmittingReply(true);
        try {
            let success: boolean;
            if (isCodeReply) {
                success = await onReply(comment.id, "Code reply", replyText, codeLanguage);
            } else {
                success = await onReply(comment.id, replyText);
            }
            if (success) {
                setReplyText("");
                setShowReply(false);
                setIsCodeReply(false);
            }
        } catch (err: any) {
            setReplyError(err.message || "Your reply doesn't seem relevant to this post.");
        } finally {
            setIsSubmittingReply(false);
        }
    };

    return (
        <div className={`${depth > 0 ? 'ml-6 pl-4 border-l-2 border-gray-200 dark:border-[#35363a]' : ''}`}>
            <div className="py-3">
                {/* Author line */}
                <div className="flex items-center gap-2 mb-1.5">
                    {isBot ? (
                        <div className="w-6 h-6 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center flex-shrink-0">
                            <Bot className="w-3.5 h-3.5 text-white" />
                        </div>
                    ) : (
                        <div className="w-6 h-6 rounded-full bg-purple-700 flex items-center justify-center flex-shrink-0">
                            <span className="text-white text-[10px] font-medium">{initials}</span>
                        </div>
                    )}
                    <span className={`text-sm font-medium ${isBot ? 'text-purple-600 dark:text-purple-400' : 'text-black dark:text-white'}`}>{authorName}</span>
                    {isBot ? (
                        <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-[10px] font-medium bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 border border-purple-200 dark:border-purple-800">
                            <Bot className="w-2.5 h-2.5" />
                            AI
                        </span>
                    ) : (
                        <BadgeIndicator tier={comment.author.badge_tier} size="sm" />
                    )}
                    <span className="text-xs text-gray-400">{timeAgo(comment.created_at)}</span>
                </div>

                {/* Comment content */}
                <div className="ml-8">
                    {comment.code_content ? (
                        <div className="mt-1">
                            <p className="text-sm text-gray-700 dark:text-gray-300 mb-1">{comment.content}</p>
                            <pre className="text-sm bg-gray-100 dark:bg-[#1a1a1a] rounded-md p-3 overflow-x-auto border border-gray-200 dark:border-[#35363a]">
                                <code>{comment.code_content}</code>
                            </pre>
                        </div>
                    ) : (
                        <p className="text-sm text-gray-700 dark:text-gray-300">{comment.content}</p>
                    )}
                    {comment.image_url && (
                        <img
                            src={`${process.env.NEXT_PUBLIC_BACKEND_URL}${comment.image_url}`}
                            alt="Comment image"
                            className="mt-2 max-h-48 rounded-lg border border-gray-200 dark:border-[#35363a]"
                        />
                    )}

                    {/* Actions */}
                    <div className="flex items-center gap-3 mt-1.5">
                        <button
                            className={`flex items-center gap-0.5 text-xs cursor-pointer ${comment.user_vote === 'upvote' ? 'text-green-500' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
                            onClick={() => onVote(comment.id, 'upvote')}
                        >
                            <ChevronUp className="w-4 h-4" />
                            <span>{comment.upvote_count || ''}</span>
                        </button>
                        {depth < 1 && (
                            <button
                                className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 cursor-pointer"
                                onClick={() => { setShowReply(!showReply); setReplyError(null); }}
                            >
                                <Reply className="w-3.5 h-3.5" />
                                Reply
                            </button>
                        )}
                        {isOwner && onDelete && (
                            <button
                                className="flex items-center gap-1 text-xs text-gray-400 hover:text-red-500 cursor-pointer"
                                onClick={() => onDelete(comment.id)}
                            >
                                <Trash2 className="w-3.5 h-3.5" />
                                Delete
                            </button>
                        )}
                    </div>

                    {/* Reply input */}
                    {showReply && (
                        <div className="mt-2 space-y-2">
                            <div className="flex items-center gap-2 mb-1">
                                <button
                                    className={`text-xs px-2 py-0.5 rounded cursor-pointer ${!isCodeReply ? 'bg-gray-200 dark:bg-[#333333] text-black dark:text-white' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}`}
                                    onClick={() => setIsCodeReply(false)}
                                >
                                    Text
                                </button>
                                <button
                                    className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded cursor-pointer ${isCodeReply ? 'bg-gray-200 dark:bg-[#333333] text-black dark:text-white' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}`}
                                    onClick={() => setIsCodeReply(true)}
                                >
                                    <Code className="w-3 h-3" />
                                    Code
                                </button>
                                {isCodeReply && (
                                    <select
                                        value={codeLanguage}
                                        onChange={(e) => setCodeLanguage(e.target.value)}
                                        className="text-xs bg-gray-100 dark:bg-[#222222] border border-gray-300 dark:border-[#35363a] rounded px-1 py-0.5 text-black dark:text-white"
                                    >
                                        <option value="javascript">JavaScript</option>
                                        <option value="python">Python</option>
                                        <option value="java">Java</option>
                                        <option value="typescript">TypeScript</option>
                                        <option value="cpp">C++</option>
                                        <option value="html">HTML</option>
                                        <option value="css">CSS</option>
                                    </select>
                                )}
                            </div>
                            {isCodeReply ? (
                                <textarea
                                    value={replyText}
                                    onChange={(e) => setReplyText(e.target.value)}
                                    placeholder="Write code..."
                                    className="w-full text-sm p-2 rounded-md border font-mono border-gray-300 dark:border-[#35363a] bg-gray-50 dark:bg-[#1a1a1a] text-black dark:text-white resize-none focus:outline-none focus:ring-1 focus:ring-gray-400"
                                    rows={4}
                                />
                            ) : (
                                <input
                                    value={replyText}
                                    onChange={(e) => setReplyText(e.target.value)}
                                    placeholder="Write a reply..."
                                    className="w-full text-sm p-2 rounded-md border border-gray-300 dark:border-[#35363a] bg-gray-50 dark:bg-[#1a1a1a] text-black dark:text-white focus:outline-none focus:ring-1 focus:ring-gray-400"
                                    onKeyDown={(e) => { if (e.key === 'Enter') handleSubmitReply(); }}
                                />
                            )}
                            {replyError && (
                                <div className="flex items-center gap-1.5 text-xs text-orange-600 dark:text-orange-400 p-2 rounded-lg bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800">
                                    <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                                    {replyError}
                                </div>
                            )}
                            <div className="flex gap-2">
                                <button
                                    onClick={handleSubmitReply}
                                    disabled={isSubmittingReply || !replyText.trim()}
                                    className="text-xs px-3 py-1 rounded-md bg-black dark:bg-white text-white dark:text-black cursor-pointer hover:opacity-90 disabled:opacity-50"
                                >
                                    {isSubmittingReply ? '...' : 'Reply'}
                                </button>
                                <button
                                    onClick={() => { setShowReply(false); setReplyText(""); setIsCodeReply(false); setReplyError(null); }}
                                    className="text-xs px-3 py-1 text-gray-500 cursor-pointer hover:text-gray-700 dark:hover:text-gray-300"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Nested replies */}
            {comment.replies && comment.replies.map(reply => (
                <CommentCard
                    key={reply.id}
                    comment={reply}
                    currentUserId={currentUserId}
                    onVote={onVote}
                    onReply={onReply}
                    onDelete={onDelete}
                    depth={depth + 1}
                />
            ))}
        </div>
    );
}
