import { useState } from "react";
import { apiFetch } from "../api/client";
import type { Asset, RfAnalyzeOut } from "../api/types";

export default function AssetsPanel({
  workspaceId,
  assets,
  onAssetsChange,
}: {
  workspaceId: number;
  assets: Asset[];
  onAssetsChange: (assets: Asset[]) => void;
}) {
  const [nmapXml, setNmapXml] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const parseAndSync = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!nmapXml.trim()) {
      setError("Paste nmap XML output first.");
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const parsed = await apiFetch<{ assets: Array<Record<string, unknown>> }>("/api/asm/parse/nmap", {
        method: "POST",
        body: JSON.stringify({ nmap_xml: nmapXml }),
      });
      if (!Array.isArray(parsed?.assets)) {
        throw new Error("Parser returned no assets array");
      }
      const sync = await apiFetch<{ diff: { added: unknown[]; removed: unknown[]; changed: unknown[] } }>(
        `/api/workspaces/${workspaceId}/assets/sync`,
        { method: "POST", body: JSON.stringify({ assets: parsed.assets }) }
      );
      const refreshed = await apiFetch<Asset[]>(`/api/workspaces/${workspaceId}/assets`);
      onAssetsChange(refreshed);
      setMessage(
        `Synced ${Array.isArray(parsed.assets) ? parsed.assets.length : 0} assets — ` +
          `added: ${sync?.diff?.added?.length ?? 0}, changed: ${sync?.diff?.changed?.length ?? 0}, removed: ${sync?.diff?.removed?.length ?? 0}`
      );
      setNmapXml("");
    } catch (err: any) {
      setError(err?.message || "Failed to parse or sync assets");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-2">
      <h2 className="text-lg font-medium">Assets (attack surface)</h2>
      <form onSubmit={parseAndSync} className="space-y-2 rounded border border-slate-800 p-4">
        <label className="block text-xs text-slate-400">Paste nmap XML output (with open ports)</label>
        <textarea
          value={nmapXml}
          onChange={(e) => setNmapXml(e.target.value)}
          rows={5}
          className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 font-mono text-xs"
          placeholder="<nmaprun>... <port protocol='tcp' portid='443'>..."
        />
        <div className="flex items-center gap-2">
          <button
            type="submit"
            disabled={busy}
            className="rounded bg-cyan-600 px-3 py-1.5 text-sm font-medium hover:bg-cyan-500 disabled:opacity-50"
          >
            Parse &amp; sync
          </button>
          {message && <span className="text-sm text-emerald-400">{message}</span>}
          {error && <span className="text-sm text-red-400">{error}</span>}
        </div>
      </form>
      <div className="rounded border border-slate-800">
        {assets.length === 0 ? (
          <div className="p-3 text-sm text-slate-400">No assets inventoried yet. Paste nmap XML above.</div>
        ) : (
          <ul className="divide-y divide-slate-800 text-sm">
            {assets.map((asset) => (
              <li key={asset.id} className="flex items-center justify-between px-3 py-2">
                <div>
                  <span className="rounded bg-slate-800 px-2 py-0.5 text-xs">{asset.asset_type}</span>{" "}
                  <span className="font-mono">{asset.identifier}</span>
                </div>
                <div className="text-xs text-slate-500">last seen {new Date(asset.last_seen).toLocaleString()}</div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

export function RfAnalyzePanel() {
  const [csvText, setCsvText] = useState("");
  const [trusted, setTrusted] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<RfAnalyzeOut | null>(null);
  const [error, setError] = useState<string | null>(null);

  const analyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!csvText.trim()) {
      setError("Paste airodump-ng CSV output first.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const data = await apiFetch<RfAnalyzeOut>("/api/rf/analyze", {
        method: "POST",
        body: JSON.stringify({
          trusted_bssids: trusted.split(",").map((s) => s.trim()).filter(Boolean),
          csv_text: csvText,
        }),
      });
      setResult(data);
    } catch (err: any) {
      setError(err?.message || "Failed to analyze RF data");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-2">
      <h2 className="text-lg font-medium">RF / rogue-AP analysis</h2>
      <form onSubmit={analyze} className="space-y-2 rounded border border-slate-800 p-4">
        <label className="block text-xs text-slate-400">Trusted BSSIDs (comma-separated)</label>
        <input
          value={trusted}
          onChange={(e) => setTrusted(e.target.value)}
          placeholder="AA:BB:CC:DD:EE:FF, 11:22:33:44:55:66"
          className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 font-mono text-xs"
        />
        <label className="block text-xs text-slate-400">airodump-ng CSV output</label>
        <textarea
          value={csvText}
          onChange={(e) => setCsvText(e.target.value)}
          rows={5}
          className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 font-mono text-xs"
          placeholder="BSSID, First time seen, ...\nAA:BB:CC:DD:EE:FF, ..."
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded bg-cyan-600 px-3 py-1.5 text-sm font-medium hover:bg-cyan-500 disabled:opacity-50"
        >
          Analyze
        </button>
        {error && <div className="text-sm text-red-400">{error}</div>}
      </form>
      {result && (
        <div className="space-y-3">
          <div>
            <h3 className="text-sm font-medium text-slate-300">Networks ({result.networks.length})</h3>
            <ul className="mt-1 space-y-1 text-xs">
              {result.networks.map((n) => (
                <li key={n.bssid} className="font-mono text-slate-300">
                  {n.bssid} {n.ssid || "(hidden)"} ch={n.channel} rssi={n.rssi} {n.encryption}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-medium text-slate-300">Anomalies ({result.anomalies.length})</h3>
            {result.anomalies.length === 0 ? (
              <div className="text-sm text-emerald-400">No unrecognized BSSIDs for known SSIDs.</div>
            ) : (
              <ul className="mt-1 space-y-1 text-xs text-red-400">
                {result.anomalies.map((a) => (
                  <li key={a.ssid} className="font-mono">
                    ⚠ {a.ssid}: unrecognized {a.bssids.join(", ")} — {a.reason}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
