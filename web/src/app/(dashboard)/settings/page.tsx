"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Plus,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  Trash2,
  Pencil,
  KeyRound,
  ExternalLink,
  RefreshCw,
  Play,
  Square,
  Server,
  Layers,
  FileAudio,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { PLATFORM_LABELS, type Platform } from "@/lib/mock-data/sources";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { PlatformBadge } from "@/components/sections/PlatformBadge";
import { Icon } from "@/lib/icons";

import { API_BASE, BACKEND_URL } from "@/lib/api-base";
const API_DOCS = `${BACKEND_URL}/docs`;
/** Default Website / App when platform=website (Scytale academy access). */
const DEFAULT_WEBSITE_APP_URL = "https://academy.scytale.ai";
const AUTH_PLATFORMS: Platform[] = [
  "facebook",
  "youtube",
  "x",
  "instagram",
  "tiktok",
  "podcast",
  "rss",
  "website",
];

const SESSION_PLATFORMS: {
  id: Platform;
  loginUrl: string;
  cookieHint: string;
  placeholder: string;
}[] = [
  {
    id: "youtube",
    loginUrl: "https://accounts.google.com/ServiceLogin?service=youtube",
    cookieHint: "Need SID / __Secure-1PSID / LOGIN_INFO from youtube.com cookies.",
    placeholder: "Paste Cookie header or Netscape cookie file…",
  },
  {
    id: "instagram",
    loginUrl: "https://www.instagram.com/accounts/login/",
    cookieHint: "Need sessionid from instagram.com cookies.",
    placeholder: "Paste Cookie header or Netscape cookie file…",
  },
  {
    id: "tiktok",
    loginUrl: "https://www.tiktok.com/login",
    cookieHint: "Need sessionid or sid_tt from tiktok.com cookies.",
    placeholder: "Paste Cookie header or Netscape cookie file…",
  },
  {
    id: "x",
    loginUrl: "https://x.com/i/flow/login",
    cookieHint: "Need auth_token from x.com cookies.",
    placeholder: "Paste Cookie header or Netscape cookie file…",
  },
];

type Tab = "stack" | "planes" | "discovery" | "transcription" | "access";

interface CredentialRow {
  id: string;
  platform: Platform;
  username: string;
  site_url?: string;
  has_password: boolean;
  has_session: boolean;
  status: string;
  last_error: string | null;
  last_verified_at: string | null;
  updated_at: string | null;
}

interface ProcessStatus {
  id: string;
  label: string;
  status: string;
  detail?: string | null;
  docs_url?: string | null;
  can_start?: boolean;
  can_stop?: boolean;
}

interface ControlPlane {
  id: string;
  label: string;
  status: string;
  blurb: string;
  home?: string | null;
  docs_url?: string | null;
}

interface TranscriptionConfig {
  engine: string;
  model: string;
  language: string;
  keep_audio: boolean;
  concurrency: number;
  batch_size: number;
  available_engines?: string[];
  available_models: string[];
  whisper_models?: string[];
  openai_models?: string[];
  whisper_installed: boolean;
  model_installed: boolean;
  openai_configured?: boolean;
  model_path: string;
  pricing?: {
    billing_unit: string;
    words_per_minute_estimate: number;
    note: string;
    openai: Record<
      string,
      { usd_per_minute: number; usd_per_hour: number; usd_per_word_estimate: number }
    >;
    whisper_cpp: {
      usd_per_minute: number;
      usd_per_word_estimate: number;
      note: string;
    };
  };
}

interface DiscoveryConfig {
  interval_minutes: number;
  max_items: number;
  media_page_size: number;
}

