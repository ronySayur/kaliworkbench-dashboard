import { useEffect, useMemo, useRef, useState } from "react";
import { getToken } from "../api/client";
import type { LogEvent } from "../api/types";

interface UseJobStreamResult {
  logs: LogEvent[];
  status: string | null;
  exitCode: number | null | undefined;
  connected: boolean;
  error: string | null;
}

export function useJobStream(jobId: number | null, initialStatus?: string): UseJobStreamResult {
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const [status, setStatus] = useState<string | null>(initialStatus ?? null);
  const [exitCode, setExitCode] = useState<number | null | undefined>(undefined);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!jobId) return;
    const token = getToken();
    if (!token) {
      setError("Missing session token");
      return;
    }
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const url = `${proto}://${window.location.host}/ws/jobs/${jobId}?token=${encodeURIComponent(token)}`;
    let cancelled = false;
    let ws: WebSocket | null = null;
    let reconnectTimer: number | null = null;

    const appendEvents = (events: LogEvent[]) => {
      const logEvents = events.filter((e) => e.type === "log");
      if (logEvents.length > 0) {
        setLogs((prev) => {
          const next = [...prev, ...logEvents];
          return next.length > 4000 ? next.slice(next.length - 4000) : next;
        });
      }
      for (const e of events) {
        if (e.type === "status" && e.status) {
          setStatus(e.status);
          if (e.exit_code !== undefined) setExitCode(e.exit_code);
        }
      }
    };

    const connect = () => {
      if (cancelled) return;
      try {
        ws = new WebSocket(url);
        wsRef.current = ws;
      } catch (e) {
        setError("Failed to open WebSocket");
        return;
      }
      ws.onopen = () => {
        if (cancelled) return;
        setConnected(true);
        setError(null);
      };
      ws.onclose = (ev) => {
        if (cancelled) return;
        setConnected(false);
        if (ev.code === 4401) {
          setError("Unauthorized (check session token)");
          return;
        }
        if (ev.code === 4404) {
          setError("Job not found");
          return;
        }
        // reconnect for transient closes unless terminal state known
        reconnectTimer = window.setTimeout(connect, 1500);
      };
      ws.onerror = () => {
        // onclose will handle
      };
      ws.onmessage = (msg) => {
        if (cancelled) return;
        try {
          const data = JSON.parse(msg.data) as LogEvent;
          if (data.type === "replay" && Array.isArray(data.events)) {
            setLogs([]);
            appendEvents(data.events);
          } else if (data.type === "batch" && Array.isArray(data.events)) {
            appendEvents(data.events);
          } else if (data.type === "status") {
            appendEvents([data]);
          } else if (data.type === "log") {
            appendEvents([data]);
          }
        } catch {
          // ignore malformed
        }
      };
    };

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimer) window.clearTimeout(reconnectTimer);
      try {
        wsRef.current?.close();
      } catch {}
      wsRef.current = null;
    };
  }, [jobId]);

  return useMemo(() => ({ logs, status, exitCode, connected, error }), [logs, status, exitCode, connected, error]);
}
