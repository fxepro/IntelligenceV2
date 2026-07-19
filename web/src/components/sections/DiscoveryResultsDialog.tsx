"use client";

import Link from "next/link";
import { ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ContentTypePill } from "@/components/sections/ContentTypePill";
import { MediaStatusPill } from "@/components/sections/StatusBadge";
import type { Source } from "@/lib/mock-data/sources";
import type { MediaItem } from "@/lib/mock-data/media-items";
import {
  formatDuration,
  formatViews,
  formatRelativeDate,
} from "@/lib/mock-data/media-items";

export function DiscoveryResultsDialog({
  open,
  onClose,
  source,
  items,
  meta,
}: {
  open: boolean;
  onClose: () => void;
  source: Source | undefined;
  items: MediaItem[];
  meta?: { newCount: number; totalFound: number };
}) {
  return (
    <Dialog open={open} onOpenChange={(next) => !next && onClose()}>
      <DialogContent className="sm:max-w-6xl max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="pr-8">
            {source?.name ?? "Discovered items"}
          </DialogTitle>
          <p className="text-sm text-muted-foreground">
            {meta?.newCount != null
              ? `${meta.newCount} new item${meta.newCount !== 1 ? "s" : ""} saved to database`
              : `${items.length} item${items.length !== 1 ? "s" : ""} shown`}
            {meta?.totalFound != null ? ` · ${meta.totalFound} found live` : ""}
          </p>
        </DialogHeader>
        <div className="overflow-auto -mx-6 px-6 flex-1 min-h-0">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="h-9 text-fine font-bold uppercase tracking-wider">Title</TableHead>
                <TableHead className="h-9 text-fine font-bold uppercase tracking-wider w-[72px]">Type</TableHead>
                <TableHead className="h-9 text-fine font-bold uppercase tracking-wider w-[72px]">Duration</TableHead>
                <TableHead className="h-9 text-fine font-bold uppercase tracking-wider w-[72px]">Views</TableHead>
                <TableHead className="h-9 text-fine font-bold uppercase tracking-wider w-[88px]">Published</TableHead>
                <TableHead className="h-9 text-fine font-bold uppercase tracking-wider w-[88px]">Status</TableHead>
                <TableHead className="h-9 w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((item, i) => (
                <TableRow key={`${item.id}-${i}`} className="h-11">
                  <TableCell className="py-2">
                    <div className="flex items-center gap-2.5 min-w-0">
                      {item.thumbnail_url ? (
                        <img
                          src={item.thumbnail_url}
                          alt=""
                          className="w-12 h-7 rounded object-cover shrink-0 bg-muted"
                        />
                      ) : (
                        <div className="w-12 h-7 rounded bg-muted shrink-0" />
                      )}
                      <span className="font-medium text-xs truncate" title={item.title}>{item.title}</span>
                    </div>
                  </TableCell>
                  <TableCell className="py-2">
                    <ContentTypePill contentType={item.content_type === "short" ? "short" : undefined} />
                  </TableCell>
                  <TableCell className="py-2 text-muted-foreground font-mono text-fine whitespace-nowrap">
                    {formatDuration(item.duration_seconds)}
                  </TableCell>
                  <TableCell className="py-2 text-muted-foreground text-fine whitespace-nowrap">
                    {formatViews(item.view_count)}
                  </TableCell>
                  <TableCell className="py-2 text-muted-foreground text-fine whitespace-nowrap">
                    {formatRelativeDate(item.published_at)}
                  </TableCell>
                  <TableCell className="py-2">
                    <MediaStatusPill status={item.status} />
                  </TableCell>
                  <TableCell className="py-2">
                    <a
                      href={item.canonical_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-muted-foreground hover:text-primary"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Close</Button>
          {source && (
            <Button asChild>
              <Link href={`/media/sources/${source.id}`}>Open channel</Link>
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
