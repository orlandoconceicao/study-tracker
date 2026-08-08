import React from "react";

export default function StatCard({ label, value, detail, accent = "blue" }) {
  return (
    <article className={`stat-card ${accent}`}>
      <span className="stat-label">{label}</span>
      <strong>{value}</strong>
      {detail && <small>{detail}</small>}
    </article>
  );
}
