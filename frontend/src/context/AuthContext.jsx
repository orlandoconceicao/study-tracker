import React, { createContext, useEffect, useState } from "react";
import api from "../services/api";
export const AuthContext = createContext(null);
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
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
    const me = await api.get("/auth/me/");
    setUser(me.data);
  };
  const register = (data) => api.post("/auth/register/", data);
  const updateProfile = async (data) => {
    const response = await api.patch("/auth/me/", data);
    setUser(response.data);
    return response.data;
  };
  useEffect(() => {
    const load = async () => {
      try {
        if (localStorage.getItem("study_access_token"))
          setUser((await api.get("/auth/me/")).data);
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
    <AuthContext.Provider value={{ user, loading, login, logout, register, updateProfile }}>
      {children}
    </AuthContext.Provider>
  );
}
