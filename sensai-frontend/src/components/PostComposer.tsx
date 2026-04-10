"use client";

import React, { useState, useEffect, useRef } from "react";
import { Search, X, Link2 } from "lucide-react";
import type { PostType, Skill } from "@/types/network";
import type { TaskSearchResult } from "@/lib/network-api";
import PostTypeBadge from "./PostTypeBadge";
import SkillTagPicker from "./SkillTagPicker";
import PollOptionEditor from "./PollOptionEditor";
import { createPost, searchTasks } from "@/lib/network-api";

interface PostComposerProps {
  hubId: number;
  orgId: number;
  authorId: number;
  availableSkills: Skill[];
  onSuccess?: (postId: number) => void;
  onCancel?: () => void;
}

const POST_TYPES: PostType[] = ["thread", "question", "note", "poll"];

/** Inline task picker with debounced search */
function TaskPicker({
  orgId,
  selected,
  onSelect,
}: {
  orgId: number;
  selected: TaskSearchResult[];
  onSelect: (tasks: TaskSearchResult[]) => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<TaskSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (!query.trim()) { setResults([]); return; }
    timerRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const data = await searchTasks(query, orgId);
        setResults(data.filter((t) => !selected.find((s) => s.id === t.id)));
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  }, [query, orgId, selected]);

  function pick(task: TaskSearchResult) {
    onSelect([...selected, task]);
    setQuery("");
    setResults([]);
  }

  function remove(id: number) {
    onSelect(selected.filter((t) => t.id !== id));
  }

  return (
    <div>
      {/* Selected tasks */}
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-2">
          {selected.map((t) => (
            <span
              key={t.id}
              className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-700"
            >
              <Link2 className="w-3 h-3" />
              {t.title}
              <button
                type="button"
                onClick={() => remove(t.id)}
                className="ml-0.5 hover:text-red-500"
              >
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-2.5 top-2 w-3.5 h-3.5 text-neutral-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search tasks by name…"
          className="w-full pl-7 pr-3 py-1.5 text-xs rounded-lg border bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        {loading && (
          <span className="absolute right-2.5 top-2 text-xs text-neutral-400">…</span>
        )}
      </div>

      {/* Dropdown */}
      {results.length > 0 && (
        <div className="mt-1 rounded-lg border bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-700 shadow-lg overflow-hidden">
          {results.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => pick(t)}
              className="w-full text-left px-3 py-2 text-xs hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors flex items-center gap-2"
            >
              <Link2 className="w-3 h-3 text-neutral-400 shrink-0" />
              <span className="flex-1 truncate">{t.title}</span>
              <span className="text-neutral-400 shrink-0 capitalize">{t.type}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function PostComposer({
  hubId,
  orgId,
  authorId,
  availableSkills,
  onSuccess,
  onCancel,
}: PostComposerProps) {
  const [type, setType] = useState<PostType>("thread");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [selectedSkills, setSelectedSkills] = useState<Skill[]>([]);
  const [selectedTasks, setSelectedTasks] = useState<TaskSearchResult[]>([]);
  const [pollOptions, setPollOptions] = useState<string[]>(["", ""]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    if (type === "poll" && pollOptions.filter((o) => o.trim()).length < 2) {
      setError("A poll needs at least 2 options.");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const blocks = body.trim()
        ? [{ type: "paragraph", content: [{ type: "text", text: body }] }]
        : [];

      const payload: any = {
        hub_id: hubId,
        author_id: authorId,
        post_type: type,
        title: title.trim(),
        blocks,
        skill_ids: selectedSkills.map((s) => s.id),
        task_ids: selectedTasks.map((t) => t.id),
      };

      if (type === "poll") {
        payload.poll_options = pollOptions
          .map((o) => o.trim())
          .filter(Boolean);
      }

      const result = await createPost(payload);
      onSuccess?.(result.id);
    } catch (err: any) {
      setError(err.message ?? "Failed to create post. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-xl border bg-white dark:bg-neutral-900 p-5 space-y-4"
    >
      {/* Type selector */}
      <div>
        <p className="text-xs font-medium text-neutral-500 mb-2">Post type</p>
        <div className="flex flex-wrap gap-2">
          {POST_TYPES.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setType(t)}
              className={`rounded-lg border px-2 py-1 transition-colors ${
                type === t
                  ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                  : "border-neutral-200 dark:border-neutral-700 hover:border-neutral-400"
              }`}
            >
              <PostTypeBadge type={t} />
            </button>
          ))}
        </div>
      </div>

      {/* Title */}
      <div>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder={
            type === "question"
              ? "What's your question?"
              : type === "poll"
              ? "Poll question"
              : "Title"
          }
          maxLength={300}
          required
          className="w-full px-3 py-2 text-sm rounded-lg border bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Body (not for polls) */}
      {type !== "poll" && (
        <div>
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder={
              type === "note"
                ? "Share your notes or insights…"
                : "Add more context (optional)"
            }
            rows={4}
            className="w-full px-3 py-2 text-sm rounded-lg border bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-700 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>
      )}

      {/* Poll options */}
      {type === "poll" && (
        <div>
          <p className="text-xs font-medium text-neutral-500 mb-2">
            Poll options
          </p>
          <PollOptionEditor options={pollOptions} onChange={setPollOptions} />
        </div>
      )}

      {/* Skill picker */}
      <div>
        <p className="text-xs font-medium text-neutral-500 mb-2">
          Tag skills (optional)
        </p>
        <SkillTagPicker
          skills={availableSkills}
          selected={selectedSkills}
          onChange={setSelectedSkills}
        />
      </div>

      {/* Task linker */}
      <div>
        <p className="text-xs font-medium text-neutral-500 mb-2">
          Link to tasks (optional)
        </p>
        <TaskPicker
          orgId={orgId}
          selected={selectedTasks}
          onSelect={setSelectedTasks}
        />
      </div>

      {error && (
        <p className="text-sm text-red-500">{error}</p>
      )}

      {/* Actions */}
      <div className="flex justify-end gap-2 pt-1">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm rounded-lg text-neutral-600 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={submitting || !title.trim()}
          className="px-5 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {submitting ? "Posting…" : "Post"}
        </button>
      </div>
    </form>
  );
}
