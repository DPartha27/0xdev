import React from "react";
import type { PostType } from "@/types/network";
import { MessageSquare, HelpCircle, FileText, BarChart2 } from "lucide-react";

interface PostTypeBadgeProps {
  type: PostType;
  size?: "sm" | "md";
}

const CONFIG: Record<PostType, { label: string; color: string; Icon: React.FC<any> }> = {
  thread: {
    label: "Thread",
    color: "bg-blue-100 text-blue-700",
    Icon: MessageSquare,
  },
  question: {
    label: "Q&A",
    color: "bg-orange-100 text-orange-700",
    Icon: HelpCircle,
  },
  note: {
    label: "Note",
    color: "bg-green-100 text-green-700",
    Icon: FileText,
  },
  poll: {
    label: "Poll",
    color: "bg-purple-100 text-purple-700",
    Icon: BarChart2,
  },
};

export default function PostTypeBadge({ type, size = "sm" }: PostTypeBadgeProps) {
  const { label, color, Icon } = CONFIG[type] ?? CONFIG.thread;
  const sizeClass = size === "sm" ? "text-xs px-2 py-0.5" : "text-sm px-3 py-1";

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-medium ${color} ${sizeClass}`}
    >
      <Icon className={size === "sm" ? "w-3 h-3" : "w-4 h-4"} />
      {label}
    </span>
  );
}
