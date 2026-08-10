import React from "react";
import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import api from "../services/api";
import { AuthProvider } from "./AuthContext";
import { useAuth } from "../hooks/useAuth";

vi.mock("../services/api", () => ({ default: { get: vi.fn(), post: vi.fn(), patch: vi.fn() } }));

const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;

describe("AuthProvider", () => {
  it("restores an authenticated session from storage", async () => {
    localStorage.setItem("study_access_token", "access");
    api.get.mockResolvedValueOnce({ data: { username: "ana" } });
    api.get.mockResolvedValueOnce({ data: { theme: "dark" } });
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user).toEqual({ username: "ana" });
    expect(document.documentElement.dataset.theme).toBe("dark");
  });

  it("clears an invalid stored session", async () => {
    localStorage.setItem("study_access_token", "invalid");
    api.get.mockRejectedValueOnce(new Error("unauthorized"));
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user).toBeNull();
    expect(localStorage.getItem("study_access_token")).toBeNull();
  });

  it("logs in, stores both tokens and loads the profile", async () => {
    api.post.mockResolvedValueOnce({ data: { access: "a", refresh: "r" } });
    api.get.mockResolvedValueOnce({ data: { username: "ana" } });
    api.get.mockResolvedValueOnce({ data: { theme: "light" } });
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));
    await act(() => result.current.login({ username: "ana", password: "secret" }));
    expect(localStorage.getItem("study_access_token")).toBe("a");
    expect(localStorage.getItem("study_refresh_token")).toBe("r");
    expect(result.current.user.username).toBe("ana");
  });

  it("updates the profile and reacts to expiration events", async () => {
    api.patch.mockResolvedValueOnce({ data: { username: "updated" } });
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));
    await act(() => result.current.updateProfile({ username: "updated" }));
    expect(result.current.user.username).toBe("updated");
    act(() => window.dispatchEvent(new Event("study-session-expired")));
    expect(result.current.user).toBeNull();
  });
});
