"use client";

import { Suspense } from "react";
import LibraryLessonsPage from "./lessons-client";

export default function LibraryLessonsRoute() {
  return (
    <Suspense
      fallback={
        <div className="p-6 text-sm text-muted-foreground">Loading lessons…</div>
      }
    >
      <LibraryLessonsPage />
    </Suspense>
  );
}
