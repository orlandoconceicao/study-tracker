import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { studiesApi } from "../../services/studies";
import Calendar from "../Calendar";
import StatCard from "./StatCard";
import RecentStudies from "./RecentStudies";

const greeting = () => {
  const hour = new Date().getHours();

  return hour < 12
    ? "Bom dia"
    : hour < 18
      ? "Boa tarde"
      : "Boa noite";
};

const hours = (value) =>
  `${Math.floor(value)}h ${Math.round((value % 1) * 60)}min`;

export default function DashboardHome() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [studies, setStudies] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([studiesApi.statistics(), studiesApi.list()])
      .then(([summary, list]) => {
        setStats(summary.data);
        setStudies(list.data.slice(0, 5));
      })
      .catch(() =>
        setError(
          "Não foi possível carregar seu resumo de estudos. Tente novamente.",
        ),
      );
  }, []);

  return (
    <>
      <div className="dashboard-hero">
        <div>
          <span className="eyebrow">SEU ESPAÇO DE ESTUDOS</span>

          <h1>
            {greeting()}, {user.username}
          </h1>

          <p>Continue mantendo sua sequência de estudos.</p>
        </div>

        <Link to="/studies/new" className="button add-study">
          + Adicionar estudo
        </Link>
      </div>

      {error && <p className="auth-error">{error}</p>}

      {stats ? (
        <div className="stat-grid">
          <StatCard
            label="Dias estudados"
            value={`${stats.total_studied_days} dias`}
            accent="lavender"
          />

          <StatCard
            label="Sequência atual"
            value={`${stats.current_streak} dias`}
            detail={
              stats.current_streak
                ? `Você está em uma sequência de ${stats.current_streak} dias.`
                : "Comece uma sequência hoje."
            }
            accent="rose"
          />

          <StatCard
            label="Melhor sequência"
            value={`${stats.best_streak} dias`}
            accent="sand"
          />
        </div>
      ) : (
        <p className="muted">Carregando seu resumo...</p>
      )}

      <div className="dashboard-columns">
        <div className="card">
          <Calendar />
        </div>

        <div className="streak-panel">
          <span className="eyebrow">CONSISTÊNCIA</span>

          <h2>Continue aparecendo</h2>

          <p>
            Seu hábito de estudo cresce a cada sessão focada.
          </p>

          <div className="streak-figure">
            <b>🔥 {stats?.current_streak || 0}</b>
            <span>dias de sequência</span>
          </div>

          <Link to="/statistics">
            Veja seu progresso →
          </Link>
        </div>
      </div>

      <div className="recent">
        <RecentStudies
          studies={studies}
          loading={!stats && !error}
        />
      </div>
    </>
  );
}