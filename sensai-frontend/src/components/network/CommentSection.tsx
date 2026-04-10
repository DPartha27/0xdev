"use client";

import { useState } from "react";
import { NetworkComment } from "@/types/network";
import CommentCard from "./CommentCard";
import { Code, ImagePlus, Trash2, Loader2, AlertTriangle } from "lucide-react";
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
    const [commentImageUrl, setCommentImageUrl] = useState<string | null>(null);
    const [imageUploading, setImageUploading] = useState(false);
    const [imageError, setImageError] = useState<string | null>(null);
    const [relevanceError, setRelevanceError] = useState<string | null>(null);

    const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setImageError(null);
        setImageUploading(true);
        try {
            const validateForm = new FormData();
            validateForm.append("file", file);
            const validateRes = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/file/validate-image`, {
                method: "POST",
                body: validateForm,
            });
            if (!validateRes.ok) {
                const err = await validateRes.json();
                setImageError(err.detail || "Only educational images are allowed.");
                return;
            }
            const uploadForm = new FormData();
            uploadForm.append("file", file);
            uploadForm.append("content_type", file.type);
            const uploadRes = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/file/upload-local`, {
                method: "POST",
                body: uploadForm,
            });
            if (uploadRes.ok) {
                const data = await uploadRes.json();
                setCommentImageUrl(data.static_url);
            }
        } catch {
            setImageError("Failed to upload image.");
        } finally {
            setImageUploading(false);
            e.target.value = "";
        }
    };

    const handleSubmit = async () => {
        if ((!newComment.trim() && !commentImageUrl) || !user?.id) return;
        setIsSubmitting(true);
        setRelevanceError(null);

        try {
            const body: any = { author_id: user.id };
            if (isCodeMode) {
                body.content = "Code snippet";
                body.code_content = newComment;
                body.coding_language = codeLanguage;
            } else {
                body.content = newComment || "Image";
            }
            if (commentImageUrl) {
                body.image_url = commentImageUrl;
            }

            const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/posts/${postId}/comments`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });

            if (res.ok) {
                setNewComment("");
                setIsCodeMode(false);
                setCommentImageUrl(null);
                setImageError(null);
                setRelevanceError(null);
                onCommentAdded();
            } else if (res.status === 422) {
                const err = await res.json();
                setRelevanceError(err.detail || "Your comment doesn't seem relevant to this post.");
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

    const handleReply = async (parentCommentId: number, content: string, codeContent?: string, codingLanguage?: string): Promise<boolean> => {
        if (!user?.id) return false;
        const body: any = { author_id: user.id, content, parent_comment_id: parentCommentId };
        if (codeContent) {
            body.code_content = codeContent;
            body.coding_language = codingLanguage;
        }

        const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/posts/${postId}/comments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        if (res.ok) {
            onCommentAdded();
            return true;
        } else if (res.status === 422) {
            const err = await res.json();
            throw new Error(err.detail || "Your reply doesn't seem relevant to this post.");
        }
        return false;
    };

    const handleDelete = async (commentId: number) => {
        if (!user?.id) return;
        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/network/comments/${commentId}`, {
                method: 'DELETE',
            });
            if (res.ok) {
                onCommentAdded();
            }
        } catch (err) {
            console.error('Error deleting comment:', err);
        }
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
                        currentUserId={user?.id}
                        onVote={handleVote}
                        onReply={handleReply}
                        onDelete={handleDelete}
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
                    <label className="flex items-center gap-1 text-xs px-2 py-0.5 rounded cursor-pointer text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
                        {imageUploading ? <Loader2 className="w-3 h-3 animate-spin" /> : <ImagePlus className="w-3 h-3" />}
                        Image
                        <input type="file" accept="image/png,image/jpeg,image/gif,image/webp" onChange={handleImageUpload} disabled={imageUploading} className="hidden" />
                    </label>
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
                {relevanceError && (
                    <div className="flex items-center gap-1.5 text-xs text-orange-600 dark:text-orange-400 mb-2 p-2 rounded-lg bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800">
                        <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                        {relevanceError}
                    </div>
                )}
                {imageError && (
                    <div className="flex items-center gap-1.5 text-xs text-red-500 mb-2">
                        <AlertTriangle className="w-3 h-3 flex-shrink-0" />
                        {imageError}
                    </div>
                )}
                {commentImageUrl && (
                    <div className="relative inline-block mb-2">
                        <img src={`${process.env.NEXT_PUBLIC_BACKEND_URL}${commentImageUrl}`} alt="Upload" className="max-h-24 rounded-md border border-gray-200 dark:border-[#35363a]" />
                        <button onClick={() => setCommentImageUrl(null)} className="absolute top-1 right-1 p-0.5 rounded-full bg-black/60 text-white hover:bg-black/80 cursor-pointer">
                            <Trash2 className="w-3 h-3" />
                        </button>
                    </div>
                )}
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
