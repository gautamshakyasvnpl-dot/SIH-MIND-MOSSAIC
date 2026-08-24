import { describe, expect, it } from "vitest";
import { API_BASE, mediaUrl } from "../api";

describe("mediaUrl", () => {
  it("resolves server-relative API paths against the configured base", () => {
    expect(mediaUrl("/api/audio/x.mp3")).toBe(`${API_BASE}/api/audio/x.mp3`);
  });

  it("adds the leading slash when missing", () => {
    expect(mediaUrl("api/audio/x.mp3")).toBe(`${API_BASE}/api/audio/x.mp3`);
  });

  it("passes absolute URLs through unchanged", () => {
    expect(mediaUrl("https://example.com/a.mp3")).toBe("https://example.com/a.mp3");
  });
});
