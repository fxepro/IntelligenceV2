"use client";

import React, { useEffect, useState } from "react";
import {
  CheckCircle2,
  AlertCircle,
  Loader2,
  Link2,
  Sparkles,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { PlatformIcon } from "@/components/sections/PlatformBadge";
import { PLATFORM_COLORS, PLATFORM_LABELS, type Source, type Platform, type SourcePriority } from "@/lib/mock-data/sources";
import {
  detectPlatform,
  guessNameFromUrl,
  facebookProfileIdFromUrl,
  PLATFORM_OPTIONS,
  PLATFORM_GUIDES,
  PRIORITY_OPTIONS,
  SOURCE_TYPES_BY_PLATFORM,
  formatTagsInput,
  parseTagsInput,
} from "@/lib/sources/helpers";

export function AddSourceDialog({
  open,
  onClose,
  onAdd,
  initialSource,
}: {
  open: boolean;
  onClose: () => void;
  onAdd: (
    source: Partial<Source> & {
      discover?: boolean;
      stream_urls?: Record<string, string>;
    }
  ) => Promise<void>;
  initialSource?: {
    platform: Platform;
    source_type: string;
    source_url: string;
    vanity_url?: string | null;
    name: string | null;
    description: string | null;
    tags?: string[];
    priority?: SourcePriority;
    streams?: Array<{
      stream_type: string;
      stream_url?: string | null;
    }>;
  };
}) {
  const editing = Boolean(initialSource);
  const [url, setUrl] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [tagsInput, setTagsInput] = useState("");
  const [priority, setPriority] = useState<SourcePriority>("normal");
  const [platform, setPlatform] = useState<Platform>("facebook");
  const [sourceType, setSourceType] = useState("facebook_reels");
  const [videoUrl, setVideoUrl] = useState("");
  const [shortUrl, setShortUrl] = useState("");
  const [discoverAfter, setDiscoverAfter] = useState(true);
  const [nameTouched, setNameTouched] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const detected = detectPlatform(url);
  const guide = PLATFORM_GUIDES[platform];
  const typeOptions = SOURCE_TYPES_BY_PLATFORM[platform];
  const urlLooksValid = /^https?:\/\/.+\..+/i.test(url.trim());
  const resolvedProfileId =
    platform === "facebook"
      ? facebookProfileIdFromUrl(initialSource?.source_url) ??
        facebookProfileIdFromUrl(url)
      : null;
  const resolvedIdUrl = resolvedProfileId
    ? `https://www.facebook.com/profile.php?id=${resolvedProfileId}`
    : null;

  useEffect(() => {
    if (!open || !initialSource) return;
    const streamUrls = Object.fromEntries(
      (initialSource.streams ?? []).map((stream) => [
        stream.stream_type,
        stream.stream_url ?? "",
      ])
    );
    setUrl(
      (initialSource.platform === "facebook" && initialSource.vanity_url
        ? initialSource.vanity_url
        : initialSource.source_url) || ""
    );
    setName(initialSource.name ?? "");
    setDescription(initialSource.description ?? "");
    setTagsInput(formatTagsInput(initialSource.tags));
    setPriority(initialSource.priority ?? "normal");
    setPlatform(initialSource.platform);
    setSourceType(initialSource.source_type);
    setVideoUrl(
      streamUrls.youtube_videos ?? streamUrls.facebook_videos ?? ""
    );
    setShortUrl(
      streamUrls.youtube_shorts ?? streamUrls.facebook_reels ?? ""
    );
    setDiscoverAfter(false);
    setNameTouched(true);
    setError(null);
  }, [open, initialSource]);

  const reset = () => {
    setUrl("");
    setName("");
    setDescription("");
    setTagsInput("");
    setPriority("normal");
    setPlatform("facebook");
    setSourceType("facebook_reels");
    setVideoUrl("");
    setShortUrl("");
    setDiscoverAfter(true);
    setNameTouched(false);
    setError(null);
  };

  const applyUrl = (v: string) => {
    setUrl(v);
    setError(null);
    const d = detectPlatform(v);
    if (d) {
      setPlatform(d.platform);
      setSourceType(d.source_type);
      const clean = v.trim().replace(/\/+$/, "");
      if (d.platform === "youtube") {
        if (/\/videos$/i.test(clean)) setVideoUrl(clean);
        if (/\/shorts$/i.test(clean)) setShortUrl(clean);
      }
    }
    if (!nameTouched) {
      const guessed = guessNameFromUrl(v);
      if (guessed) setName(guessed);
    }
  };

  const pickPlatform = (p: Platform) => {
    setPlatform(p);
    const types = SOURCE_TYPES_BY_PLATFORM[p];
    setSourceType(types[0]?.value ?? "facebook_reels");
    setVideoUrl("");
    setShortUrl("");
  };

  const handleSubmit = async () => {
    if (!url.trim() || submitting) return;
    if (!urlLooksValid) {
      setError("Paste a full URL starting with https://");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await onAdd({
        platform,
        source_type: sourceType as Source["source_type"],
        source_url: url.trim(),
        stream_urls:
          platform === "youtube"
            ? {
                youtube_videos: videoUrl.trim(),
                youtube_shorts: shortUrl.trim(),
              }
            : platform === "facebook"
              ? {
                  facebook_reels: shortUrl.trim(),
                  facebook_videos: videoUrl.trim(),
                }
              : undefined,
        name: name.trim() || guessNameFromUrl(url) || url.trim(),
        description: description.trim() || null,
        tags: parseTagsInput(tagsInput),
        priority,
        discover: discoverAfter,
      });
      reset();
      onClose();
    } catch (err: any) {
      setError(err.message ?? "Failed to add source");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) {
          if (!submitting) reset();
          onClose();
        }
      }}
    >
      <DialogContent className="sm:max-w-4xl max-h-[90vh] overflow-y-auto gap-0 p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b border-border/50 space-y-2">
          <DialogTitle className="text-xl">{editing ? "Edit source" : "Add source"}</DialogTitle>
          <DialogDescription className="text-sm leading-relaxed">
            {editing
              ? "Update the source name, notes, channel URL, and content stream URLs together."
              : "Paste a public channel, page, or feed URL. We detect the platform, save it to your library, and can kick off discovery right away."}
          </DialogDescription>
        </DialogHeader>

        <div className="px-6 py-5 space-y-6">
          <div className="space-y-2">
            <div className="flex items-center justify-between gap-2">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                <Link2 className="w-3.5 h-3.5" />{" "}
                {platform === "facebook" ? "Vanity URL" : "Source URL"}
              </label>
              {detected && (
                <span className="text-fine font-bold uppercase tracking-wider text-emerald-500 inline-flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Detected {PLATFORM_LABELS[detected.platform]}
                </span>
              )}
            </div>
            <Textarea
              autoFocus
              rows={2}
              placeholder={
                platform === "facebook"
                  ? "Paste vanity URL — e.g. https://www.facebook.com/PageName"
                  : "Paste URL — e.g. https://www.youtube.com/@channel"
              }
              value={url}
              onChange={(e) => applyUrl(e.target.value)}
              className="font-mono text-sm resize-none min-h-[4.5rem]"
            />
            <p className="text-caption text-muted-foreground leading-relaxed">
              {platform === "facebook"
                ? "Enter the vanity page URL. On save we scrape page source for page_id / page_id_type and store the stable profile.php?id=… URL."
                : "Tip: copy the link from the address bar on the creator’s page, not from a share sheet or a single video."}
            </p>
            {platform === "facebook" && (
              <div className="space-y-2 rounded-lg border border-border/60 bg-muted/20 px-3 py-2.5">
                <label className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                  Profile ID URL
                </label>
                {resolvedProfileId && resolvedIdUrl ? (
                  <>
                    <Input
                      readOnly
                      value={resolvedIdUrl}
                      className="font-mono text-sm"
                      onFocus={(e) => e.target.select()}
                    />
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                      <span className="font-mono text-sm tabular-nums select-all">
                        {resolvedProfileId}
                      </span>
                      <a
                        href={resolvedIdUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-primary"
                      >
                        Open to verify
                        <ExternalLink className="w-3 h-3 shrink-0" />
                      </a>
                    </div>
                  </>
                ) : (
                  <p className="text-sm text-amber-600">
                    Not resolved yet — save a vanity URL to scrape page_id, or paste a profile.php?id=… link.
                  </p>
                )}
              </div>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Platform</label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {PLATFORM_OPTIONS.map((p) => {
                const active = platform === p.id;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => pickPlatform(p.id)}
                    disabled={editing}
                    className={`text-left rounded-xl border px-3 py-2.5 transition-colors ${
                      active
                        ? "border-primary/50 bg-primary/10 ring-1 ring-primary/30"
                        : "border-border/60 bg-muted/20 hover:bg-muted/40"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`inline-flex items-center justify-center w-7 h-7 rounded-md border ${PLATFORM_COLORS[p.id] ?? ""}`}>
                        <PlatformIcon platform={p.id} className="w-3.5 h-3.5" />
                      </span>
                      <div className="min-w-0">
                        <p className="text-xs font-semibold truncate">{p.label}</p>
                        <p className="text-fine text-muted-foreground truncate">{p.hint}</p>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {(platform === "facebook" || platform === "youtube") && (
            <div className="rounded-xl border border-border/60 bg-muted/15 p-4 space-y-3">
              <div>
                <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                  Content stream URLs
                </p>
                <p className="text-caption text-muted-foreground mt-1">
                  {platform === "youtube"
                    ? "Paste each URL that exists. Leave Videos or Shorts blank when that subtype does not exist."
                    : "Facebook cannot reliably derive these. Paste the Reels and Videos links separately."}
                </p>
              </div>
              <div className="grid grid-cols-1 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium">
                    {platform === "youtube" ? "Videos URL" : "Facebook Videos URL"}
                  </label>
                  <Input
                    value={videoUrl}
                    onChange={(event) => setVideoUrl(event.target.value)}
                    placeholder={
                      platform === "youtube"
                        ? "https://youtube.com/@channel/videos"
                        : "Paste the Facebook Videos link"
                    }
                    className="font-mono text-xs"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium">
                    {platform === "youtube" ? "Shorts URL" : "Facebook Reels URL"}
                  </label>
                  <Input
                    value={shortUrl}
                    onChange={(event) => setShortUrl(event.target.value)}
                    placeholder={
                      platform === "youtube"
                        ? "https://youtube.com/@channel/shorts"
                        : "Paste the Facebook Reels link"
                    }
                    className="font-mono text-xs"
                  />
                </div>
              </div>
            </div>
          )}

          <div className={`grid grid-cols-1 gap-5 ${platform === "facebook" ? "" : "lg:grid-cols-5"}`}>
            <div className={`${platform === "facebook" ? "" : "lg:col-span-3"} space-y-4`}>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Display name</label>
                  <Input
                    placeholder="e.g. David Finance"
                    value={name}
                    onChange={(e) => {
                      setNameTouched(true);
                      setName(e.target.value);
                    }}
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Source type</label>
                  <Select
                    value={sourceType}
                    onValueChange={setSourceType}
                    disabled={platform === "youtube" || platform === "facebook"}
                  >
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {typeOptions.map((t) => (
                        <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                    Tags <span className="text-muted-foreground/50 normal-case tracking-normal font-normal">(comma-separated)</span>
                  </label>
                  <Input
                    placeholder="finance, watchlist, canada"
                    value={tagsInput}
                    onChange={(e) => setTagsInput(e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Priority</label>
                  <Select value={priority} onValueChange={(value) => setPriority(value as SourcePriority)}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {PRIORITY_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={option.value!} title={option.title}>
                          {option.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                  Notes <span className="text-muted-foreground/50 normal-case tracking-normal font-normal">(optional)</span>
                </label>
                <Textarea
                  rows={3}
                  placeholder="Why you’re watching this source…"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="resize-none text-sm"
                />
              </div>

              <label className="flex items-start gap-3 rounded-xl border border-border/60 bg-muted/20 px-3.5 py-3 cursor-pointer hover:bg-muted/30 transition-colors">
                <input
                  type="checkbox"
                  checked={discoverAfter}
                  onChange={(e) => setDiscoverAfter(e.target.checked)}
                  className="mt-0.5 accent-primary"
                />
                <span className="min-w-0">
                  <span className="text-sm font-medium flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-primary" /> Discover content after saving
                  </span>
                  <span className="text-caption text-muted-foreground leading-relaxed block mt-0.5">
                    Scan all enabled content streams after saving.
                  </span>
                </span>
              </label>
            </div>

            {platform !== "facebook" && (
              <div className="lg:col-span-2 rounded-xl border border-border/50 bg-muted/15 p-4 space-y-3">
                <p className="text-fine font-bold uppercase tracking-widest text-muted-foreground">
                  {guide.title}
                </p>
                <ul className="space-y-2">
                  {guide.bullets.map((b) => (
                    <li key={b} className="text-xs text-muted-foreground leading-relaxed flex gap-2">
                      <span className="text-primary mt-0.5">•</span>
                      <span>{b}</span>
                    </li>
                  ))}
                </ul>
                <div className="space-y-1.5 pt-1">
                  <p className="text-fine font-bold uppercase tracking-widest text-muted-foreground">Examples</p>
                  {guide.examples.map((ex) => (
                    <button
                      key={ex}
                      type="button"
                      onClick={() => applyUrl(ex)}
                      className="block w-full text-left text-caption font-mono text-primary/90 hover:text-primary truncate rounded-md px-2 py-1.5 bg-background/60 border border-border/40 hover:border-primary/30 transition-colors"
                      title={ex}
                    >
                      {ex}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="flex items-center gap-2 text-sm text-red-400 bg-red-500/5 border border-red-500/20 rounded-xl px-4 py-3">
              <AlertCircle className="w-4 h-4 flex-shrink-0" /> {error}
            </div>
          )}
        </div>

        <DialogFooter className="px-6 py-4 border-t border-border/50 bg-muted/10 gap-2 sm:gap-2">
          <Button variant="outline" onClick={onClose} disabled={submitting}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={!url.trim() || submitting} className="gap-1.5 min-w-[140px]">
            {submitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
            {submitting
              ? "Saving…"
              : discoverAfter
                ? editing ? "Save & Discover" : "Add & Discover"
                : editing ? "Save Changes" : "Add Source"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
