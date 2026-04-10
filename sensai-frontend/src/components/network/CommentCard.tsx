"use client";

import { useState } from "react";
import { NetworkComment } from "@/types/network";
import BadgeIndicator from "./BadgeIndicator";
import { ChevronUp, Reply, Code } from "lucide-react";

interface CommentCardProps {
    comment: NetworkComment;
    onVote: (commentId: number, voteType: string) => void;
    onReply: (commentId: number, content: string, codeContent?: string, codingLanguage?: string) => void;
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

export default function CommentCard({ comment, onVote, onReply, depth = 0 }: CommentCardProps) {
    const [showReply, setShowReply] = useState(false);
    const [replyText, setReplyText] = useState("");
    const [isCodeReply, setIsCodeReply] = useState(false);
    const [codeLanguage, setCodeLanguage] = useState("javascript");
    const authorName = `${comment.author.first_name} ${comment.author.last_name}`.trim() || comment.author.email;
    const initials = comment.author.first_name ? comment.author.first_name.charAt(0).toUpperCase() : 'U';

    const handleSubmitReply = () => {
        if (!replyText.trim()) return;
        if (isCodeReply) {
            onReply(comment.id, "Code reply", replyText, codeLanguage);
        } else {
            onReply(comment.id, replyText);
        }
        setReplyText("");
        setShowReply(false);
        setIsCodeReply(false);
    };

    return (
        <div className={`${depth > 0 ? 'ml-6 pl-4 border-l-2 border-gray-200 dark:border-[#35363a]' : ''}`}>
            <div className="py-3">
                {/* Author line */}
                <div className="flex items-center gap-2 mb-1.5">
                    <div className="w-6 h-6 rounded-full bg-purple-700 flex items-center justify-center flex-shrink-0">
                        <span className="text-white text-[10px] font-medium">{initials}</span>
                    </div>
                    <span className="text-sm font-medium text-black dark:text-white">{authorName}</span>
                    <BadgeIndicator tier={comment.author.badge_tier} size="sm" />
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
                                onClick={() => setShowReply(!showReply)}
                            >
                                <Reply className="w-3.5 h-3.5" />
                                Reply
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
                            <div className="flex gap-2">
                                <button
                                    onClick={handleSubmitReply}
                                    className="text-xs px-3 py-1 rounded-md bg-black dark:bg-white text-white dark:text-black cursor-pointer hover:opacity-90"
                                >
                                    Reply
                                </button>
                                <button
                                    onClick={() => { setShowReply(false); setReplyText(""); setIsCodeReply(false); }}
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
                    onVote={onVote}
                    onReply={onReply}
                    depth={depth + 1}
                />
            ))}
        </div>
    );
}
