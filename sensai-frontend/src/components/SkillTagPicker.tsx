"use client";

import React, { useState, useRef, useEffect } from "react";
import type { Skill } from "@/types/network";
import SkillTag from "./SkillTag";

interface SkillTagPickerProps {
  skills: Skill[];           // All available skills for this org
  selected: Skill[];         // Currently selected skills
  onChange: (selected: Skill[]) => void;
  placeholder?: string;
  disabled?: boolean;
}

export default function SkillTagPicker({
  skills,
  selected,
  onChange,
  placeholder = "Add skills...",
  disabled = false,
}: SkillTagPickerProps) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedIds = new Set(selected.map((s) => s.id));
  const filtered = skills.filter(
    (s) =>
      !selectedIds.has(s.id) &&
      s.name.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function addSkill(skill: Skill) {
    onChange([...selected, skill]);
    setQuery("");
  }

  function removeSkill(skillId: number) {
    onChange(selected.filter((s) => s.id !== skillId));
  }

  return (
    <div ref={containerRef} className="relative">
      <div
        className={`flex flex-wrap gap-1 min-h-[38px] p-1.5 border rounded-md bg-white dark:bg-neutral-900 ${
          disabled ? "opacity-60 pointer-events-none" : "cursor-text"
        }`}
        onClick={() => !disabled && setOpen(true)}
      >
        {selected.map((skill) => (
          <SkillTag key={skill.id} skill={skill} onRemove={removeSkill} />
        ))}
        <input
          className="flex-1 min-w-[120px] outline-none bg-transparent text-sm px-1 text-neutral-800 dark:text-neutral-100"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          placeholder={selected.length === 0 ? placeholder : ""}
          disabled={disabled}
        />
      </div>

      {open && filtered.length > 0 && (
        <ul className="absolute z-50 mt-1 w-full max-h-48 overflow-y-auto bg-white dark:bg-neutral-900 border rounded-md shadow-lg">
          {filtered.map((skill) => (
            <li
              key={skill.id}
              className="px-3 py-2 text-sm cursor-pointer hover:bg-neutral-100 dark:hover:bg-neutral-800 flex items-center gap-2"
              onMouseDown={(e) => {
                e.preventDefault();
                addSkill(skill);
              }}
            >
              <SkillTag skill={skill} />
              {skill.description && (
                <span className="text-neutral-500 text-xs truncate">
                  {skill.description}
                </span>
              )}
            </li>
          ))}
        </ul>
      )}

      {open && query && filtered.length === 0 && (
        <div className="absolute z-50 mt-1 w-full bg-white dark:bg-neutral-900 border rounded-md shadow-lg px-3 py-2 text-sm text-neutral-500">
          No skills found for "{query}"
        </div>
      )}
    </div>
  );
}
