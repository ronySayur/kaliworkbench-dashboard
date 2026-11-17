import { useState } from "react";
import { apiFetch } from "../api/client";
import type { ResponseDiffOut } from "../api/responseDiff";

function parseCommand(input: string): string[] {
  const re = /[^\s"']+|"([^"]*)"|'([^']*)'/g;
  const args: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(input)) !== null) {
    args.push(m[1] ?? m[2] ?? m[0]);
  }
  return args;
}

export default function ResponseDiffPanel({ workspaceId }: { workspaceId: number }) {
  const [sourceCmd, setSourceCmd] = useState("");
  const [targetCmd, setTargetCmd] = useState("");
  const [diffTarget, setDiffTarget] = useState("");
  const [timeout, setTimeoutVal] = useState("10");
  const [result, setResult] = useState<ResponseDiffOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const runDiff = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const source = parseCommand(sourceCmd);
    const target = parseCommand(targetCmd);
    if (source.length === 0 || target.length === 0) {
      setError("Source and target commands are required.");
      return;
    }
    if (!diffTarget.trim()) {
      setError("Target must be an allowlisted host/CIDR for this workspace.");
      return;
    }
    setBusy(true);
    try {
      const data = await apiFetch<ResponseDiffOut>("/api/response-diff", {
        method: "POST",
        body: JSON.stringify({
          workspace_id: workspaceId,
          target: diffTarget.trim(),
          source_command: source,
          target_command: target,
          timeout: Number(timeout) || 10,
        }),
      });
      setResult(data);
    } catch (err: any) {
      setError(err?.message || "Failed to run response diff");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-2 rounded border border-slate-800 p-4">
      <h2 className="text-lg font-medium">Response diff</h2>
      <p className="text-sm text-slate-400">
        Run the same request shape with two command variants and diff the JSON responses (e.g. admin vs user token). Target must be allowlisted.
      </p>
      <form onSubmit={runDiff} className="space-y-2">
        <div>
          <label className="block text-xs text-slate-400">Source command (argv)</label>
          <input
            value={sourceCmd}
            onChange={(e) => setSourceCmd(e.target.value)}
            placeholder="curl -s -H Authorization..."
            className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 font-mono text-sm"
            required
          />
        </div>
        <div>
          <label className="block text-xs text-slate-400">Target command (argv)</label>
          <input
            value={targetCmd}
            onChange={(e) => setTargetCmd(e.target.value)}
            placeholder="curl -s -H Authorization..."
            className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 font-mono text-sm"
            required
          />
        </div>
        <div>
          <label className="block text-xs text-slate-400">Diff target (must be allowlisted)</label>
          <input
            value={diffTarget}
            onChange={(e) => setDiffTarget(e.target.value)}
            placeholder="e.g. 127.0.0.1 or app.staging.local"
            className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm"
            required
          />
        </div>
        <div>
          <label className="block text-xs text-slate-400">Timeout (seconds)</label>
          <input
            type="number"
            min={1}
            max={300}
            value={timeout}
            onChange={(e) => setTimeoutVal(e.target.value)}
            className="w-32 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={busy}
          className="rounded bg-cyan-600 px-3 py-1.5 text-sm font-medium hover:bg-cyan-500 disabled:opacity-50"
        >
          Run diff
        </button>
      </form>
      {error && <div className="text-sm text-red-400">{error}</div>}
      {result && (
        <div className="space-y-2 rounded border border-slate-800 bg-slate-950/50 p-3 text-sm">
          <div>Same: <span className={result.same ? "text-green-400" : "text-red-400"}>{String(result.same)}</span></div>
          {result.error && <div className="text-red-400">Error: {result.error}</div>}
          {result.differences?.length > 0 && (
            <ul className="space-y-1">
              {result.differences.map((d, idx) => (
                <li key={idx} className="font-mono text-xs">
                  {d.status} {d.path} source={JSON.stringify(d.source_value)} target={JSON.stringify(d.target_value)}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
