"use client";

import React, { useState } from "react";
import { X, Flag } from "lucide-react";
import type { FlagReason } from "@/types/network";
import { flagContent } from "@/lib/network-api";

interface FlagContentDialogProps {
  open: boolean;
  onClose: () => void;
  targetType: "post" | "reply";
  targetId: number;
  postId: number;
  reporterId: number;
}

const REASONS: { value: FlagReason; label: string; description: string }[] = [
  { value: "spam", label: "Spam", description: "Unsolicited promotion or repetitive content" },
  { value: "offensive", label: "Offensive", description: "Harassment, hate speech, or harmful content" },
  { value: "off_topic", label: "Off-topic", description: "Not relevant to this hub or discussion" },
  { value: "misinformation", label: "Misinformation", description: "Factually incorrect or misleading content" },
  { value: "other", label: "Other", description: "Another issue not listed above" },
];

export default function FlagContentDialog({
  open,
  onClose,
  targetType,
  targetId,
  postId,
  reporterId,
}: FlagContentDialogProps) {
  const [selected, setSelected] = useState<FlagReason | null>(null);
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  async function handleSubmit() {
    if (!selected) return;
    setSubmitting(true);
    try {
      await flagContent(
        targetType,
        targetId,
        postId,
        reporterId,
        selected,
        description || undefined
      );
      setSubmitted(true);
      setTimeout(() => {
        onClose();
        setSubmitted(false);
        setSelected(null);
        setDescription("");
      }, 1500);
    } finally {
      setSubmitting(false);
    }
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-2xl w-full max-w-md">
        <div className="flex items-center justify-between px-5 py-4 border-b border-neutral-200 dark:border-neutral-700">
          <div className="flex items-center gap-2">
            <Flag className="w-4 h-4 text-red-500" />
            <h2 className="font-semibold">Report content</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded text-neutral-400 hover:text-neutral-600 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {submitted ? (
          <div className="px-5 py-8 text-center">
            <p className="text-green-600 font-medium">
              Thanks for reporting. We'll review this shortly.
            </p>
          </div>
        ) : (
          <div className="px-5 py-4 space-y-3">
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              Why are you reporting this content?
            </p>

            <div className="space-y-2">
              {REASONS.map((r) => (
                <button
                  key={r.value}
                  type="button"
                  onClick={() => setSelected(r.value)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg border transition-colors ${
                    selected === r.value
                      ? "border-red-400 bg-red-50 dark:bg-red-900/20"
                      : "border-neutral-200 dark:border-neutral-700 hover:border-neutral-400"
                  }`}
                >
                  <p className="text-sm font-medium">{r.label}</p>
                  <p className="text-xs text-neutral-500">{r.description}</p>
                </button>
              ))}
            </div>

            {selected === "other" && (
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the issue…"
                rows={3}
                maxLength={500}
                className="w-full px-3 py-2 text-sm rounded-lg border bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-700 focus:outline-none focus:ring-2 focus:ring-red-400 resize-none"
              />
            )}

            <div className="flex justify-end gap-2 pt-1">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm rounded-lg text-neutral-600 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!selected || submitting}
                onClick={handleSubmit}
                className="px-4 py-2 text-sm rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                {submitting ? "Reporting…" : "Report"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
