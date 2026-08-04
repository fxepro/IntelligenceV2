"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AlertCircle, ArrowLeft, Download, Loader2 } from "lucide-react";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { Button } from "@/components/ui/button";
import { Icon } from "@/lib/icons";
import { API_BASE } from "@/lib/api-base";

interface LibraryItem {
  id: string;
  title: string | null;
  stream_type: string | null;
  content_type: string | null;
  source_id: string | null;
  description: string | null;
}

export default function LibraryItemViewerPage() {
  const params = useParams();
  const id = String(params.id ?? "");

  const [item, setItem] = useState<LibraryItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const assetUrl = `${API_BASE}/api/v1/library/assets/${id}`;

  const load = useCallback(async () => {
    if (!id) return;
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/library/${id}`);
      if (!res.ok) throw new Error(`Item not found (${res.status})`);
      setItem(await res.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load item");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  const mediaType = item?.stream_type || item?.content_type || "other";
  const backHref = item?.source_id ? `/library/sources/${item.source_id}` : "/library/sources";

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href={backHref} className="hover:text-foreground inline-flex items-center gap-1">
          <ArrowLeft className="h-4 w-4" />
          Back
        </Link>
      </div>

      <AppPageHeader
        title={item?.title || "Library item"}
        description={item?.description || undefined}
        icon={<Icon name="library" className="h-5 w-5 text-primary" />}
        actions={
          <Button asChild variant="outline" size="sm" className="gap-1.5">
            <a href={assetUrl} target="_blank" rel="noreferrer">
              <Download className="h-4 w-4" />
              Download
            </a>
          </Button>
        }
      />

      {loading ? (
        <p className="inline-flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading…
        </p>
      ) : error ? (
        <p className="text-destructive inline-flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          {error}
        </p>
      ) : (
        <div className="rounded-2xl border bg-card overflow-hidden">
          {mediaType === "video" ? (
            <video
              src={assetUrl}
              controls
              className="w-full max-h-[80vh] bg-black"
              preload="metadata"
            />
          ) : mediaType === "audio" ? (
            <div className="p-8">
              <audio src={assetUrl} controls className="w-full" preload="metadata" />
            </div>
          ) : mediaType === "pdf" ? (
            <iframe
              src={assetUrl}
              title={item?.title || "PDF"}
              className="w-full min-h-[80vh] border-0"
            />
          ) : mediaType === "image" ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={assetUrl} alt={item?.title || "Image"} className="max-w-full mx-auto block" />
          ) : (
            <div className="p-10 text-center text-muted-foreground space-y-4">
              <p>This file type opens best via download.</p>
              <Button asChild>
                <a href={assetUrl} target="_blank" rel="noreferrer">
                  Open file
                </a>
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
