"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Header } from "@/components/layout/header";
import { ChevronLeft, Save, Trash2 } from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { useSchools } from "@/lib/api";
import { updateHub, deleteHub } from "@/lib/network-api";
import type { Hub } from "@/types/network";
import ConfirmationDialog from "@/components/ConfirmationDialog";

export default function HubSettingsPage() {
  const params = useParams();
  const router = useRouter();
  const schoolId = params.id as string;
  const hubSlug = params.hubSlug as string;
  const { user } = useAuth();
  const { schools } = useSchools();

  const school = schools?.find(
    (s) => s.id === schoolId || s.slug === schoolId
  );
  const orgId = school ? parseInt(school.id) : null;
  const isAdmin = school?.role === "owner" || school?.role === "admin";

  const [hub, setHub] = useState<Hub | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [icon, setIcon] = useState("");
  const [visibility, setVisibility] = useState("public");
  const [saving, setSaving] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (!orgId) return;
    fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/hubs/?org_id=${orgId}`)
      .then((r) => r.json())
      .then((hubs: Hub[]) => {
        const found = hubs.find((h) => h.slug === hubSlug);
        if (found) {
          setHub(found);
          setName(found.name);
          setDescription(found.description ?? "");
          setIcon(found.icon ?? "");
          setVisibility(found.visibility);
        }
      });
  }, [orgId, hubSlug]);

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-white dark:bg-black flex items-center justify-center">
        <p className="text-neutral-500">Access denied</p>
      </div>
    );
  }

  async function handleSave() {
    if (!hub) return;
    setSaving(true);
    try {
      await updateHub(hub.id, { name, description, icon, visibility });
      router.push(`/school/${schoolId}/network/${hubSlug}`);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!hub) return;
    setDeleting(true);
    try {
      await deleteHub(hub.id);
      router.push(`/school/${schoolId}/network`);
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="min-h-screen bg-white dark:bg-black">
      <div className="hidden sm:block">
        <Header showCreateCourseButton={false} />
      </div>
      <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
        <Link
          href={`/school/${schoolId}/network/${hubSlug}`}
          className="inline-flex items-center gap-1 text-sm text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
          Back to hub
        </Link>

        <h1 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
          Hub Settings
        </h1>

        <div className="rounded-xl border bg-white dark:bg-neutral-900 p-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full px-3 py-2 text-sm rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              Icon (emoji)
            </label>
            <input
              type="text"
              value={icon}
              onChange={(e) => setIcon(e.target.value)}
              maxLength={4}
              className="w-20 px-3 py-2 text-sm rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 focus:outline-none focus:ring-2 focus:ring-blue-500 text-center text-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              Visibility
            </label>
            <select
              value={visibility}
              onChange={(e) => setVisibility(e.target.value)}
              className="px-3 py-2 text-sm rounded-lg border border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="public">Public</option>
              <option value="private">Private</option>
              <option value="archived">Archived</option>
            </select>
          </div>

          <div className="flex justify-end">
            <button
              type="button"
              disabled={saving}
              onClick={handleSave}
              className="flex items-center gap-1.5 px-4 py-2 text-sm rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              <Save className="w-4 h-4" />
              {saving ? "Saving…" : "Save changes"}
            </button>
          </div>
        </div>

        {/* Danger zone */}
        <div className="rounded-xl border border-red-200 dark:border-red-900 p-5">
          <h2 className="font-semibold text-red-600 mb-2">Danger Zone</h2>
          <p className="text-sm text-neutral-500 mb-3">
            Deleting this hub will permanently remove all posts and discussions.
          </p>
          <button
            type="button"
            onClick={() => setShowDeleteDialog(true)}
            className="flex items-center gap-1.5 px-4 py-2 text-sm rounded-lg border border-red-400 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Delete hub
          </button>
        </div>
      </div>

      <ConfirmationDialog
        show={showDeleteDialog}
        title="Delete hub"
        message={`Are you sure you want to delete "${hub?.name}"? All posts will be permanently deleted.`}
        confirmButtonText="Delete"
        type="delete"
        isLoading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setShowDeleteDialog(false)}
      />
    </div>
  );
}
