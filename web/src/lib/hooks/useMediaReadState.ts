"use client";

import { useState, useEffect, useCallback } from "react";

const READ_STORAGE_KEY = "intelligence:media-read-ids";

export function loadReadIds(): Set<string> {
  if (typeof window === "undefined") return new Set();
  try {
    const raw = localStorage.getItem(READ_STORAGE_KEY);
    if (!raw) return new Set();
    const arr = JSON.parse(raw);
    return new Set(Array.isArray(arr) ? arr.map(String) : []);
  } catch {
    return new Set();
  }
}

export function saveReadIds(ids: Set<string>) {
  try {
    localStorage.setItem(READ_STORAGE_KEY, JSON.stringify([...ids]));
  } catch {
    // ignore quota / private mode
  }
}

/** Local read/unread tracking until server persistence exists. */
export function useMediaReadState() {
  const [readIds, setReadIds] = useState<Set<string>>(() => new Set());

  useEffect(() => {
    setReadIds(loadReadIds());
  }, []);

  const markRead = useCallback((id: string) => {
    setReadIds((prev) => {
      if (prev.has(id)) return prev;
      const next = new Set(prev);
      next.add(id);
      saveReadIds(next);
      return next;
    });
  }, []);

  return { readIds, markRead };
}
