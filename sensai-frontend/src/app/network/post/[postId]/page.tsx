"use client";

import { useEffect } from "react";
import { useParams } from "next/navigation";
import { Header } from "@/components/layout/header";
import PostDetail from "@/components/network/PostDetail";

export default function PostDetailPage() {
    const params = useParams();
    const postId = Number(params.postId);

    useEffect(() => {
        document.title = 'Post · SensAI';
    }, []);

    return (
        <div className="min-h-screen bg-white dark:bg-black text-black dark:text-white">
            <Header />
            <PostDetail postId={postId} />
        </div>
    );
}
