import { useEffect, useRef } from "react";
import type { LogEvent } from "../api/types";

export default function LogViewer({ logs }: { logs: LogEvent[] }) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [logs.length]);

  return (
    <div className="h-96 overflow-auto rounded border border-slate-800 bg-black p-3 font-mono text-xs leading-5">
      {logs.length === 0 ? (
        <div className="text-slate-500">No log output yet.</div>
      ) : (
        <pre className="whitespace-pre-wrap break-words">
          {logs.map((e, idx) => (
            <span
              key={`${e.seq ?? idx}-${idx}`}
              className={e.stream === "stderr" ? "text-red-400" : "text-slate-200"}
            >
              {e.data}
            </span>
          ))}
        </pre>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
