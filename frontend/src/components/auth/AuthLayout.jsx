import React from "react";

export default function AuthLayout({ children }) {
  return (
    <main className="auth-layout">
      <section className="auth-brand">
        <div className="auth-logo">▣</div>
        <span className="eyebrow">STUDY TRACKER</span>
        <h1>
          Crie uma rotina de
          <br />
          estudos consistente.
        </h1>
        <p>
          Acompanhe seu progresso e construa o hábito de estudar todos os dias.
        </p>
        <div className="auth-visual">
          <div className="visual-calendar">
            <b>Agosto</b>
            <div>
              <i />
              <i className="done" />
              <i />
              <i />
              <i className="done" />
              <i />
              <i className="done" />
              <i />
              <i />
            </div>
          </div>
          <div className="visual-progress">
            <span>Foco semanal</span>
            <b>76%</b>
          </div>
        </div>
      </section>
      <section className="auth-form-side">{children}</section>
    </main>
  );
}
