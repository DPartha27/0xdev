"use client";

import React from "react";
import { Plus, X } from "lucide-react";

interface PollOptionEditorProps {
  options: string[];
  onChange: (options: string[]) => void;
}

export default function PollOptionEditor({
  options,
  onChange,
}: PollOptionEditorProps) {
  const add = () => {
    if (options.length < 10) onChange([...options, ""]);
  };

  const remove = (i: number) => {
    onChange(options.filter((_, idx) => idx !== i));
  };

  const update = (i: number, value: string) => {
    const next = [...options];
    next[i] = value;
    onChange(next);
  };

  return (
    <div className="space-y-2">
      {options.map((opt, i) => (
        <div key={i} className="flex items-center gap-2">
          <span className="text-sm text-neutral-400 w-5 shrink-0">{i + 1}.</span>
          <input
            type="text"
            value={opt}
            onChange={(e) => update(i, e.target.value)}
            placeholder={`Option ${i + 1}`}
            maxLength={200}
            className="flex-1 px-3 py-1.5 text-sm rounded-lg border bg-white dark:bg-neutral-900 border-neutral-200 dark:border-neutral-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {options.length > 2 && (
            <button
              type="button"
              onClick={() => remove(i)}
              className="p-1 text-neutral-400 hover:text-red-500 transition-colors"
              aria-label="Remove option"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      ))}

      {options.length < 10 && (
        <button
          type="button"
          onClick={add}
          className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-700 transition-colors mt-1"
        >
          <Plus className="w-4 h-4" />
          Add option
        </button>
      )}
    </div>
  );
}
