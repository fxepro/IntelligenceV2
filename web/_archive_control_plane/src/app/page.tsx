"use client";

import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Health = { status: string; version: string; topology: string };
type Job = {
  id: string;
  job_type: string;
  status: string;
  progress: number;
  error_message: string | null;
  created_at: string;
};
type Source = {
  id: string;
  name: string | null;
  platform: string;
  source_url: string;
  status: string;
};

function statusPill(status: string) {
  const s = status.toLowerCase();
  if (s === "ok" || s === "completed" || s === "active") return "ok";
  if (s === "failed" || s === "error") return "fail";
  return "warn";
}

export default function HomePage() {
  const [health, setHealth] = useState<Health | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const [h, j, s] = await Promise.all([
        fetch(`${API}/api/v1/health`).then((r) => {
          if (!r.ok) throw new Error(`health ${r.status}`);
          return r.json();
        }),
        fetch(`${API}/api/v1/jobs?limit=10`).then((r) => (r.ok ? r.json() : [])),
        fetch(`${API}/api/v1/sources?domain=media`).then((r) =>
          r.ok ? r.json() : { items: [] },
        ),
      ]);
      setHealth(h);
      setJobs(Array.isArray(j) ? j : []);
      setSources(s.items ?? []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "API unreachable");
      setHealth(null);
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 5000);
    return () => clearInterval(id);
  }, [refresh]);

  const addDemoSource = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/v1/sources`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          domain: "media",
          platform: "youtube",
          source_type: "channel",
          source_url: `https://www.youtube.com/@demo-${Date.now()}`,
          name: "Demo source (v2)",
        }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `create failed ${res.status}`);
      }
      await refresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Create failed");
    } finally {
      setBusy(false);
    }
  };

  const discoverFirst = async () => {
    if (!sources[0]) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/v1/sources/${sources[0].id}/discover`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ max_items: 10 }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? `discover failed ${res.status}`);
      }
      await refresh();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Discover failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main>
      <p className="brand">Media Intelligence · v2</p>
      <h1>Control plane</h1>
      <p className="lede">
        API enqueues jobs; workers discover, acquire, and transcribe. This UI is a thin operator
        surface for Phase A — health, sources, and job status.
      </p>

      {error && (
        <div className="card" style={{ marginBottom: "1rem", borderColor: "var(--fail)" }}>
          <p className="muted" style={{ color: "var(--fail)", margin: 0 }}>
            {error} — is the API up at <code>{API}</code>?
          </p>
        </div>
      )}

      <div className="grid two">
        <section className="card">
          <h2>API health</h2>
          {health ? (
            <>
              <div className="row">
                <span>Status</span>
                <span className={`pill ${statusPill(health.status)}`}>{health.status}</span>
              </div>
              <div className="row">
                <span>Version</span>
                <span>{health.version}</span>
              </div>
              <div className="row">
                <span>Topology</span>
                <span>{health.topology}</span>
              </div>
            </>
          ) : (
            <p className="muted">Waiting for API…</p>
          )}
        </section>

        <section className="card">
          <h2>Actions</h2>
          <p className="muted" style={{ marginTop: 0 }}>
            Create a demo source, then enqueue discover (returns <code>job_id</code> immediately).
          </p>
          <div className="actions">
            <button className="primary" disabled={busy} onClick={addDemoSource}>
              Add demo source
            </button>
            <button disabled={busy || sources.length === 0} onClick={discoverFirst}>
              Discover first source
            </button>
            <button disabled={busy} onClick={refresh}>
              Refresh
            </button>
          </div>
        </section>
      </div>

      <div className="grid two" style={{ marginTop: "1rem" }}>
        <section className="card">
          <h2>Sources ({sources.length})</h2>
          {sources.length === 0 ? (
            <p className="muted">No sources yet.</p>
          ) : (
            sources.slice(0, 8).map((s) => (
              <div className="row" key={s.id}>
                <div>
                  <div>{s.name ?? s.source_url}</div>
                  <div className="muted">
                    {s.platform} · {s.source_url.replace(/^https?:\/\//, "")}
                  </div>
                </div>
                <span className={`pill ${statusPill(s.status)}`}>{s.status}</span>
              </div>
            ))
          )}
        </section>

        <section className="card">
          <h2>Recent jobs ({jobs.length})</h2>
          {jobs.length === 0 ? (
            <p className="muted">No jobs yet.</p>
          ) : (
            jobs.map((j) => (
              <div className="row" key={j.id}>
                <div>
                  <div>
                    {j.job_type} · {j.id.slice(0, 8)}
                  </div>
                  <div className="muted">
                    {Math.round((j.progress || 0) * 100)}%
                    {j.error_message ? ` · ${j.error_message}` : ""}
                  </div>
                </div>
                <span className={`pill ${statusPill(j.status)}`}>{j.status}</span>
              </div>
            ))
          )}
        </section>
      </div>

      <p className="muted" style={{ marginTop: "2rem" }}>
        Docs: <code>docs/New Intelligence Platform Architecture.md</code> · Backstop app in{" "}
        <code>v1/</code>
      </p>
    </main>
  );
}
