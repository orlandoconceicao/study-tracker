import React from "react";
import { Link } from "react-router-dom";

const duration = (minutes) =>
  `${Math.floor(minutes / 60) ? `${Math.floor(minutes / 60)}h ` : ""}${
    minutes % 60 ? `${minutes % 60}min` : ""
  }`.trim();

export default function RecentStudies({ studies, loading }) {
  return (
    <div className="card recent-card">
      <div className="section-heading">
        <div>
          <span className="eyebrow">ATIVIDADE</span>
          <h2>Estudos recentes</h2>
        </div>

        <Link to="/studies">Ver todos</Link>
      </div>

      {loading ? (
        <p className="muted">Carregando seus estudos...</p>
      ) : studies.length ? (
        <div className="recent-list">
          {studies.map((study) => (
            <div className="recent-item" key={study.id}>
              <div className="study-mark">
                {study.subject.slice(0, 1).toUpperCase()}
              </div>

              <div>
                <strong>{study.subject}</strong>

                <p>
                  {new Date(`${study.date}T12:00`).toLocaleDateString(
                    "pt-BR",
                    {
                      month: "short",
                      day: "numeric",
                    },
                  )}

                  {study.notes ? ` · ${study.notes}` : ""}
                </p>
              </div>

              <strong>{duration(study.duration_minutes)}</strong>
            </div>
          ))}
        </div>
      ) : (
        <div>
          <p className="muted">Comece sua jornada de estudos hoje.</p>

          <Link to="/studies/new" className="button">
            + Adicionar estudo
          </Link>
        </div>
      )}
    </div>
  );
}