import { describe, expect, it, vi } from "vitest";
import api from "./api";

describe("api client", () => {
  it("adds the access token to requests", async () => {
    localStorage.setItem("study_access_token", "token-value");
    const adapter = vi.fn(async (config) => ({ data: {}, status: 200, statusText: "OK", headers: {}, config }));
    await api.get("/test", { adapter });
    expect(adapter.mock.calls[0][0].headers.Authorization).toBe("Bearer token-value");
  });

  it("clears tokens and emits expiration on a 401 response", async () => {
    localStorage.setItem("study_access_token", "access");
    localStorage.setItem("study_refresh_token", "refresh");
    const listener = vi.fn();
    window.addEventListener("study-session-expired", listener);
    const adapter = async (config) => Promise.reject({ response: { status: 401 }, config });
    await expect(api.get("/test", { adapter })).rejects.toBeDefined();
    expect(localStorage.getItem("study_access_token")).toBeNull();
    expect(localStorage.getItem("study_refresh_token")).toBeNull();
    expect(listener).toHaveBeenCalledOnce();
    window.removeEventListener("study-session-expired", listener);
  });
});
