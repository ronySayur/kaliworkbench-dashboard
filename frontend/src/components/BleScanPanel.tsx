import { useState } from "react";
import { apiFetch } from "../api/client";

interface BleDevice {
  address: string | null;
  name: string | null;
  rssi: number | null;
  details?: string;
}

interface BleScanOut {
  summary: { count: number; avg_rssi: number | null; min_rssi: number | null; max_rssi: number | null };
  devices: BleDevice[];
}

export default function BleScanPanel() {
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<BleScanOut | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [timeout, setTimeoutVal] = useState("5");

  const scan = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const data = await apiFetch<BleScanOut>("/api/ble/scan", {
        method: "POST",
        body: JSON.stringify({ timeout: Number(timeout) || 5 }),
      });
      setResult(data);
    } catch (err: any) {
      setError(err?.message || "Failed to scan BLE devices");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-2">
      <h2 className="text-lg font-medium">BLE peripheral scan</h2>
      <form onSubmit={scan} className="flex flex-wrap items-end gap-2 rounded border border-slate-800 p-4">
        <div>
          <label className="block text-xs text-slate-400">Timeout (seconds)</label>
          <input
            type="number"
            min={1}
            max={30}
            value={timeout}
            onChange={(e) => setTimeoutVal(e.target.value)}
            className="w-24 rounded border border-slate-700 bg-slate-950 px-2 py-1 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={busy}
          className="rounded bg-cyan-600 px-3 py-1.5 text-sm font-medium hover:bg-cyan-500 disabled:opacity-50"
        >
          {busy ? "Scanning..." : "Scan"}
        </button>
        {error && <div className="w-full text-sm text-red-400">{error}</div>}
      </form>
      {result && (
        <div className="space-y-2 rounded border border-slate-800 p-3 text-sm">
          <div>
            Devices seen: {result.summary.count} — avg RSSI: {result.summary.avg_rssi ?? "n/a"} — range [{result.summary.min_rssi ?? "—"}, {result.summary.max_rssi ?? "—"}]
          </div>
          {result.devices.length === 0 ? (
            <div className="text-slate-400">No BLE devices detected (adapter may be missing or access blocked).</div>
          ) : (
            <ul className="divide-y divide-slate-800 text-xs">
              {result.devices.map((d) => (
                <li key={(d.address || Math.random()) + String(d.rssi)} className="flex items-center justify-between py-1">
                  <span className="font-mono">{d.address}</span>
                  <span className="text-slate-300">{d.name || "(unnamed)"}</span>
                  <span className="text-slate-500">rssi: {d.rssi}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
