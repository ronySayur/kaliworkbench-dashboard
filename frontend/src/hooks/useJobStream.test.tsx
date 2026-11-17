import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, cleanup } from "@testing-library/react";
import { useJobStream } from "./useJobStream";

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  url: string;
  onopen: (() => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  onclose: ((ev: { code: number }) => void) | null = null;
  onerror: (() => void) | null = null;
  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }
  close() {
    // no-op: prevents reconnect timers firing after unmount
  }
  emit(msg: unknown) {
    this.onmessage?.({ data: JSON.stringify(msg) });
  }
  open() {
    this.onopen?.();
  }
}

describe("useJobStream", () => {
  beforeEach(() => {
    MockWebSocket.instances = [];
    localStorage.setItem("kwb_token", "t");
    vi.stubGlobal("WebSocket", MockWebSocket as unknown as typeof WebSocket);
  });
  afterEach(() => {
    cleanup();
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it("includes the session token in the WS url", () => {
    renderHook(() => useJobStream(42));
    expect(MockWebSocket.instances[0].url).toContain("/ws/jobs/42?token=t");
  });

  it("accumulates log events and surfaces terminal status from batches", () => {
    const { result } = renderHook(() => useJobStream(42));
    const ws = MockWebSocket.instances[0];
    act(() => {
      ws.open();
      ws.emit({ type: "replay", events: [{ type: "log", seq: 1, stream: "stdout", data: "hi\n" }] });
      ws.emit({
        type: "batch",
        events: [
          { type: "log", seq: 2, stream: "stdout", data: "again\n" },
          { type: "status", status: "succeeded", exit_code: 0 },
        ],
      });
    });
    expect(result.current.logs.map((l) => l.data)).toEqual(["hi\n", "again\n"]);
    expect(result.current.status).toBe("succeeded");
    expect(result.current.connected).toBe(true);
  });
});
