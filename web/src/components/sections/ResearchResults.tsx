"use client";

import { Telescope, Loader2 } from "lucide-react";
import { CandidateCard, type Candidate } from "@/components/sections/CandidateCard";

export function ResearchResults({
  loading,
  searched,
  candidates,
  busyId,
  onPromote,
  onDismiss,
}: {
  loading: boolean;
  searched: boolean;
  candidates: Candidate[];
  busyId: string | null;
  onPromote: (id: string) => void;
  onDismiss: (id: string) => void;
}) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-muted-foreground gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
        <p className="text-sm">Searching platforms and ranking candidates…</p>
      </div>
    );
  }

  if (candidates.length > 0) {
    return (
      <>
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">
            {candidates.length} candidate source{candidates.length !== 1 ? "s" : ""}
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {candidates.map((c) => (
            <CandidateCard
              key={c.id}
              c={c}
              onPromote={onPromote}
              onDismiss={onDismiss}
              busy={busyId === c.id}
            />
          ))}
        </div>
      </>
    );
  }

  if (searched) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-muted-foreground gap-2">
        <Telescope className="w-10 h-10 opacity-30" />
        <p className="text-sm">No candidates found. Try a broader query, enable Facebook, or check the notices above.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center py-20 text-muted-foreground gap-2">
      <Telescope className="w-10 h-10 opacity-30" />
      <p className="text-sm">Describe what you want to monitor to discover new sources.</p>
    </div>
  );
}
