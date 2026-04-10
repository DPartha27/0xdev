import React from "react";
import type { Skill } from "@/types/network";

interface SkillTagProps {
  skill: Pick<Skill, "id" | "name" | "slug">;
  onRemove?: (skillId: number) => void;
  onClick?: (skill: Pick<Skill, "id" | "name" | "slug">) => void;
  size?: "sm" | "md";
}

const SKILL_COLORS = [
  "bg-blue-100 text-blue-800",
  "bg-purple-100 text-purple-800",
  "bg-green-100 text-green-800",
  "bg-yellow-100 text-yellow-800",
  "bg-pink-100 text-pink-800",
  "bg-indigo-100 text-indigo-800",
];

function getSkillColor(slug: string) {
  let hash = 0;
  for (let i = 0; i < slug.length; i++) {
    hash = (hash * 31 + slug.charCodeAt(i)) % SKILL_COLORS.length;
  }
  return SKILL_COLORS[Math.abs(hash) % SKILL_COLORS.length];
}

export default function SkillTag({ skill, onRemove, onClick, size = "sm" }: SkillTagProps) {
  const colorClass = getSkillColor(skill.slug);
  const sizeClass = size === "sm" ? "text-xs px-2 py-0.5" : "text-sm px-3 py-1";

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-medium ${colorClass} ${sizeClass} ${onClick ? "cursor-pointer hover:opacity-80" : ""}`}
      onClick={() => onClick?.(skill)}
    >
      {skill.name}
      {onRemove && (
        <button
          type="button"
          className="ml-0.5 hover:opacity-70"
          onClick={(e) => {
            e.stopPropagation();
            onRemove(skill.id);
          }}
          aria-label={`Remove ${skill.name}`}
        >
          ×
        </button>
      )}
    </span>
  );
}
