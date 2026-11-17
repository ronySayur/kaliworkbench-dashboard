import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiFetch } from "../api/client";
import type { Job, Scope, Workspace, Asset } from "../api/types";
import ScopeForm from "../components/ScopeForm";
import ResponseDiffPanel from "../components/ResponseDiffPanel";
import AssetsPanel, { RfAnalyzePanel } from "../components/AssetsPanel";
import BleScanPanel from "../components/BleScanPanel";

function parseCommand(input: string): string[] {
  // split by whitespace but respect simple quoted segments
  const re = /[^\s"']+|"([^"]*)"|'([^']*)'/g;
  const args: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(input)) !== null) {
    args.push(m[1] ?? m[2] ?? m[0]);
  }
  return args;
}

export default function WorkspaceDetailPage() {
  const { id } = useParams();
  const workspaceId = Number(id);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [scopes, setScopes] = useState<Scope[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [jobError, setJobError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [moduleName, setModuleName] = useState("generic");
  const [target, setTarget] = useState("127.0.0.1");
  const [commandStr, setCommandStr] = useState("echo hello-from-kaliworkbench");
  const [timeout, setTimeoutVal] = useState("60");
  const [creatingJob, setCreatingJob] = useState(false);

  const load = async () => {
    if (!workspaceId) return;
    setLoading(true);
    setError(null);
    try {
      const [ws, sc, js, as] = await Promise.all([
        apiFetch<Workspace>(`/api/workspaces/${workspaceId}`),
        apiFetch<Scope[]>(`/api/workspaces/${workspaceId}/scopes`),
        apiFetch<Job[]>(`/api/jobs?workspace_id=${workspaceId}`),
        apiFetch<Asset[]>(`/api/workspaces/${workspaceId}/assets`).catch(() => [] as Asset[]),
      ]);
      setWorkspace(ws);
      setScopes(sc);
      setJobs(js);
      setAssets(as);
    } catch (e: any) {
      setError(e?.message || "Failed to load workspace");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId]);

  const deleteScope = async (scopeId: number) => {
    try {
      await apiFetch<void>(`/api/workspaces/${workspaceId}/scopes/${scopeId}`, { method: "DELETE" });
      setScopes((prev) => prev.filter((s) => s.id !== scopeId));
    } catch (e: any) {
      setError(e?.message || "Failed to delete scope");
    }
  };

  const createJob = async (e: React.FormEvent) => {
    e.preventDefault();
    setJobError(null);
    const command = parseCommand(commandStr);
    if (command.length === 0) {
      setJobError("Command is required");
      return;
    }
    setCreatingJob(true);
    try {
      await apiFetch<Job>(`/api/workspaces/${workspaceId}/jobs`, {
        method: "POST",
        body: JSON.stringify({
          module: moduleName || "generic",
          command,
          target: target || null,
          timeout: timeout ? Number(timeout) : null,
        }),
      });
      await load();
    } catch (e: any) {
      setJobError(e?.message || "Failed to create job");
    } finally {
      setCreatingJob(false);
    }
  };

  if (!workspaceId) return <div className="text-red-400">Invalid workspace id</div>;
  if (loading) return <div className="text-slate-400">Loading...</div>;
  if (error) return <div className="text-red-400">{error}</div>;
  if (!workspace) return <div className="text-red-400">Workspace not found</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{workspace.name}</h1>
          {workspace.description && <p className="text-sm text-slate-400">{workspace.description}</p>}
          <p className="text-xs text-slate-500">Workspace ID {workspace.id}</p>
        </div>
        <button onClick={load} className="rounded border border-slate-700 px-3 py-1 text-sm hover:bg-slate-800">
          Refresh
        </button>
      </div>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Allowed scopes</h2>
        <p className="text-sm text-slate-400">
          Jobs require a target that matches an allowlisted entry for this workspace.
        </p>
        <ScopeForm workspaceId={workspaceId} onCreated={(s) => setScopes((prev) => [s, ...prev])} />
        <div className="rounded border border-slate-800">
          {scopes.length === 0 ? (
            <div className="p-3 text-sm text-slate-400">No scopes yet. Add one to allow job targets.</div>
          ) : (
            <ul className="divide-y divide-slate-800">
              {scopes.map((s) => (
                <li key={s.id} className="flex items-center justify-between px-3 py-2 text-sm">
                  <div>
                    <span className="mr-2 rounded bg-slate-800 px-2 py-0.5 text-xs">{s.target_type}</span>
                    <span className="font-mono">{s.value}</span>
                    {s.notes && <span className="ml-2 text-slate-400">— {s.notes}</span>}
                  </div>
                  <button
                    onClick={() => deleteScope(s.id)}
                    className="text-xs text-red-400 hover:text-red-300"
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Run job (guarded)</h2>
        <form onSubmit={createJob} className="space-y-3 rounded border border-slate-800 p-4">
          <div className="grid gap-3 md:grid-cols-3">
            <div>
              <label className="block text-xs text-slate-400">Module</label>
              <input
                value={moduleName}
                onChange={(e) => setModuleName(e.target.value)}
                className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400">Target (must be allowlisted)</label>
              <input
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm"
                required
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400">Timeout (seconds)</label>
              <input
                type="number"
                min={1}
                max={3600}
                value={timeout}
                onChange={(e) => setTimeoutVal(e.target.value)}
                className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs text-slate-400">Command (argv, space-separated; quotes supported)</label>
            <input
              value={commandStr}
              onChange={(e) => setCommandStr(e.target.value)}
              className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 font-mono text-sm"
              required
            />
            <p className="mt-1 text-xs text-slate-500">
              Example: <code>bash -lc &quot;for i in 1 2 3 4 5; do echo $i; sleep 1; done&quot;</code>
            </p>
          </div>
          <button
            type="submit"
            disabled={creatingJob}
            className="rounded bg-cyan-600 px-3 py-1.5 text-sm font-medium hover:bg-cyan-500 disabled:opacity-50"
          >
            Start job
          </button>
          {jobError && <div className="text-sm text-red-400">{jobError}</div>}
        </form>
      </section>

      <AssetsPanel workspaceId={workspaceId} assets={assets} onAssetsChange={setAssets} />

      <RfAnalyzePanel />

      <BleScanPanel />

      <ResponseDiffPanel workspaceId={workspaceId} />

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Jobs</h2>
        <div className="rounded border border-slate-800">
          {jobs.length === 0 ? (
            <div className="p-3 text-sm text-slate-400">No jobs yet.</div>
          ) : (
            <ul className="divide-y divide-slate-800">
              {jobs.map((j) => (
                <li key={j.id} className="flex items-center justify-between px-3 py-2 text-sm">
                  <div>
                    <div className="font-medium">
                      #{j.id} <span className="text-slate-400">[{j.module}]</span> — {j.status}
                    </div>
                    <div className="text-xs text-slate-500">
                      exit={j.exit_code ?? "—"} • {new Date(j.created_at).toLocaleString()}
                    </div>
                  </div>
                  <Link
                    to={`/jobs/${j.id}`}
                    className="rounded border border-slate-700 px-3 py-1 text-sm hover:bg-slate-800"
                  >
                    View
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </div>
  );
}
