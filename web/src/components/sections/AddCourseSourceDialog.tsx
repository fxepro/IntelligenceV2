"use client";

import React, { useState, useEffect } from "react";
import { AlertCircle, Link2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { CURRICULUM_TYPES, inferCurriculumTypeFromUrl } from "@/lib/courses/curriculum-types";
import { slugifyCourseId } from "@/lib/sources/helpers";

export const COURSE_SOURCE_TYPES = [
  { value: "website", label: "Website" },
  { value: "sitemap", label: "Sitemap" },
  { value: "playlist", label: "Playlist" },
  { value: "profile", label: "Profile" },
  { value: "channel", label: "Channel" },
] as const;

export interface CourseSourceFormData {
  name: string;
  courseId: string;
  url: string;
  sourceType: string;
  connector: string;
}

export function AddCourseSourceDialog({
  open,
  onClose,
  onAdd,
}: {
  open: boolean;
  onClose: () => void;
  onAdd: (data: CourseSourceFormData) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [courseId, setCourseId] = useState("");
  const [courseIdTouched, setCourseIdTouched] = useState(false);
  const [url, setUrl] = useState("");
  const [sourceType, setSourceType] = useState("website");
  const [curriculumType, setCurriculumType] = useState("website");
  const [curriculumTouched, setCurriculumTouched] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const urlLooksValid = /^https?:\/\/.+\..+/i.test(url.trim());
  const courseIdLooksValid = /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(courseId.trim());
  const isValid = name.trim().length > 0 && courseIdLooksValid && urlLooksValid;
  const isManual = curriculumType === "manual";

  useEffect(() => {
    if (open) {
      setName("");
      setCourseId("");
      setCourseIdTouched(false);
      setUrl("");
      setSourceType("website");
      setCurriculumType("website");
      setCurriculumTouched(false);
      setError(null);
    }
  }, [open]);

  useEffect(() => {
    if (!courseIdTouched && name.trim()) {
      setCourseId(slugifyCourseId(name));
    }
  }, [name, courseIdTouched]);

  useEffect(() => {
    if (!curriculumTouched && urlLooksValid) {
      setCurriculumType(inferCurriculumTypeFromUrl(url));
    }
  }, [url, curriculumTouched, urlLooksValid]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Course name is required.");
      return;
    }
    if (!courseIdLooksValid) {
      setError("Destination ID is required (auto-filled from name — edit if needed).");
      return;
    }
    if (!urlLooksValid) {
      setError("Source URL must be a valid http(s) link.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await onAdd({
        name: name.trim(),
        courseId: courseId.trim(),
        url: url.trim(),
        sourceType,
        connector: curriculumType,
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add course");
    } finally {
      setSubmitting(false);
    }
  };

  const selectedCurriculum = CURRICULUM_TYPES.find((t) => t.value === curriculumType);

  return (
    <Dialog open={open} onOpenChange={(next) => !next && onClose()}>
      <DialogContent className="sm:max-w-2xl gap-0 p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b border-border/50 space-y-2">
          <DialogTitle className="text-xl">Add Course Source</DialogTitle>
          <DialogDescription className="text-sm leading-relaxed">
            Source URL is the page to scrape. Lessons land in{" "}
            <code className="text-xs font-mono">v2/data/&#123;destination-id&#125;/</code>.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-5">
          {error && (
            <div className="flex items-center gap-2 text-sm text-red-400 bg-red-500/5 border border-red-500/20 rounded-xl px-4 py-3">
              <AlertCircle className="w-4 h-4 flex-shrink-0" /> {error}
            </div>
          )}

          <div className="space-y-2">
            <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
              Course Name
            </label>
            <Input
              autoFocus
              placeholder="e.g., SOC 2 Video Course"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setError(null);
              }}
              className="text-sm"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
              Destination ID (folder name)
            </label>
            <Input
              placeholder="e.g., soc2-videos"
              value={courseId}
              onChange={(e) => {
                setCourseIdTouched(true);
                setCourseId(slugifyCourseId(e.target.value));
                setError(null);
              }}
              className="text-sm font-mono"
            />
            <p className="text-xs text-muted-foreground">
              Stored on the source record and used for{" "}
              <span className="font-mono">v2/data/{courseId || "destination-id"}/</span>
            </p>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
              <Link2 className="w-3.5 h-3.5" /> Source URL
            </label>
            <Textarea
              rows={2}
              placeholder="https://example.com/course/curriculum"
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                setError(null);
              }}
              className="font-mono text-sm resize-none min-h-[4.5rem]"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                Source Type
              </label>
              <Select value={sourceType} onValueChange={setSourceType}>
                <SelectTrigger className="text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {COURSE_SOURCE_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                Curriculum type
              </label>
              <Select
                value={curriculumType}
                onValueChange={(value) => {
                  setCurriculumTouched(true);
                  setCurriculumType(value);
                }}
              >
                <SelectTrigger className="text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CURRICULUM_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedCurriculum?.hint ? (
                <p className="text-xs text-muted-foreground">{selectedCurriculum.hint}</p>
              ) : null}
            </div>
          </div>

          <DialogFooter className="pt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
              Cancel
            </Button>
            <Button type="submit" disabled={!isValid || submitting}>
              {submitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" /> Adding...
                </>
              ) : isManual ? (
                "Add course"
              ) : (
                "Add and Discover"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
