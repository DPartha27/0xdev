import React from "react";
import Link from "next/link";
import { Users, FileText, Lock, Archive } from "lucide-react";
import type { Hub } from "@/types/network";
import SkillTag from "./SkillTag";

interface HubCardProps {
  hub: Hub;
  schoolId: string;
}

export default function HubCard({ hub, schoolId }: HubCardProps) {
  return (
    <Link
      href={`/school/${schoolId}/network/${hub.slug}`}
      className="block rounded-xl border bg-white dark:bg-neutral-900 hover:shadow-md transition-shadow p-5"
    >
      <div className="flex items-start gap-3">
        {hub.icon && (
          <span className="text-2xl leading-none mt-0.5">{hub.icon}</span>
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-neutral-900 dark:text-neutral-100 truncate">
              {hub.name}
            </h3>
            {hub.visibility === "private" && (
              <Lock className="w-3.5 h-3.5 text-neutral-400 shrink-0" />
            )}
            {hub.visibility === "archived" && (
              <Archive className="w-3.5 h-3.5 text-neutral-400 shrink-0" />
            )}
          </div>

          {hub.description && (
            <p className="text-sm text-neutral-500 line-clamp-2 mb-3">
              {hub.description}
            </p>
          )}

          {hub.skills.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-3">
              {hub.skills.slice(0, 4).map((skill) => (
                <SkillTag key={skill.id} skill={skill} />
              ))}
              {hub.skills.length > 4 && (
                <span className="text-xs text-neutral-400">
                  +{hub.skills.length - 4} more
                </span>
              )}
            </div>
          )}

          <div className="flex items-center gap-4 text-xs text-neutral-500">
            <span className="flex items-center gap-1">
              <Users className="w-3.5 h-3.5" />
              {hub.member_count} member{hub.member_count !== 1 ? "s" : ""}
            </span>
            <span className="flex items-center gap-1">
              <FileText className="w-3.5 h-3.5" />
              {hub.post_count} post{hub.post_count !== 1 ? "s" : ""}
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}
