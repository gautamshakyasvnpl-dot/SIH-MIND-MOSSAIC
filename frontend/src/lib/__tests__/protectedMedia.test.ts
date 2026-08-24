import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { API_BASE, fetchProtectedMediaBlobUrl } from "../api";

const JWT = "fake.jwt.value";

describe("fetchProtectedMediaBlobUrl", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  beforeEach(() => {
    const map = new Map<string, string>();
    vi.stubGlobal("localStorage", {
      getItem: (k: string) => map.get(k) ?? null,
      setItem: (k: string, v: string) => void map.set(k, v),
      removeItem: (k: string) => void map.delete(k),
      clear: () => map.clear(),
      key: () => null,
      get length() {
        return map.size;
      },
    } as Storage);
  });

  it("mints a one-time media token and fetches via capability URL with Bearer header, never putting the JWT in a URL", async () => {
    localStorage.setItem("sahaik_token", JWT);
    const seenUrls: string[] = [];
    const fetchMock = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        const url = String(input);
        seenUrls.push(url);
        if (url === `${API_BASE}/api/media/token`) {
          expect(init?.method).toBe("POST");
          expect(JSON.parse(String(init?.body))).toEqual({
            kind: "document_file",
            id: "doc-1",
          });
          return new Response(
            JSON.stringify({ token: "cap123", expires_in: 60, url: "/api/media/cap123" }),
            { status: 200 }
          );
        }
        return new Response("original-bytes", { status: 200 });
      }
    );
    vi.stubGlobal("fetch", fetchMock);

    const blobUrl = await fetchProtectedMediaBlobUrl("document_file", "doc-1");

    expect(blobUrl.startsWith("blob:")).toBe(true);
    URL.revokeObjectURL(blobUrl);
    expect(seenUrls).toEqual([
      `${API_BASE}/api/media/token`,
      `${API_BASE}/api/media/cap123`,
    ]);
    for (const url of seenUrls) expect(url.includes(JWT)).toBe(false);
    const mediaCallInit = fetchMock.mock.calls[1][1];
    expect((mediaCallInit?.headers as Record<string, string>).Authorization).toBe(`Bearer ${JWT}`);
  });

  it("throws a friendly error when the capability fetch fails", async () => {
    localStorage.setItem("sahaik_token", JWT);
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL): Promise<Response> => {
        if (String(input) === `${API_BASE}/api/media/token`) {
          return new Response(
            JSON.stringify({ token: "cap123", expires_in: 60, url: "/api/media/cap123" }),
            { status: 200 }
          );
        }
        return new Response(JSON.stringify({ detail: "expired" }), { status: 404 });
      })
    );

    await expect(fetchProtectedMediaBlobUrl("question_audio", "s-1")).rejects.toThrow(
      "That file link has expired"
    );
  });
});
