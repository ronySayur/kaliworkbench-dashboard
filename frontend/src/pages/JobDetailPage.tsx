import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiFetch, getToken } from "../api/client";
import type { Finding, Job } from "../api/types";
import { useJobStream } from "../hooks/useJobStream";
import LogViewer from "../components/LogViewer";

function statusColor(status: string | null | undefined): string {
  switch (status) {
    case "succeeded":
      return "text-green-400";
    case "running":
      return "text-cyan-400";
    case "queued":
      return "text-yellow-400";
    case "failed":
    case "timed_out":
    case "cancelled":
      return "text-red-400";
    default:
      return "text-slate-300";
  }
}

export default function JobDetailPage() {
  const { id } = useParams();
  const jobId = Number(id);
  const [job, setJob] = useState<Job | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const { logs, status, exitCode, connected, error: streamError } = useJobStream(
    Number.isFinite(jobId) ? jobId : null,
    job?.status
  );

  const load = async () => {
    if (!jobId) return;
    try {
      const [data, found] = await Promise.all([
        apiFetch<Job>(`/api/jobs/${jobId}`),
        apiFetch<Finding[]>(`/api/jobs/${jobId}/findings`).catch(() => [] as Finding[]),
      ]);
      setJob(data);
      setFindings(found || []);
      setError(null);
    } catch (e: any) {
      setError(e?.message || "Failed to load job");
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);

  useEffect(() => {
    if (status) {
      setJob((prev) => (prev ? { ...prev, status } : prev));
    }
  }, [status]);

  const cancel = async () => {
    if (!jobId) return;
    setBusy(true);
    try {
      const data = await apiFetch<Job>(`/api/jobs/${jobId}/cancel`, { method: "POST" });
      setJob(data);
    } catch (e: any) {
      setError(e?.message || "Failed to cancel job");
    } finally {
      setBusy(false);
    }
  };

  const downloadJobBlob = async (path: string, filename: string, mime: string) => {
    if (!jobId) return;
    setBusy(true);
    try {
      const token = getToken();
      const res = await fetch(path, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e?.message || "Failed to download report");
    } finally {
      setBusy(false);
    }
  };

  const downloadMarkdown = () =>
    downloadJobBlob(`/api/jobs/${jobId}/report.md`, `kaliworkbench-job-${jobId}.md`, "text/markdown");
  const downloadHtml = () =>
    downloadJobBlob(`/api/jobs/${jobId}/report.html`, `kaliworkbench-job-${jobId}.html`, "text/html");
  const downloadPdf = () =>
    downloadJobBlob(`/api/jobs/${jobId}/report.pdf`, `kaliworkbench-job-${jobId}.pdf`, "application/pdf");

  const downloadSarif = async () => {
    if (!jobId) return;
    setBusy(true);
    try {
      const sarif = await apiFetch<unknown>(`/api/jobs/${jobId}/sarif`);
      const blob = new Blob([JSON.stringify(sarif, null, 2)], { type: "application/sarif+json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `kaliworkbench-job-${jobId}.sarif.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e?.message || "Failed to download SARIF");
    } finally {
      setBusy(false);
    }
  };

  if (!jobId) return <div className="text-red-400">Invalid job id</div>;
  if (error) return <div className="text-red-400">{error}</div>;
  if (!job) return <div className="text-slate-400">Loading...</div>;

  const effectiveStatus = status || job.status;
  const commandArgs = (() => {
    try {
      return JSON.stringify(JSON.parse(job.command_args), null, 2);
    } catch {
      return job.command_args;
    }
  })();

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Job #{job.id}</h1>
          <p className="text-sm text-slate-400">
            Workspace <Link to={`/workspaces/${job.workspace_id}`} className="text-cyan-400 hover:underline">#{job.workspace_id}</Link> • module {job.module}
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={load} className="rounded border border-slate-700 px-3 py-1 text-sm hover:bg-slate-800">
            Refresh
          </button>
          {(effectiveStatus === "queued" || effectiveStatus === "running") && (
            <button
              onClick={cancel}
              disabled={busy}
              className="rounded bg-red-600 px-3 py-1 text-sm font-medium hover:bg-red-500 disabled:opacity-50"
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-2 rounded border border-slate-800 p-4 text-sm">
          <div><span className="text-slate-400">Status:</span> <span className={statusColor(effectiveStatus)}>{effectiveStatus}</span></div>
          <div><span className="text-slate-400">Exit code:</span> {exitCode !== undefined ? (exitCode ?? "—") : (job.exit_code ?? "—")}</div>
          <div><span className="text-slate-400">PID:</span> {job.pid ?? "—"} <span className="text-slate-400">PGID:</span> {job.pgid ?? "—"}</div>
          <div><span className="text-slate-400">Created:</span> {new Date(job.created_at).toLocaleString()}</div>
          <div><span className="text-slate-400">Started:</span> {job.started_at ? new Date(job.started_at).toLocaleString() : "—"}</div>
          <div><span className="text-slate-400">Finished:</span> {job.finished_at ? new Date(job.finished_at).toLocaleString() : "—"}</div>
          <div><span className="text-slate-400">WS:</span> {connected ? <span className="text-green-400">connected</span> : <span className="text-slate-500">disconnected</span>}</div>
          {job.error && <div className="text-red-400">Error: {job.error}</div>}
          {streamError && <div className="text-red-400">Stream: {streamError}</div>}
        </div>
        <div className="rounded border border-slate-800 p-4">
          <div className="mb-2 text-sm text-slate-400">Command / args</div>
          <pre className="max-h-48 overflow-auto text-xs text-slate-200">{commandArgs}</pre>
        </div>
      </div>

      <section className="space-y-2">
        <h2 className="text-lg font-medium">Live logs</h2>
        <LogViewer logs={logs} />
      </section>

      <section className="space-y-2">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">Findings</h2>
          <div className="flex gap-2">
            <button
              onClick={downloadMarkdown}
              disabled={busy}
              className="rounded border border-slate-700 px-3 py-1 text-sm hover:bg-slate-800 disabled:opacity-50"
            >
              Download Markdown
            </button>
            <button
              onClick={downloadHtml}
              disabled={busy}
              className="rounded border border-slate-700 px-3 py-1 text-sm hover:bg-slate-800 disabled:opacity-50"
            >
              Download HTML
            </button>
            <button
              onClick={downloadPdf}
              disabled={busy}
              className="rounded border border-slate-700 px-3 py-1 text-sm hover:bg-slate-800 disabled:opacity-50"
            >
              Download PDF
            </button>
            {findings.length > 0 && (
              <button
                onClick={downloadSarif}
                disabled={busy}
                className="rounded border border-slate-700 px-3 py-1 text-sm hover:bg-slate-800 disabled:opacity-50"
              >
                Download SARIF
              </button>
            )}
          </div>
        </div>
        {findings.length === 0 ? (
          <div className="rounded border border-slate-800 p-4 text-sm text-slate-400">No findings yet.</div>
        ) : (
          <div className="space-y-2">
            {findings.map((f) => (
              <div key={f.id} className="rounded border border-slate-800 p-4 text-sm">
                <div className="flex items-center gap-2">
                  <span className="rounded bg-slate-800 px-2 py-0.5 text-xs uppercase">{f.severity}</span>
                  <span className="font-medium">{f.title}</span>
                </div>
                {f.endpoint_or_device && <div className="mt-1 text-xs text-slate-400 font-mono">{f.endpoint_or_device}</div>}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