function StatusPill({ row }: { row: CredentialRow }) {
  if (row.status === "connected") {
    return (
      <span className="inline-flex items-center gap-1 text-fine font-bold uppercase tracking-wider text-emerald-500">
        <CheckCircle2 className="w-3 h-3" /> Connected
      </span>
    );
  }
  if (row.status === "error") {
    return (
      <span className="inline-flex items-center gap-1 text-fine font-bold uppercase tracking-wider text-red-400" title={row.last_error ?? ""}>
        <AlertCircle className="w-3 h-3" /> Error
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-fine font-bold uppercase tracking-wider text-amber-500">
      <KeyRound className="w-3 h-3" /> Saved
    </span>
  );
}

function ProcessPill({ status }: { status: string }) {
  if (status === "up" || status === "active") {
    return (
      <span className="inline-flex items-center gap-1 text-fine font-bold uppercase tracking-wider text-emerald-500">
        <CheckCircle2 className="w-3 h-3" /> {status === "active" ? "Active" : "Up"}
      </span>
    );
  }
  if (status === "planned") {
    return (
      <span className="inline-flex items-center gap-1 text-fine font-bold uppercase tracking-wider text-muted-foreground">
        Planned
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-fine font-bold uppercase tracking-wider text-red-400">
      <AlertCircle className="w-3 h-3" /> Down
    </span>
  );
}

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>("stack");
  const [items, setItems] = useState<CredentialRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [platform, setPlatform] = useState<Platform>("facebook");
  const [username, setUsername] = useState("");
  const [siteUrl, setSiteUrl] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [saving, setSaving] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);
  const [cUser, setCUser] = useState("");
  const [xs, setXs] = useState("");
  const [fbLabel, setFbLabel] = useState("");
  const [savingSession, setSavingSession] = useState(false);
  const [showFacebookSetup, setShowFacebookSetup] = useState(false);
  const [accessView, setAccessView] = useState<"all" | "connected">("all");
  const [sessionDrafts, setSessionDrafts] = useState<Record<string, { cookies: string; label: string }>>({});
  const [showSessionSetup, setShowSessionSetup] = useState<Record<string, boolean>>({});
  const [savingSessionPlatform, setSavingSessionPlatform] = useState<string | null>(null);

  const [processes, setProcesses] = useState<ProcessStatus[]>([]);
  const [planes, setPlanes] = useState<ControlPlane[]>([]);
  const [sysLoading, setSysLoading] = useState(true);
  const [startingId, setStartingId] = useState<string | null>(null);
  const [stoppingId, setStoppingId] = useState<string | null>(null);
  const [transcription, setTranscription] = useState<TranscriptionConfig | null>(null);
  const [savingTranscription, setSavingTranscription] = useState(false);
  const [discovery, setDiscovery] = useState<DiscoveryConfig | null>(null);
  const [savingDiscovery, setSavingDiscovery] = useState(false);

  const fbRow = items.find((r) => r.platform === "facebook");
  const facebookConnected = Boolean(fbRow?.status === "connected" || fbRow?.has_session);
  const connectedItems = items.filter((row) => row.status === "connected" || row.has_session);
  const visibleAccessItems = accessView === "connected" ? connectedItems : items;

  const loadTranscription = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/settings/transcription`);
      if (!res.ok) return;
      setTranscription(await res.json());
    } catch {
      setTranscription(null);
    }
  }, []);

  const loadDiscovery = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/settings/discovery`);
      if (!res.ok) return;
      setDiscovery(await res.json());
    } catch {
      setDiscovery(null);
    }
  }, []);

  const load = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/credentials`);
      if (!res.ok) throw new Error("Failed to load credentials");
      const data = await res.json();
      setItems(
        (data.items ?? []).map((row: CredentialRow) => ({
          ...row,
          site_url: row.site_url || "",
        })),
      );
    } catch {
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadSystem = useCallback(async () => {
    setSysLoading(true);
    try {
      // Prefer Next.js stack routes (works even if FastAPI is stale/down)
      const res = await fetch("/api/stack/status");
      if (!res.ok) throw new Error("status failed");
      const data = await res.json();
      setProcesses(data.processes ?? []);
      setPlanes(data.control_planes ?? []);
    } catch {
      setProcesses([
        {
          id: "api",
          label: "API",
          status: "down",
          detail: "Stack status unavailable — is Web running?",
          docs_url: API_DOCS,
          can_start: true,
          can_stop: true,
        },
        {
          id: "redis",
          label: "Redis (Celery broker)",
          status: "unknown",
          detail: "—",
          can_start: true,
          can_stop: true,
        },
        {
          id: "celery",
          label: "Celery workers",
          status: "unknown",
          detail: "—",
          can_start: true,
          can_stop: true,
        },
        {
          id: "celery_beat",
          label: "Celery Beat",
          status: "unknown",
          detail: "—",
          can_start: true,
          can_stop: true,
        },
        {
          id: "web",
          label: "Web (Next.js)",
          status: "unknown",
          detail: "—",
          can_start: true,
          can_stop: true,
        },
      ]);
      setPlanes([
        {
          id: "media",
          label: "Media",
          status: "active",
          blurb: "Social posts, videos, websites, podcasts, newsletters and channels",
          home: "/media/sources",
          docs_url: API_DOCS,
        },
        { id: "finance", label: "Finance", status: "planned", blurb: "Markets, filings, companies, securities and financial signals", home: "/finance" },
        { id: "software", label: "Software", status: "planned", blurb: "Products, vendors, licenses, codebases and digital platforms", home: "/software" },
        { id: "business", label: "Business", status: "planned", blurb: "Companies, ownership, operations, filings and commercial signals", home: "/business" },
        { id: "government", label: "Government", status: "active", blurb: "Agencies, regulations, procurement, public records and policy", home: "/government/sources" },
        { id: "taxes", label: "Taxes", status: "planned", blurb: "Rules, filings, jurisdictions, incentives and compliance signals", home: "/taxes" },
        { id: "healthcare", label: "Healthcare/Medical", status: "planned", blurb: "Providers, facilities, claims, treatments, pharma and clinical signals", home: "/healthcare" },
        { id: "people", label: "People", status: "planned", blurb: "Individuals, roles, relationships, affiliations and influence signals", home: "/people" },
        { id: "geography", label: "Geography", status: "planned", blurb: "Places, regions, borders, corridors and spatial economic signals", home: "/geography" },
        { id: "politics", label: "Politics", status: "planned", blurb: "Campaigns, officials, legislation, elections and civic power signals", home: "/politics" },
        { id: "nonprofit", label: "Non-profit", status: "planned", blurb: "Orgs, missions, funding, grants, programs and civic initiatives", home: "/nonprofit" },
        { id: "news", label: "News", status: "planned", blurb: "Published events, claims, organizations, people and developing stories" },
        { id: "real_estate", label: "Real Estate", status: "planned", blurb: "Parcels, buildings, owners, liens, zoning, permits and transactions", home: "/real-estate" },
        { id: "auctions", label: "Auctions", status: "planned", blurb: "HOA, tax, foreclosure and public auctions — lots, dates, bidders and jurisdictions", home: "/auctions" },
        { id: "torrents", label: "Torrents", status: "planned", blurb: "Torrent indexes, releases, magnets, swarm activity and distribution signals", home: "/torrents" },
        { id: "trademarks", label: "Trademarks", status: "active", blurb: "Marks, owners, classes, status, prosecution history and related brands", home: "/trademarks/sources" },
        { id: "domain_names", label: "Domains", status: "active", blurb: "www, .net and other TLDs — registries, WHOIS, DNS, availability and ownership", home: "/domain-names/sources" },
        { id: "library", label: "Library", status: "active", blurb: "Lessons from courses, books, and videos — text, PDF, and video by topic", home: "/library/lessons" },
        { id: "patents", label: "Patents", status: "planned", blurb: "Applications, grants, claims, inventors, assignees, citations and legal status" },
        { id: "songs", label: "Songs", status: "planned", blurb: "Musical compositions and associated writers, publishers and rights" },
        { id: "music", label: "Music", status: "planned", blurb: "Sound recordings, releases, artists, labels and catalogs" },
        { id: "books", label: "Books", status: "planned", blurb: "Published works, editions, authors, publishers, rights and sales signals" },
        { id: "movies", label: "Movies", status: "planned", blurb: "Films, television, video works, production entities and distribution rights" },
        { id: "fiction", label: "Fiction", status: "planned", blurb: "Unpublished or independently created stories, characters, settings and story worlds" },
      ].sort((a, b) => a.label.localeCompare(b.label)));
    } finally {
      setSysLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    loadSystem();
    loadTranscription();
    loadDiscovery();
  }, [load, loadSystem, loadTranscription, loadDiscovery]);

  useEffect(() => {
    if (tab !== "stack") return;
    const t = setInterval(loadSystem, 8000);
    return () => clearInterval(t);
  }, [tab, loadSystem]);

  const startProcess = async (id: string) => {
    setStartingId(id);
    setError(null);
    try {
      const res = await fetch("/api/stack/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(typeof data.detail === "string" ? data.detail : `Could not start ${id}`);
      }
      setFlash(`Starting ${id}… Refresh status in a few seconds.`);
      setTimeout(loadSystem, 2500);
    } catch (e: any) {
      setError(e.message ?? "Start failed");
    } finally {
      setStartingId(null);
    }
  };

  const stopProcess = async (id: string) => {
    setStoppingId(id);
    setError(null);
    try {
      const res = await fetch("/api/stack/stop", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(typeof data.detail === "string" ? data.detail : `Could not stop ${id}`);
      }
      setFlash(`Stopped ${id}.`);
      setTimeout(loadSystem, 1500);
    } catch (e: any) {
      setError(e.message ?? "Stop failed");
    } finally {
      setStoppingId(null);
    }
  };

  const resetAdd = () => {
    setEditingId(null);
    setPlatform("facebook");
    setUsername("");
    setSiteUrl("");
    setPassword("");
    setShowPw(false);
    setError(null);
  };

  const selectPlatform = (next: Platform) => {
    setPlatform(next);
    if (next === "website") {
      setSiteUrl((current) => current.trim() || DEFAULT_WEBSITE_APP_URL);
    } else {
      setSiteUrl("");
    }
  };

  const openEdit = (row: CredentialRow) => {
    setEditingId(row.id);
    setPlatform(row.platform);
    setUsername(row.username);
    setSiteUrl(
      row.site_url?.trim() ||
        (row.platform === "website" ? DEFAULT_WEBSITE_APP_URL : ""),
    );
    setPassword("");
    setShowPw(false);
    setError(null);
    setShowAdd(true);
  };

  const openFacebookLogin = () => {
    window.open("https://www.facebook.com/login", "fb-login", "noopener,noreferrer,width=520,height=720");
    setFlash("Log in to Facebook in the popup, then paste full cookies (or c_user + xs) below.");
  };

  const saveFacebookSession = async () => {
    const fullCookies = (sessionDrafts.facebook?.cookies || "").trim();
    if (!fullCookies && (!cUser.trim() || !xs.trim())) {
      setError("Paste full facebook.com cookies, or both c_user and xs.");
      return;
    }
    setSavingSession(true);
    setError(null);
    try {
      const body = fullCookies
        ? { cookies: fullCookies, username: fbLabel.trim() || undefined }
        : {
            c_user: cUser.trim(),
            xs: xs.trim(),
            username: fbLabel.trim() || undefined,
          };
      const res = await fetch(`${API_BASE}/api/v1/credentials/facebook/session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail =
          typeof data.detail === "string"
            ? data.detail
            : Array.isArray(data.detail)
              ? data.detail.map((d: any) => d.msg || JSON.stringify(d)).join("; ")
              : `Failed to save session (${res.status})`;
        throw new Error(detail);
      }
      setCUser("");
      setXs("");
      setFbLabel("");
      setSessionDrafts((current) => ({
        ...current,
        facebook: { cookies: "", label: "" },
      }));
      setFlash(
        fullCookies
          ? "Facebook session connected with full cookies — re-run Discover on CrypticCash."
          : "Facebook session connected — Discover can use this login for reels."
      );
      await load();
      setShowFacebookSetup(false);
    } catch (e: any) {
      setError(e.message ?? "Failed to save session");
    } finally {
      setSavingSession(false);
    }
  };

  const savePlatformSession = async (platformId: Platform) => {
    const draft = sessionDrafts[platformId] ?? { cookies: "", label: "" };
    if (!draft.cookies.trim()) {
      setError(`Paste ${PLATFORM_LABELS[platformId]} cookies first.`);
      return;
    }
    setSavingSessionPlatform(platformId);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/credentials/${platformId}/session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cookies: draft.cookies.trim(),
          username: draft.label.trim() || undefined,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail =
          typeof data.detail === "string"
            ? data.detail
            : Array.isArray(data.detail)
              ? data.detail.map((d: any) => d.msg || JSON.stringify(d)).join("; ")
              : `Failed to save ${platformId} session (${res.status})`;
        throw new Error(detail);
      }
      setSessionDrafts((current) => ({
        ...current,
        [platformId]: { cookies: "", label: "" },
      }));
      setShowSessionSetup((current) => ({ ...current, [platformId]: false }));
      setFlash(`${PLATFORM_LABELS[platformId]} session connected.`);
      await load();
    } catch (e: any) {
      setError(e.message ?? "Failed to save session");
    } finally {
      setSavingSessionPlatform(null);
    }
  };

  const handleAdd = async () => {
    if (!username.trim()) {
      setError("Username is required.");
      return;
    }
    if (!editingId && !password) {
      setError("Platform, username, and password are required.");
      return;
    }
    if (platform === "website" && !siteUrl.trim()) {
      setError("Website / App URL is required for website credentials.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const res = editingId
        ? await fetch(`${API_BASE}/api/v1/credentials/${editingId}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              username: username.trim(),
              site_url:
                platform === "website"
                  ? (siteUrl.trim() || DEFAULT_WEBSITE_APP_URL)
                  : "",
              ...(password ? { password } : {}),
            }),
          })
        : await fetch(`${API_BASE}/api/v1/credentials`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              platform,
              username: username.trim(),
              password,
              site_url:
                platform === "website"
                  ? (siteUrl.trim() || DEFAULT_WEBSITE_APP_URL)
                  : undefined,
            }),
          });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : editingId
              ? "Failed to update credential"
              : "Failed to add credential",
        );
      }
      // Keep table in sync immediately (Website / App included).
      if (data?.id) {
        const mapped: CredentialRow = {
          id: String(data.id),
          platform: data.platform,
          username: data.username,
          site_url: data.site_url || (data.platform === "website" ? DEFAULT_WEBSITE_APP_URL : ""),
          has_password: Boolean(data.has_password),
          has_session: Boolean(data.has_session),
          status: data.status,
          last_error: data.last_error ?? null,
          last_verified_at: data.last_verified_at ?? null,
          updated_at: data.updated_at ?? null,
        };
        setItems((prev) => {
          const idx = prev.findIndex((r) => r.id === mapped.id);
          if (idx >= 0) {
            const next = [...prev];
            next[idx] = mapped;
            return next;
          }
          return [mapped, ...prev];
        });
      }
      setShowAdd(false);
      resetAdd();
      setFlash(editingId ? "Credential updated." : "Credential added.");
      await load();
    } catch (e: any) {
      setError(e.message ?? "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    setBusyId(id);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/credentials/${id}`, { method: "DELETE" });
      if (!res.ok && res.status !== 204) throw new Error("Delete failed");
      setItems((prev) => prev.filter((r) => r.id !== id));
    } catch (e: any) {
      setError(e.message ?? "Delete failed");
    } finally {
      setBusyId(null);
    }
  };

  const saveTranscription = async () => {
    if (!transcription) return;
    setSavingTranscription(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/settings/transcription`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          engine: transcription.engine,
          model: transcription.model,
          language: transcription.language,
          keep_audio: transcription.keep_audio,
          concurrency: transcription.concurrency,
          batch_size: transcription.batch_size,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail ?? "Could not save transcription settings");
      setTranscription(data);
      setFlash("Transcription settings saved.");
    } catch (e: any) {
      setError(e.message ?? "Could not save transcription settings");
    } finally {
      setSavingTranscription(false);
    }
  };

  const saveDiscovery = async () => {
    if (!discovery) return;
    setSavingDiscovery(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/settings/discovery`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(discovery),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail ?? "Could not save discovery settings");
      setDiscovery(data);
      setFlash("Discovery settings saved.");
    } catch (e: any) {
      setError(e.message ?? "Could not save discovery settings");
    } finally {
      setSavingDiscovery(false);
    }
  };

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: "stack", label: "Stack status", icon: <Server className="w-3.5 h-3.5" /> },
    { id: "planes", label: "Control planes", icon: <Layers className="w-3.5 h-3.5" /> },
    { id: "discovery", label: "Discovery", icon: <RefreshCw className="w-3.5 h-3.5" /> },
    { id: "transcription", label: "Transcription", icon: <FileAudio className="w-3.5 h-3.5" /> },
    { id: "access", label: "Access", icon: <KeyRound className="w-3.5 h-3.5" /> },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <AppPageHeader
        title="Settings"
        icon={
          <div className="p-1.5 bg-primary/10 rounded-lg">
            <Icon name="settings" className="w-5 h-5 text-primary" />
          </div>
        }
        description="Stack processes, domain control planes, and platform access credentials."
        actions={
          tab === "access" ? (
            <Button onClick={() => { resetAdd(); setShowAdd(true); }} className="gap-2 shrink-0">
              <Icon name="plus" className="w-4 h-4" /> Add
            </Button>
          ) : (
            <Button
              variant="outline"
              onClick={
                tab === "discovery"
                  ? loadDiscovery
                  : tab === "transcription"
                    ? loadTranscription
                    : loadSystem
              }
              className="gap-2 shrink-0"
              disabled={(tab === "stack" || tab === "planes") && sysLoading}
            >
              <RefreshCw className={`w-4 h-4 ${(tab === "stack" || tab === "planes") && sysLoading ? "animate-spin" : ""}`} /> Refresh
            </Button>
          )
        }
      />

      <div className="flex items-center gap-1 p-1 rounded-xl bg-muted/40 border border-border/50 w-fit">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`inline-flex items-center gap-1.5 text-xs font-medium px-3.5 py-1.5 rounded-lg transition-colors ${
              tab === t.id
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      {flash && (
        <div className="flex items-start gap-2 text-sm text-primary bg-primary/5 border border-primary/20 rounded-xl px-4 py-3">
          <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0" /> {flash}
        </div>
      )}
      {error && !showAdd && (
        <div className="flex items-start gap-2 text-sm text-red-400 bg-red-500/5 border border-red-500/20 rounded-xl px-4 py-3">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" /> {error}
        </div>
      )}

      {tab === "stack" && (
        <div className="space-y-4">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <p className="text-sm text-muted-foreground max-w-2xl">
              <span className="text-foreground font-medium">Start</span> opens a console shell
              (same commands as <span className="font-mono text-xs">v2/.startup</span>).{" "}
              <span className="text-foreground font-medium">Stop</span> kills that process.
            </p>
            <a
              href={API_DOCS}
              target="_blank"
              rel="noreferrer"
              className="text-fine font-bold uppercase tracking-wider text-primary inline-flex items-center gap-1 hover:underline shrink-0"
            >
              API docs <ExternalLink className="w-3 h-3" />
            </a>
          </div>
          {sysLoading && processes.length === 0 && (
            <p className="text-sm text-muted-foreground flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" /> Checking…
            </p>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            {processes.map((p) => (
              <Card
                key={p.id}
                className="shadow-sm border-border/50 rounded-2xl p-4 flex flex-col gap-3"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <h3 className="font-display text-sm font-semibold tracking-tight truncate">
                      {p.label}
                    </h3>
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                      {p.detail || "—"}
                    </p>
                  </div>
                  <ProcessPill status={p.status} />
                </div>
                <div className="mt-auto flex flex-wrap items-center gap-2">
                  {p.docs_url && (
                    <a
                      href={p.docs_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-fine text-primary inline-flex items-center gap-0.5 hover:underline"
                    >
                      docs <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                  {p.can_start !== false && (
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={startingId === p.id || p.status === "up"}
                      onClick={() => startProcess(p.id)}
                      className="h-8 min-w-[5.75rem] justify-center gap-1.5 text-fine font-bold uppercase tracking-wider border-emerald-600/40 text-emerald-700 hover:bg-emerald-600/10 hover:text-emerald-800 dark:border-emerald-500/40 dark:text-emerald-400 dark:hover:bg-emerald-500/10 dark:hover:text-emerald-300"
                    >
                      {startingId === p.id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Play className="w-3.5 h-3.5" />
                      )}
                      Start
                    </Button>
                  )}
                  {p.can_stop !== false && p.id !== "postgres" && (
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={stoppingId === p.id || p.status === "down"}
                      onClick={() => stopProcess(p.id)}
                      className="h-8 min-w-[5.75rem] justify-center gap-1.5 text-fine font-bold uppercase tracking-wider border-red-600/40 text-red-700 hover:bg-red-600/10 hover:text-red-800 dark:border-red-500/40 dark:text-red-400 dark:hover:bg-red-500/10 dark:hover:text-red-300"
                    >
                      {stoppingId === p.id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Square className="w-3.5 h-3.5" />
                      )}
                      Stop
                    </Button>
                  )}
                  {p.id === "postgres" && (
                    <span className="text-fine text-muted-foreground">external</span>
                  )}
                </div>
              </Card>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            Cheat sheet: <span className="font-mono">v2/.startup</span>
          </p>
        </div>
      )}

      {tab === "planes" && (
        <div className="space-y-4">
          <p className="text-sm text-muted-foreground max-w-2xl">
            <span className="text-foreground font-medium">Intelligence</span> is the platform.
            Each domain below is a control plane (Media is live; others are planned).
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {(planes.length ? planes : []).map((plane) => {
            const card = (
              <Card
                key={plane.id}
                className={`shadow-sm border-border/50 rounded-2xl p-4 transition-colors h-full ${
                  plane.status === "active" ? "hover:border-primary/40" : "opacity-75"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <h3 className="font-display text-sm font-semibold tracking-tight">{plane.label}</h3>
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-3">{plane.blurb}</p>
                  </div>
                  <ProcessPill status={plane.status === "active" ? "active" : "planned"} />
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {plane.home && plane.status === "active" && (
                    <Link href={plane.home}>
                      <Button size="sm" className="gap-1.5">
                        Open workspace
                      </Button>
                    </Link>
                  )}
                  {plane.docs_url && (
                    <a href={plane.docs_url} target="_blank" rel="noreferrer">
                      <Button size="sm" variant="outline" className="gap-1.5">
                        API docs <ExternalLink className="w-3.5 h-3.5" />
                      </Button>
                    </a>
                  )}
                </div>
              </Card>
            );
            return card;
          })}
          {!sysLoading && planes.length === 0 && (
            <p className="text-sm text-muted-foreground">No control plane metadata.</p>
          )}
          </div>
        </div>
      )}

      {tab === "discovery" && (
        <Card className="shadow-sm border-border/50 rounded-2xl overflow-hidden">
          <CardHeader className="bg-muted/30 border-b border-border/50 py-4">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <RefreshCw className="w-4 h-4 text-primary" />
              Autorun discovery
            </CardTitle>
          </CardHeader>
          <div className="p-5 space-y-5 max-w-2xl">
            {!discovery ? (
              <div className="text-sm text-muted-foreground flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" /> Loading…
              </div>
            ) : (
              <>
                <p className="text-sm text-muted-foreground">
                  Sources with Autorun enabled are checked on this schedule. Discovery catalogs
                  new posts; turn on <strong>Auto-transcribe</strong> per source to keep
                  transcribing in batches (Settings → Transcription) until pending is done.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      Check every
                    </label>
                    <Select
                      value={String(discovery.interval_minutes)}
                      onValueChange={(value) =>
                        setDiscovery((current) =>
                          current ? { ...current, interval_minutes: Number(value) } : current
                        )
                      }
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="15">15 minutes</SelectItem>
                        <SelectItem value="30">30 minutes</SelectItem>
                        <SelectItem value="60">1 hour</SelectItem>
                        <SelectItem value="180">3 hours</SelectItem>
                        <SelectItem value="360">6 hours</SelectItem>
                        <SelectItem value="720">12 hours</SelectItem>
                        <SelectItem value="1440">24 hours</SelectItem>
                        <SelectItem value="10080">7 days</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      Maximum items per stream
                    </label>
                    <Input
                      type="number"
                      min={1}
                      max={5000}
                      value={discovery.max_items}
                      onChange={(event) =>
                        setDiscovery((current) =>
                          current
                            ? { ...current, max_items: Number(event.target.value) || 1 }
                            : current
                        )
                      }
                    />
                    <p className="text-xs text-muted-foreground">
                      Used for manual discover, Discover All, and Autorun. Up to 5,000.
                    </p>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      Media list page size
                    </label>
                    <Input
                      type="number"
                      min={50}
                      max={5000}
                      value={discovery.media_page_size}
                      onChange={(event) =>
                        setDiscovery((current) =>
                          current
                            ? {
                                ...current,
                                media_page_size: Number(event.target.value) || 50,
                              }
                            : current
                        )
                      }
                    />
                    <p className="text-xs text-muted-foreground">
                      Max items loaded per source or Intelligence view. Up to 5,000.
                    </p>
                  </div>
                </div>
                <div className="rounded-xl border border-border/50 bg-muted/20 px-4 py-3 text-xs text-muted-foreground">
                  Celery Beat must be running using step 4 in <code>v2/.startup</code>.
                  Paused sources and sources with Autorun off are skipped for Discover Autorun.
                </div>
                <Button onClick={saveDiscovery} disabled={savingDiscovery}>
                  {savingDiscovery && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                  Save discovery settings
                </Button>
              </>
            )}
          </div>
        </Card>
      )}

      {tab === "transcription" && (
        <Card className="shadow-sm border-border/50 rounded-2xl overflow-hidden">
          <CardHeader className="bg-muted/30 border-b border-border/50 py-4">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <FileAudio className="w-4 h-4 text-primary" />
              Transcription
            </CardTitle>
          </CardHeader>
          <div className="p-5 space-y-5 max-w-2xl">
            {!transcription ? (
              <div className="text-sm text-muted-foreground flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" /> Loading…
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      Engine
                    </label>
                    <Select
                      value={transcription.engine}
                      onValueChange={(engine) =>
                        setTranscription((current) => {
                          if (!current) return current;
                          const models =
                            engine === "openai"
                              ? current.openai_models ?? ["whisper-1", "gpt-4o-transcribe", "gpt-4o-mini-transcribe"]
                              : current.whisper_models ?? current.available_models;
                          return {
                            ...current,
                            engine,
                            model: models[0] ?? current.model,
                            available_models: models,
                          };
                        })
                      }
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="whisper_cpp">Local whisper.cpp</SelectItem>
                        <SelectItem value="openai">OpenAI API</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      Model
                    </label>
                    <Select
                      value={transcription.model}
                      onValueChange={(model) =>
                        setTranscription((current) =>
                          current ? { ...current, model, model_installed: false } : current
                        )
                      }
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {transcription.available_models.map((model) => (
                          <SelectItem key={model} value={model}>{model}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      Language
                    </label>
                    <Select
                      value={transcription.language}
                      onValueChange={(language) =>
                        setTranscription((current) =>
                          current ? { ...current, language } : current
                        )
                      }
                    >
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="auto">Auto detect</SelectItem>
                        <SelectItem value="en">English</SelectItem>
                        <SelectItem value="es">Spanish</SelectItem>
                        <SelectItem value="fr">French</SelectItem>
                        <SelectItem value="de">German</SelectItem>
                        <SelectItem value="it">Italian</SelectItem>
                        <SelectItem value="pt">Portuguese</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <label className="flex items-center gap-3 self-end h-10 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={transcription.keep_audio}
                      onChange={(event) =>
                        setTranscription((current) =>
                          current ? { ...current, keep_audio: event.target.checked } : current
                        )
                      }
                      className="accent-primary"
                    />
                    <span className="text-sm">Keep downloaded audio</span>
                  </label>
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      Max concurrent jobs
                    </label>
                    <Input
                      type="number"
                      min={1}
                      max={16}
                      value={transcription.concurrency ?? 1}
                      onChange={(event) =>
                        setTranscription((current) =>
                          current
                            ? {
                                ...current,
                                concurrency: Math.max(
                                  1,
                                  Math.min(16, Number(event.target.value) || 1),
                                ),
                              }
                            : current
                        )
                      }
                    />
                    <p className="text-[11px] text-muted-foreground leading-snug">
                      Auto-enqueue pauses while this many transcription jobs are already running.
                      Keep at 1 for local whisper with a solo worker.
                    </p>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      Auto-enqueue batch
                    </label>
                    <Input
                      type="number"
                      min={1}
                      max={200}
                      value={transcription.batch_size ?? 20}
                      onChange={(event) =>
                        setTranscription((current) =>
                          current
                            ? {
                                ...current,
                                batch_size: Math.max(
                                  1,
                                  Math.min(200, Number(event.target.value) || 20),
                                ),
                              }
                            : current
                        )
                      }
                    />
                    <p className="text-[11px] text-muted-foreground leading-snug">
                      Keeps at most this many jobs in the queue+running pipeline for
                      Auto-transcribe sources, then tops up the next batch until the channel
                      is done. Manual Transcribe all ignores this cap.
                    </p>
                  </div>
                </div>

                {transcription.engine === "whisper_cpp" ? (
                  <div className="rounded-xl border border-border/50 bg-muted/20 px-4 py-3 text-sm">
                    <div className="flex flex-wrap gap-x-5 gap-y-1">
                      <span>
                        whisper.cpp:{" "}
                        <strong className={transcription.whisper_installed ? "text-emerald-500" : "text-amber-500"}>
                          {transcription.whisper_installed ? "installed" : "not installed"}
                        </strong>
                      </span>
                      <span>
                        Selected model:{" "}
                        <strong className={transcription.model_installed ? "text-emerald-500" : "text-amber-500"}>
                          {transcription.model_installed ? "installed" : "not installed"}
                        </strong>
                      </span>
                    </div>
                    {!transcription.model_installed && (
                      <code className="block mt-2 text-xs break-all text-muted-foreground">
                        powershell -ExecutionPolicy Bypass -File .\infra\whisper\install-whisper.ps1 -Model {transcription.model}
                      </code>
                    )}
                    <p className="mt-2 text-xs text-muted-foreground">
                      Local compute only — no per-minute API fee.
                    </p>
                  </div>
                ) : (
                  <div className="rounded-xl border border-border/50 bg-muted/20 px-4 py-3 text-sm space-y-2">
                    <div>
                      API key:{" "}
                      <strong className={transcription.openai_configured ? "text-emerald-500" : "text-amber-500"}>
                        {transcription.openai_configured ? "configured" : "missing in v2/.env"}
                      </strong>
                    </div>
                    {!transcription.openai_configured && (
                      <p className="text-xs text-muted-foreground">
                        Set <code>OPENAI_API_KEY</code> in <code>v2/.env</code> and restart API + Celery workers.
                      </p>
                    )}
                    {transcription.pricing && (
                      <div className="text-xs text-muted-foreground space-y-1 pt-1 border-t border-border/40">
                        <p>{transcription.pricing.note}</p>
                        {(["whisper-1", "gpt-4o-transcribe", "gpt-4o-mini-transcribe"] as const).map((model) => {
                          const row = transcription.pricing?.openai[model];
                          if (!row) return null;
                          return (
                            <p key={model}>
                              <strong className="text-foreground">{model}</strong>:{" "}
                              ${row.usd_per_minute.toFixed(3)}/min (${row.usd_per_hour.toFixed(2)}/hr) · ~
                              ${row.usd_per_word_estimate.toFixed(5)}/word at ~
                              {transcription.pricing?.words_per_minute_estimate} wpm
                            </p>
                          );
                        })}
                        <p className="pt-1">
                          Example: a 60s reel ≈ ${(transcription.pricing.openai[transcription.model]?.usd_per_minute ?? 0.006).toFixed(3)} with {transcription.model}.
                        </p>
                      </div>
                    )}
                  </div>
                )}

                <Button onClick={saveTranscription} disabled={savingTranscription}>
                  {savingTranscription && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                  Save transcription settings
                </Button>
              </>
            )}
          </div>
        </Card>
      )}

      {tab === "access" && (
        <>
          <Card className="shadow-sm border-border/50 overflow-hidden rounded-2xl">
            <CardHeader className="bg-muted/30 border-b border-border/50 py-4">
              <CardTitle className="text-sm font-medium flex items-center justify-between gap-3">
                <span className="inline-flex items-center gap-2">
                  <PlatformBadge platform="facebook" variant="logo" />
                  Facebook access
                </span>
                <span className="inline-flex items-center gap-3">
                  {facebookConnected ? (
                    <span className="text-fine font-bold uppercase tracking-wider text-emerald-500 inline-flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Connected
                    </span>
                  ) : (
                    <span className="text-fine text-muted-foreground">Not connected</span>
                  )}
                  {facebookConnected && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="h-8 text-xs"
                      onClick={() => setShowFacebookSetup((visible) => !visible)}
                    >
                      {showFacebookSetup ? "Close" : "Edit session"}
                    </Button>
                  )}
                </span>
              </CardTitle>
            </CardHeader>
            {(!facebookConnected || showFacebookSetup) && (
            <div className="p-5 space-y-5">
              <p className="text-sm text-muted-foreground max-w-2xl">
                Pages with 100+ reels need a full browser cookie paste (not just{" "}
                <span className="font-mono text-xs">c_user</span>/<span className="font-mono text-xs">xs</span>).
                Facebook soft-caps anonymous grids around ~70 tiles.
              </p>
              <Button
                type="button"
                onClick={openFacebookLogin}
                className="h-11 px-5 gap-2 font-semibold text-white border-0"
                style={{ backgroundColor: "#1877F2" }}
              >
                Continue with Facebook
                <ExternalLink className="w-3.5 h-3.5 opacity-80" />
              </Button>
              <div className="space-y-1.5 max-w-2xl">
                <label className="text-fine font-bold uppercase tracking-widest text-muted-foreground">
                  Full cookies (recommended)
                </label>
                <Textarea
                  rows={5}
                  className="font-mono text-xs"
                  placeholder="Paste Cookie header or Netscape export from facebook.com…"
                  value={sessionDrafts.facebook?.cookies ?? ""}
                  onChange={(e) =>
                    setSessionDrafts((current) => ({
                      ...current,
                      facebook: {
                        cookies: e.target.value,
                        label: current.facebook?.label ?? "",
                      },
                    }))
                  }
                />
              </div>
              <div className="grid gap-3 sm:grid-cols-2 max-w-2xl">
                <div className="space-y-1.5">
                  <label className="text-fine font-bold uppercase tracking-widest text-muted-foreground">c_user (fallback)</label>
                  <Input value={cUser} onChange={(e) => setCUser(e.target.value)} className="font-mono text-sm" autoComplete="off" />
                </div>
                <div className="space-y-1.5">
                  <label className="text-fine font-bold uppercase tracking-widest text-muted-foreground">xs (fallback)</label>
                  <Input value={xs} onChange={(e) => setXs(e.target.value)} className="font-mono text-sm" autoComplete="off" />
                </div>
                <div className="space-y-1.5 sm:col-span-2">
                  <label className="text-fine font-bold uppercase tracking-widest text-muted-foreground">Label (optional)</label>
                  <Input value={fbLabel} onChange={(e) => setFbLabel(e.target.value)} placeholder={fbRow?.username || "facebook-session"} />
                </div>
              </div>
              <Button
                onClick={saveFacebookSession}
                disabled={
                  savingSession ||
                  (!(sessionDrafts.facebook?.cookies || "").trim() && (!cUser.trim() || !xs.trim()))
                }
                className="gap-1.5"
              >
                {savingSession && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                Save Facebook session
              </Button>
            </div>
            )}
          </Card>

          {SESSION_PLATFORMS.map((sessionPlatform) => {
            const row = items.find((item) => item.platform === sessionPlatform.id);
            const connected = Boolean(row?.status === "connected" || row?.has_session);
            const showSetup = !connected || Boolean(showSessionSetup[sessionPlatform.id]);
            const draft = sessionDrafts[sessionPlatform.id] ?? { cookies: "", label: "" };
            const saving = savingSessionPlatform === sessionPlatform.id;
            return (
              <Card
                key={sessionPlatform.id}
                className="shadow-sm border-border/50 overflow-hidden rounded-2xl"
              >
                <CardHeader className="bg-muted/30 border-b border-border/50 py-4">
                  <CardTitle className="text-sm font-medium flex items-center justify-between gap-3">
                    <span className="inline-flex items-center gap-2">
                      <PlatformBadge platform={sessionPlatform.id} variant="logo" />
                      {PLATFORM_LABELS[sessionPlatform.id]} access
                    </span>
                    <span className="inline-flex items-center gap-3">
                      {connected ? (
                        <span className="text-fine font-bold uppercase tracking-wider text-emerald-500 inline-flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" /> Connected
                        </span>
                      ) : (
                        <span className="text-fine text-muted-foreground">Not connected</span>
                      )}
                      {connected && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-8 text-xs"
                          onClick={() =>
                            setShowSessionSetup((current) => ({
                              ...current,
                              [sessionPlatform.id]: !current[sessionPlatform.id],
                            }))
                          }
                        >
                          {showSetup && connected ? "Close" : "Edit session"}
                        </Button>
                      )}
                    </span>
                  </CardTitle>
                </CardHeader>
                {showSetup && (
                  <div className="p-5 space-y-4">
                    <p className="text-sm text-muted-foreground max-w-2xl">
                      Log in in your browser, then paste cookies from DevTools → Application → Cookies.
                      {" "}
                      {sessionPlatform.cookieHint}
                    </p>
                    <Button
                      type="button"
                      variant="outline"
                      className="h-10 px-4 gap-2"
                      onClick={() =>
                        window.open(
                          sessionPlatform.loginUrl,
                          `${sessionPlatform.id}-login`,
                          "noopener,noreferrer,width=520,height=720"
                        )
                      }
                    >
                      Open {PLATFORM_LABELS[sessionPlatform.id]} login
                      <ExternalLink className="w-3.5 h-3.5 opacity-80" />
                    </Button>
                    <div className="space-y-1.5 max-w-3xl">
                      <label className="text-fine font-bold uppercase tracking-widest text-muted-foreground">
                        Cookies
                      </label>
                      <Textarea
                        rows={5}
                        value={draft.cookies}
                        onChange={(event) =>
                          setSessionDrafts((current) => ({
                            ...current,
                            [sessionPlatform.id]: {
                              ...draft,
                              cookies: event.target.value,
                            },
                          }))
                        }
                        placeholder={sessionPlatform.placeholder}
                        className="font-mono text-xs"
                      />
                    </div>
                    <div className="space-y-1.5 max-w-3xl">
                      <label className="text-fine font-bold uppercase tracking-widest text-muted-foreground">
                        Label (optional)
                      </label>
                      <Input
                        value={draft.label}
                        onChange={(event) =>
                          setSessionDrafts((current) => ({
                            ...current,
                            [sessionPlatform.id]: {
                              ...draft,
                              label: event.target.value,
                            },
                          }))
                        }
                        placeholder={row?.username || `${sessionPlatform.id}-session`}
                      />
                    </div>
                    <Button
                      onClick={() => savePlatformSession(sessionPlatform.id)}
                      disabled={saving || !draft.cookies.trim()}
                      className="gap-1.5"
                    >
                      {saving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                      Save {PLATFORM_LABELS[sessionPlatform.id]} session
                    </Button>
                  </div>
                )}
              </Card>
            );
          })}

          <Card className="shadow-sm border-border/50 overflow-hidden rounded-2xl">
            <CardHeader className="bg-muted/30 border-b border-border/50 py-4">
              <CardTitle className="text-sm font-medium flex items-center justify-between">
                <span className="inline-flex items-center gap-2">
                  <KeyRound className="w-4 h-4 text-primary" />
                  Stored credentials
                </span>
                <span className="text-fine bg-primary/10 text-primary px-3 py-1 rounded-full border border-primary/20 font-bold">
                  {visibleAccessItems.length} ACCOUNT{visibleAccessItems.length !== 1 ? "S" : ""}
                </span>
              </CardTitle>
            </CardHeader>
            <div className="flex items-center gap-1 p-3 border-b border-border/50 bg-background">
              <button
                type="button"
                onClick={() => setAccessView("all")}
                className={`inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${
                  accessView === "all"
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                }`}
              >
                All credentials
                <span className="text-fine tabular-nums">({items.length})</span>
              </button>
              <button
                type="button"
                onClick={() => setAccessView("connected")}
                className={`inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${
                  accessView === "connected"
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                }`}
              >
                Connected
                <span className="text-fine tabular-nums">({connectedItems.length})</span>
              </button>
            </div>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader className="bg-muted/10">
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="h-11 px-5 text-fine font-bold uppercase tracking-wider w-[72px]">Platform</TableHead>
                    <TableHead className="h-11 px-5 text-fine font-bold uppercase tracking-wider">Website / App</TableHead>
                    <TableHead className="h-11 px-5 text-fine font-bold uppercase tracking-wider">Username</TableHead>
                    <TableHead className="h-11 px-5 text-fine font-bold uppercase tracking-wider w-[120px]">Session</TableHead>
                    <TableHead className="h-11 px-5 text-fine font-bold uppercase tracking-wider w-[120px]">Status</TableHead>
                    <TableHead className="h-11 px-5 text-fine font-bold uppercase tracking-wider w-[100px] text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {loading && (
                    <TableRow>
                      <TableCell colSpan={6} className="h-24 text-center text-muted-foreground text-sm">
                        <Loader2 className="w-4 h-4 animate-spin inline mr-2" /> Loading…
                      </TableCell>
                    </TableRow>
                  )}
                  {!loading && visibleAccessItems.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={6} className="h-24 text-center text-sm text-muted-foreground">
                        {accessView === "connected" ? "No connected accounts yet." : "No credentials yet."}
                      </TableCell>
                    </TableRow>
                  )}
                  {visibleAccessItems.map((row) => {
                    const busy = busyId === row.id;
                    const siteDisplay =
                      row.platform === "website"
                        ? (row.site_url || DEFAULT_WEBSITE_APP_URL).replace(/\/$/, "")
                        : (row.site_url || "").replace(/\/$/, "");
                    return (
                      <TableRow key={row.id} className="h-14">
                        <TableCell className="px-5 py-3">
                          <PlatformBadge platform={row.platform} variant="logo" />
                        </TableCell>
                        <TableCell
                          className="px-5 py-3 text-sm text-muted-foreground truncate max-w-[260px]"
                          title={siteDisplay || undefined}
                        >
                          {siteDisplay
                            ? siteDisplay.replace(/^https?:\/\//, "")
                            : "—"}
                        </TableCell>
                        <TableCell className="px-5 py-3 text-sm font-medium truncate max-w-[280px]">
                          {row.username}
                        </TableCell>
                        <TableCell className="px-5 py-3 text-sm text-muted-foreground">
                          {row.has_session ? "Yes" : "—"}
                        </TableCell>
                        <TableCell className="px-5 py-3">
                          <StatusPill row={row} />
                        </TableCell>
                        <TableCell className="px-5 py-3 text-right">
                          <div className="inline-flex items-center gap-0.5">
                            <Button
                              size="icon"
                              variant="ghost"
                              disabled={busy}
                              onClick={() => openEdit(row)}
                              className="h-8 w-8 text-muted-foreground hover:text-foreground"
                              title="Edit credential"
                            >
                              <Pencil className="w-3.5 h-3.5" />
                            </Button>
                            <Button
                              size="icon"
                              variant="ghost"
                              disabled={busy}
                              onClick={() => handleDelete(row.id)}
                              className="h-8 w-8 text-muted-foreground hover:text-red-500"
                              title="Delete credential"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          </Card>
        </>
      )}

      <Dialog open={showAdd} onOpenChange={(open) => { if (!open) { setShowAdd(false); resetAdd(); } }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{editingId ? "Edit credential" : "Add credential"}</DialogTitle>
            <DialogDescription>
              {editingId
                ? "Update username, website/app, or password. Leave password blank to keep the current one."
                : "Store login access for platforms and websites."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 py-1">
            <div className="space-y-1.5">
              <label className="text-fine font-bold uppercase tracking-widest text-muted-foreground">Platform</label>
              <Select
                value={platform}
                onValueChange={(v) => selectPlatform(v as Platform)}
                disabled={Boolean(editingId)}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {AUTH_PLATFORMS.map((p) => (
                    <SelectItem key={p} value={p}>{PLATFORM_LABELS[p]}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {platform === "website" ? (
              <div className="space-y-1.5">
                <label className="text-fine font-bold uppercase tracking-widest text-muted-foreground">
                  Website / App
                </label>
                <Input
                  type="url"
                  placeholder={DEFAULT_WEBSITE_APP_URL}
                  value={siteUrl}
                  onChange={(e) => setSiteUrl(e.target.value)}
                  autoComplete="url"
                />
                <p className="text-caption text-muted-foreground">
                  Auto-fills to {DEFAULT_WEBSITE_APP_URL.replace(/^https?:\/\//, "")} for Website platform.
                </p>
              </div>
            ) : null}
            <div className="space-y-1.5">
              <label className="text-fine font-bold uppercase tracking-widest text-muted-foreground">Username / email</label>
              <Input autoComplete="username" value={username} onChange={(e) => setUsername(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <label className="text-fine font-bold uppercase tracking-widest text-muted-foreground">
                Password{editingId ? " (optional)" : ""}
              </label>
              <div className="relative">
                <Input
                  type={showPw ? "text" : "password"}
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pr-10"
                  placeholder={editingId ? "Leave blank to keep current" : undefined}
                />
                <button
                  type="button"
                  onClick={() => setShowPw((v) => !v)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground"
                  tabIndex={-1}
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowAdd(false); resetAdd(); }} disabled={saving}>Cancel</Button>
            <Button
              onClick={handleAdd}
              disabled={
                saving ||
                !username.trim() ||
                (!editingId && !password) ||
                (platform === "website" && !siteUrl.trim())
              }
              className="gap-1.5"
            >
              {saving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              {editingId ? "Save" : "Add"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
