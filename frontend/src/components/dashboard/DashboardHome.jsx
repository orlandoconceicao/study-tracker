import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import { studiesApi } from "../../services/studies";
import Calendar from "../Calendar";
import StatCard from "./StatCard";
import RecentStudies from "./RecentStudies";
import { collection, educationApi } from "../../services/education";

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
  const [recommendation, setRecommendation] = useState(null);
  const [family, setFamily] = useState({ children: [], selected: null, progress: null });

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

  useEffect(() => {
    educationApi.getChildren().then(async (response) => {
      const children = collection(response).filter((child) => child.active && child.grade);
      const selected = children.find((child) => String(child.id) === localStorage.getItem("study_active_child")) || children[0] || null;
      if (!selected) { setFamily({ children, selected: null, progress: null }); return; }
      localStorage.setItem("study_active_child", selected.id);
      const [progressResponse, recommendationResponse] = await Promise.all([educationApi.getChildProgress(selected.id), educationApi.getRecommendations({ child: selected.id })]);
      setFamily({ children, selected, progress: progressResponse.data });
      setRecommendation(collection(recommendationResponse)[0] || null);
    }).catch(() => {});
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

      <section className="dashboard-family card"><div className="section-heading"><div><span className="eyebrow">SEUS FILHOS</span><h2>{family.selected ? `Estudando com ${family.selected.name}` : "Comece pelo perfil do seu filho"}</h2></div><Link className="text-button" to="/settings">Gerenciar</Link></div>{family.selected ? <div className="dashboard-child"><div><strong>{family.selected.name}</strong><span>{family.selected.grade_name}</span>{family.progress && <small>{family.progress.topics_started} conteúdos estudados · {family.progress.exercises_attempted} exercícios feitos</small>}</div>{family.progress?.recent_attempts?.[0] ? <div><span className="eyebrow">ÚLTIMO CONTEÚDO</span><strong>{family.progress.recent_attempts[0].topic_title}</strong><Link className="button" to={`/learn/topic/${family.progress.recent_attempts[0].topic}`}>Continuar</Link></div> : <Link className="button" to="/learn">Começar a estudar</Link>}</div> : <div className="empty-inline"><p>Cadastre um filho e informe a série para visualizar matérias e conteúdos.</p><Link className="button" to="/settings">Cadastrar filho</Link></div>}</section>

      {recommendation && <section className="dashboard-recommendation card"><div><span className="eyebrow">RECOMENDADO PARA VOCÊ</span><h2>{recommendation.topic_title}</h2><p>{recommendation.reason}</p><small>{recommendation.subject_name}{recommendation.accuracy !== null ? ` · ${recommendation.accuracy}% de acerto` : ""}</small></div><Link className="button" to={`/learn/topic/${recommendation.topic}`}>Estudar agora</Link></section>}

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
