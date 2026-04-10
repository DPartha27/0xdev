"use client";

import React, { useState } from "react";
import { Bookmark } from "lucide-react";
import { bookmarkPost } from "@/lib/network-api";

interface BookmarkButtonProps {
  postId: number;
  userId: number;
  isBookmarked: boolean;
  onToggle?: (isBookmarked: boolean) => void;
}

export default function BookmarkButton({
  postId,
  userId,
  isBookmarked: initialBookmarked,
  onToggle,
}: BookmarkButtonProps) {
  const [bookmarked, setBookmarked] = useState(initialBookmarked);
  const [pending, setPending] = useState(false);

  async function handleClick() {
    if (pending) return;
    const prev = bookmarked;
    setBookmarked(!prev);
    setPending(true);
    try {
      await bookmarkPost(postId, userId);
      onToggle?.(!prev);
    } catch {
      setBookmarked(prev);
    } finally {
      setPending(false);
    }
  }

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={pending}
      className={`p-1.5 rounded transition-colors ${
        bookmarked
          ? "text-yellow-500"
          : "text-neutral-400 hover:text-yellow-500"
      } disabled:opacity-40`}
      aria-label={bookmarked ? "Remove bookmark" : "Bookmark"}
      title={bookmarked ? "Remove bookmark" : "Bookmark"}
    >
      <Bookmark
        className="w-4 h-4"
        fill={bookmarked ? "currentColor" : "none"}
      />
    </button>
  );
}
