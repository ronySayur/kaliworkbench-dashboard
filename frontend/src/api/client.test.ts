import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch, clearToken, getToken, setToken } from "./client";

function mockFetch(status: number, body: unknown) {
  const text = typeof body === "string" ? body : JSON.stringify(body);
  return vi.fn(async () => new Response(text, { status, headers: { "Content-Type": "application/json" } }));
}

describe("apiFetch", () => {
  beforeEach(() => {
    clearToken();
    vi.restoreAllMocks();
  });

  it("attaches the bearer token when present", async () => {
    setToken("secret-token");
    const fetchMock = mockFetch(200, [{ id: 1 }]);
    vi.stubGlobal("fetch", fetchMock);
    const result = await apiFetch<Array<{ id: number }>>("/api/workspaces");
    expect(result).toEqual([{ id: 1 }]);
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(new Headers(init?.headers).get("Authorization")).toBe("Bearer secret-token");
  });

  it("omits the Authorization header when no token is stored", async () => {
    const fetchMock = mockFetch(200, []);
    vi.stubGlobal("fetch", fetchMock);
    await apiFetch("/api/workspaces");
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(new Headers(init?.headers).get("Authorization")).toBeNull();
  });

  it("throws ApiError with the response detail on non-2xx", async () => {
    const fetchMock = mockFetch(403, { detail: "target denied: target not in allowlist" });
    vi.stubGlobal("fetch", fetchMock);
    await expect(apiFetch("/api/workspaces")).rejects.toMatchObject({
      status: 403,
      message: "target denied: target not in allowlist",
    });
    expect(getToken()).toBe("");
  });

  it("setToken trims whitespace and getToken reads it back", () => {
    setToken("  abc  ");
    expect(getToken()).toBe("abc");
    clearToken();
    expect(getToken()).toBe("");
  });
});
