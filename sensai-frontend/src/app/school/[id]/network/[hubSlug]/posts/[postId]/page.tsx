"use client";

import React from "react";
import { useParams } from "next/navigation";
import { Header } from "@/components/layout/header";
import { useAuth } from "@/lib/auth";
import { useSchools } from "@/lib/api";
import { usePost } from "@/lib/network-api";
import PostDetailView from "@/components/PostDetailView";

export default function PostPage() {
  const params = useParams();
  const schoolId = params.id as string;
  const hubSlug = params.hubSlug as string;
  const postId = parseInt(params.postId as string);

  const { user } = useAuth();
  const { schools } = useSchools();
  const school = schools?.find(
    (s) => s.id === schoolId || s.slug === schoolId
  );

  const userId = user?.id ? parseInt(user.id.toString()) : 0;
  const { post, isLoading, refetch } = usePost(postId, userId);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-white dark:bg-black">
        <div className="hidden sm:block">
          <Header showCreateCourseButton={false} />
        </div>
        <div className="flex justify-center items-center py-24">
          <div className="w-10 h-10 border-t-2 border-b-2 rounded-full animate-spin border-neutral-400" />
        </div>
      </div>
    );
  }

  if (!post) {
    return (
      <div className="min-h-screen bg-white dark:bg-black flex items-center justify-center">
        <p className="text-neutral-500">Post not found</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-black">
      <div className="hidden sm:block">
        <Header showCreateCourseButton={false} />
      </div>
      <div className="max-w-4xl mx-auto px-4 py-8">
        <PostDetailView
          post={post}
          schoolId={schoolId}
          hubSlug={hubSlug}
          currentUserId={userId}
          onRefresh={refetch}
        />
      </div>
    </div>
  );
}
