"use client";

import React, { useState } from "react";
import { AlertCircle, Loader2, Youtube } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { API_BASE } from "@/lib/api-base";

export function ManualImportCourseLessonsDialog({
  open,
  onClose,
  sourceId,
  courseId,
  courseName,
  onImported,
}: {
  open: boolean;
  onClose: () => void;
  sourceId: string;
  courseId: string;
  courseName: string;
  onImported?: (result: { imported: number; skipped: number }) => void;
}) {
  const [text, setText] = useState("");
  const [defaultCategory, setDefaultCategory] = useState("General");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleClose = () => {
    setText("");
    setDefaultCategory("General");
    setError(null);
    setSuccess(null);
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/courses/sources/${sourceId}/lessons/manual-import`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text: text.trim(),
            default_category: defaultCategory.trim() || "General",
          }),
        },
      );
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(typeof data.detail === "string" ? data.detail : "Import failed");
      }
      const imported = Number(data.imported ?? 0);
      const skipped = Number(data.skipped ?? 0);
      if (imported === 0) {
        setSuccess(
          data.message ||
            (skipped > 0
              ? `No new links — ${skipped} duplicate URL(s) skipped.`
              : "No YouTube URLs found in pasted text."),
        );
      } else {
        setSuccess(
          `Added ${imported} lesson${imported !== 1 ? "s" : ""}` +
            (skipped > 0 ? ` · ${skipped} duplicate(s) skipped` : "") +
            ` → v2/data/${courseId}/`,
        );
        onImported?.({ imported, skipped });
        setText("");
      }
    } catch (err: any) {
      setError(err.message ?? "Import failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(next) => !next && handleClose()}>
      <DialogContent className="sm:max-w-2xl gap-0 p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b border-border/50 space-y-2">
          <DialogTitle className="text-xl flex items-center gap-2">
            <Youtube className="w-5 h-5 text-red-500" />
            Add YouTube lessons manually
          </DialogTitle>
          <DialogDescription className="text-sm leading-relaxed">
            Bypass Discover — paste links for <strong>{courseName}</strong>. Writes to destination{" "}
            <code className="text-xs font-mono">v2/data/{courseId}/</code> (marked{" "}
            <code className="text-xs">manual: true</code>, safe from scrape overwrite).
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {error && (
            <div className="flex items-center gap-2 text-sm text-red-400 bg-red-500/5 border border-red-500/20 rounded-xl px-4 py-3">
              <AlertCircle className="w-4 h-4 shrink-0" /> {error}
            </div>
          )}
          {success && (
            <div className="text-sm text-primary bg-primary/5 border border-primary/20 rounded-xl px-4 py-3">
              {success}
            </div>
          )}

          <div className="space-y-2">
            <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
              Default section (when line is URL only)
            </label>
            <Input
              value={defaultCategory}
              onChange={(e) => setDefaultCategory(e.target.value)}
              placeholder="General"
              className="text-sm"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
              YouTube links
            </label>
            <Textarea
              rows={12}
              value={text}
              onChange={(e) => {
                setText(e.target.value);
                setError(null);
                setSuccess(null);
              }}
              placeholder={`One per line. Examples:

https://youtu.be/abc123
Introduction to SOC2 | https://youtu.be/abc123
Module 1 | What is SOC2 (1:05) | https://youtu.be/xyz789`}
              className="font-mono text-xs leading-relaxed resize-y min-h-[220px]"
            />
          </div>

          <DialogFooter className="pt-2">
            <Button type="button" variant="outline" onClick={handleClose} disabled={submitting}>
              {success && !error ? "Close" : "Cancel"}
            </Button>
            <Button type="submit" disabled={!text.trim() || submitting}>
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Importing…
                </>
              ) : (
                "Import lessons"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
