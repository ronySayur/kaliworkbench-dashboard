import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch, ApiError } from "../api/client";
import type { Workspace } from "../api/types";

interface PreflightTool {
  name: string;
  path: string | null;
  version: string | null;
  ok: boolean;
}

export default function WorkspacesPage() {
  const [items, setItems] = useState<Workspace[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [preflight, setPreflight] = useState<PreflightTool[]>([]);

  useEffect(() => {
    apiFetch<{ tools: PreflightTool[] }>("/api/preflight")
      .then((d) => setPreflight(Array.isArray(d?.tools) ? d.tools : []))
      .catch(() => setPreflight([]));
  }, []);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetch<Workspace[]>("/api/workspaces");
      setItems(data);
    } catch (e: any) {
      setError(e?.message || "Failed to load workspaces");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await apiFetch<Workspace>("/api/workspaces", {
        method: "POST",
        body: JSON.stringify({ name, description: description || null }),
      });
      setName("");
      setDescription("");
      await load();
    } catch (e: any) {
      setError(e?.message || "Failed to create workspace");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Workspaces</h1>
        <p className="text-sm text-slate-400">
          Create a workspace and define its target allowlist before running jobs.
        </p>
      </div>

      <form onSubmit={create} className="space-y-3 rounded border border-slate-800 p-4">
        <h2 className="font-medium">New workspace</h2>
        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <label className="block text-xs text-slate-400">Name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm"
              required
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400">Description</label>
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm"
            />
          </div>
        </div>
        <button className="rounded bg-cyan-600 px-3 py-1.5 text-sm font-medium hover:bg-cyan-500">
          Create workspace
        </button>
      </form>

      {preflight.length > 0 && (
        <div className="rounded border border-slate-800 p-4">
          <h2 className="font-medium">Tool health (preflight)</h2>
          <div className="mt-2 grid grid-cols-2 gap-1 text-xs md:grid-cols-4">
            {preflight.map((t) => (
              <div
                key={t.name}
                className={`rounded border px-2 py-1 ${
                  t.ok ? "border-emerald-900 text-emerald-300" : "border-slate-800 text-slate-500"
                }`}
                title={t.ok ? t.version || t.path || "available" : "not installed"}
              >
                {t.ok ? "✓" : "×"} {t.name}
              </div>
            ))}
          </div>
        </div>
      )}

      {error && <div className="rounded border border-red-900 bg-red-950/30 p-3 text-sm text-red-300">{error}</div>}

      <div className="rounded border border-slate-800">
        <div className="border-b border-slate-800 px-4 py-2 font-medium">Existing workspaces</div>
        {loading ? (
          <div className="p-4 text-sm text-slate-400">Loading...</div>
        ) : items.length === 0 ? (
          <div className="p-4 text-sm text-slate-400">No workspaces yet.</div>
        ) : (
          <ul className="divide-y divide-slate-800">
            {items.map((ws) => (
              <li key={ws.id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <div className="font-medium">{ws.name}</div>
                  {ws.description && <div className="text-sm text-slate-400">{ws.description}</div>}
                  <div className="text-xs text-slate-500">ID {ws.id} • {new Date(ws.created_at).toLocaleString()}</div>
                </div>
                <Link
                  to={`/workspaces/${ws.id}`}
                  className="rounded border border-slate-700 px-3 py-1 text-sm hover:bg-slate-800"
                >
                  Open
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
