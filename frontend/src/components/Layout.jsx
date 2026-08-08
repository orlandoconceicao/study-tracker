import React, { useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import Sidebar from "./layout/Sidebar";

export default function Layout() {
  const { user, logout, loading } = useAuth();
  const [open, setOpen] = useState(false);

  if (loading) {
    return <p className="center">Carregando seu espaço de estudos...</p>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const handleLogout = () => {
    setOpen(false);
    logout();
  };

  return (
    <div className="app-shell">
      <button
        className="mobile-menu"
        onClick={() => setOpen(!open)}
        aria-label={open ? "Fechar menu" : "Abrir menu"}
        aria-expanded={open}
      >
        ☰
      </button>

      <div className={open ? "mobile-drawer open" : "mobile-drawer"}>
        <Sidebar onLogout={handleLogout} />
      </div>

      <Sidebar onLogout={handleLogout} />

      <main className="workspace">
        <Outlet context={{ user }} />
      </main>
    </div>
  );
}
