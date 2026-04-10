"use client";

import { useState } from "react";
import { NetworkComment } from "@/types/network";
import CommentCard from "./CommentCard";
import { Code } from "lucide-react";
import { useAuth } from "@/lib/auth";

interface CommentSectionProps {
    postId: number;
    comments: NetworkComment[];
    onCommentAdded: () => void;
}

export default function CommentSection({ postId, comments, onCommentAdded }: CommentSectionProps) {
    const { user } = useAuth();
    const [newComment, setNewComment] = useState("");
    const [isCodeMode, setIsCodeMode] = useState(false);
    const [codeLanguage, setCodeLanguage] = useState("javascript");
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async () => {
        if (!newComment.trim() || !user?.id) return;
        setIsSubmitting(true);

        try {
            const body: any = { author_id: user.id };
            if (isCodeMode) {
                body.content = "Code snippet";
                body.code_content = newComment;
                body.coding_language = codeLanguage;
            } else {
                body.content = newComment;
            }

            const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/posts/${postId}/comments`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });

            if (res.ok) {
                setNewComment("");
                setIsCodeMode(false);
                onCommentAdded();
            }
        } catch (err) {
            console.error('Error posting comment:', err);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleVote = async (commentId: number, voteType: string) => {
        if (!user?.id) return;
        await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/comments/${commentId}/vote`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: user.id, vote_type: voteType }),
        });
        onCommentAdded();
    };

    const handleReply = async (parentCommentId: number, content: string, codeContent?: string, codingLanguage?: string) => {
        if (!user?.id) return;
        const body: any = { author_id: user.id, content, parent_comment_id: parentCommentId };
        if (codeContent) {
            body.code_content = codeContent;
            body.coding_language = codingLanguage;
        }

        await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/posts/${postId}/comments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        onCommentAdded();
    };

    return (
        <div className="mt-6">
            <h3 className="text-lg font-semibold text-black dark:text-white mb-4">
                Comments ({comments.length})
            </h3>

            {/* Comment list */}
            <div className="space-y-1 mb-6">
                {comments.map(comment => (
                    <CommentCard
                        key={comment.id}
                        comment={comment}
                        onVote={handleVote}
                        onReply={handleReply}
                    />
                ))}
                {comments.length === 0 && (
                    <p className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">
                        No comments yet. Be the first to comment!
                    </p>
                )}
            </div>

            {/* New comment input */}
            <div className="border-t border-gray-200 dark:border-[#35363a] pt-4">
                <div className="flex items-center gap-2 mb-2">
                    <button
                        className={`text-xs px-2 py-0.5 rounded cursor-pointer ${!isCodeMode ? 'bg-gray-200 dark:bg-[#333333] text-black dark:text-white' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}`}
                        onClick={() => setIsCodeMode(false)}
                    >
                        Text
                    </button>
                    <button
                        className={`flex items-center gap-1 text-xs px-2 py-0.5 rounded cursor-pointer ${isCodeMode ? 'bg-gray-200 dark:bg-[#333333] text-black dark:text-white' : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'}`}
                        onClick={() => setIsCodeMode(true)}
                    >
                        <Code className="w-3 h-3" />
                        Code
                    </button>
                    {isCodeMode && (
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
                <div className="flex gap-2">
                    {isCodeMode ? (
                        <textarea
                            value={newComment}
                            onChange={(e) => setNewComment(e.target.value)}
                            placeholder="Write code..."
                            className="flex-1 text-sm p-3 rounded-lg border font-mono border-gray-300 dark:border-[#35363a] bg-gray-50 dark:bg-[#1a1a1a] text-black dark:text-white resize-none focus:outline-none focus:ring-1 focus:ring-gray-400"
                            rows={4}
                        />
                    ) : (
                        <input
                            value={newComment}
                            onChange={(e) => setNewComment(e.target.value)}
                            placeholder="Add a comment..."
                            className="flex-1 text-sm p-3 rounded-lg border border-gray-300 dark:border-[#35363a] bg-gray-50 dark:bg-[#1a1a1a] text-black dark:text-white focus:outline-none focus:ring-1 focus:ring-gray-400"
                            onKeyDown={(e) => { if (e.key === 'Enter' && !isCodeMode) handleSubmit(); }}
                        />
                    )}
                    <button
                        onClick={handleSubmit}
                        disabled={isSubmitting || !newComment.trim()}
                        className="px-4 py-2 text-sm font-medium rounded-lg bg-black dark:bg-white text-white dark:text-black hover:opacity-90 disabled:opacity-50 cursor-pointer self-end"
                    >
                        {isSubmitting ? '...' : 'Post'}
                    </button>
                </div>
            </div>
        </div>
    );
}
