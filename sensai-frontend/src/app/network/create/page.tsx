"use client";

import { useEffect } from "react";
import { Header } from "@/components/layout/header";
import CreatePostForm from "@/components/network/CreatePostForm";

export default function CreatePostPage() {
    useEffect(() => {
        document.title = 'Create Post · SensAI';
    }, []);

    return (
        <div className="min-h-screen bg-white dark:bg-black text-black dark:text-white">
            <Header />
            <CreatePostForm />
        </div>
    );
}
