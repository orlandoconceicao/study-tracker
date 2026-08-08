import React from "react";
import { NavLink } from "react-router-dom";

const links = [
  ["/dashboard", "Dashboard", "▦"],
  ["/studies", "Estudos", "▤"],
  ["/statistics", "Estatísticas", "◔"],
  ["/settings", "Configurações", "⚙"],
];

export default function Sidebar({ onLogout }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span>▣</span> Study Tracker
      </div>

      <nav>
        {links.map(([to, label, icon]) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => (isActive ? "active" : "")}
          >
            <i>{icon}</i>
            {label}
          </NavLink>
        ))}
      </nav>

      <button className="logout" onClick={onLogout}>
        ↪ <span>Sair</span>
      </button>
    </aside>
  );
}