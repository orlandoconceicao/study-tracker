import React from "react";
import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <main className="center">
      <section className="card empty-state">
        <span className="eyebrow">ERRO 404</span>
        <h1>Página não encontrada</h1>
        <p>O endereço acessado não existe.</p>
        <Link to="/dashboard" className="button">
          Voltar ao dashboard
        </Link>
      </section>
    </main>
  );
}
