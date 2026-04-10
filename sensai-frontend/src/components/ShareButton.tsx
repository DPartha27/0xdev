"use client";

import React, { useState } from "react";
import { Share2, Check } from "lucide-react";

interface ShareButtonProps {
  url?: string;
  title?: string;
}

export default function ShareButton({ url, title }: ShareButtonProps) {
  const [copied, setCopied] = useState(false);

  async function handleShare() {
    const shareUrl = url ?? window.location.href;
    try {
      if (navigator.share) {
        await navigator.share({ title, url: shareUrl });
      } else {
        await navigator.clipboard.writeText(shareUrl);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }
    } catch {
      // User cancelled or clipboard blocked — silently ignore
    }
  }

  return (
    <button
      type="button"
      onClick={handleShare}
      className="flex items-center gap-1.5 text-sm text-neutral-500 hover:text-neutral-800 transition-colors"
      title="Share"
    >
      {copied ? (
        <>
          <Check className="w-4 h-4 text-green-500" />
          <span className="text-green-600 text-xs">Copied!</span>
        </>
      ) : (
        <>
          <Share2 className="w-4 h-4" />
          <span className="text-xs">Share</span>
        </>
      )}
    </button>
  );
}
