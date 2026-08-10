import React, { createContext, useEffect, useState } from "react";
import api from "../services/api";
import { applyTheme, SYSTEM_THEME_QUERY, THEME_STORAGE_KEY } from "../services/theme";
export const AuthContext = createContext(null);
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [preferences, setPreferences] = useState({ theme: localStorage.getItem(THEME_STORAGE_KEY) || "system", language: "pt-BR", daily_study_goal_minutes: 60 });
  const [loading, setLoading] = useState(true);
  const logout = () => {
    localStorage.removeItem("study_access_token");
    localStorage.removeItem("study_refresh_token");
    setUser(null);
  };
  const login = async (credentials) => {
    const { data } = await api.post("/auth/login/", credentials);
    localStorage.setItem("study_access_token", data.access);
    localStorage.setItem("study_refresh_token", data.refresh);
    const [me, savedPreferences] = await Promise.all([api.get("/auth/me/"), api.get("/users/preferences/")]);
    setUser(me.data);
    setPreferences(savedPreferences.data);
  };
  const register = (data) => api.post("/auth/register/", data);
  const updateProfile = async (data) => {
    const response = await api.patch("/auth/me/", data);
    setUser(response.data);
    return response.data;
  };
  const updatePreferences = async (data) => {
    const response = await api.patch("/users/preferences/", data);
    setPreferences(response.data);
    return response.data;
  };
  useEffect(() => {
    applyTheme(preferences.theme);
    const media = window.matchMedia?.(SYSTEM_THEME_QUERY);
    const handleSystemTheme = () => preferences.theme === "system" && applyTheme("system");
    media?.addEventListener?.("change", handleSystemTheme);
    return () => media?.removeEventListener?.("change", handleSystemTheme);
  }, [preferences.theme]);
  useEffect(() => {
    const load = async () => {
      try {
        if (localStorage.getItem("study_access_token")) {
          const [me, savedPreferences] = await Promise.all([api.get("/auth/me/"), api.get("/users/preferences/")]);
          setUser(me.data);
          setPreferences(savedPreferences.data);
        }
      } catch {
        logout();
      } finally {
        setLoading(false);
      }
    };
    load();
    window.addEventListener("study-session-expired", logout);
    return () => window.removeEventListener("study-session-expired", logout);
  }, []);
  return (
    <AuthContext.Provider value={{ user, preferences, loading, login, logout, register, updateProfile, updatePreferences }}>
      {children}
    </AuthContext.Provider>
  );
}
