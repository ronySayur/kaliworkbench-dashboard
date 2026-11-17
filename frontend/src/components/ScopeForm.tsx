import { useState } from "react";
import { apiFetch } from "../api/client";
import type { Scope } from "../api/types";

export default function ScopeForm({
  workspaceId,
  onCreated,
}: {
  workspaceId: number;
  onCreated: (scope: Scope) => void;
}) {
  const [targetType, setTargetType] = useState<Scope["target_type"]>("IP");
  const [value, setValue] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const scope = await apiFetch<Scope>(`/api/workspaces/${workspaceId}/scopes`, {
        method: "POST",
        body: JSON.stringify({ target_type: targetType, value, notes: notes || null }),
      });
      setValue("");
      setNotes("");
      onCreated(scope);
    } catch (err: any) {
      setError(err?.message || "Failed to create scope");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="flex flex-wrap items-end gap-2 rounded border border-slate-800 p-3">
      <div>
        <label className="block text-xs text-slate-400">Type</label>
        <select
          value={targetType}
          onChange={(e) => setTargetType(e.target.value as Scope["target_type"])}
          className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm"
        >
          <option value="IP">IP</option>
          <option value="CIDR">CIDR</option>
          <option value="Domain">Domain</option>
          <option value="MAC">MAC</option>
        </select>
      </div>
      <div className="min-w-[220px] flex-1">
        <label className="block text-xs text-slate-400">Value</label>
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="e.g. 127.0.0.1, 10.0.0.0/24, example.local"
          className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm"
          required
        />
      </div>
      <div className="min-w-[180px] flex-1">
        <label className="block text-xs text-slate-400">Notes (optional)</label>
        <input
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm"
        />
      </div>
      <button
        type="submit"
        disabled={busy}
        className="rounded bg-emerald-600 px-3 py-1.5 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
      >
        Add scope
      </button>
      {error && <div className="w-full text-sm text-red-400">{error}</div>}
    </form>
  );
}
