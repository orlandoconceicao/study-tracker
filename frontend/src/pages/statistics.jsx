import React, { useEffect, useState } from "react";
import { studiesApi } from "../services/studies";
import StatCard from "../components/dashboard/StatCard";

const hours = (value) => `${Math.floor(value)}h ${Math.round((value % 1) * 60)}min`;

export default function Statistics() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    studiesApi.statistics().then((response) => setData(response.data)).catch((requestError) => setError(requestError.response?.data?.detail || "Não foi possível carregar suas estatísticas."));
  }, []);

  return (
    <section className="page-content">
      <header className="page-hero">
        <div><span className="eyebrow">SEU DESEMPENHO</span><h1>Estatísticas</h1><p>Veja sua evolução e acompanhe seu desempenho nos estudos.</p></div>
      </header>
      {error ? <p className="auth-error">{error}</p> : !data ? <p className="muted">Carregando suas estatísticas...</p> : <>
        <div className="stat-grid statistics-grid">
          <StatCard label="Dias estudados" value={`${data.total_studied_days} dias`} accent="lavender" />
          <StatCard label="Tempo total estudado" value={hours(data.total_hours)} accent="blue" />
          <StatCard label="Sequência atual" value={`${data.current_streak} dias`} accent="rose" />
          <StatCard label="Melhor sequência" value={`${data.best_streak} dias`} accent="sand" />
        </div>
        <section className="card progress-summary">
          <span className="eyebrow">RITMO DE ESTUDO</span><h2>Seu progresso</h2>
          <div className="progress-metrics">
            <div><strong>{data.average_minutes_per_day} min</strong><span>Média por dia estudado</span></div>
            <div><strong>{data.week_minutes} min</strong><span>Estudados nesta semana</span></div>
            <div><strong>{data.month_minutes} min</strong><span>Estudados neste mês</span></div>
          </div>
        </section>
      </>}
    </section>
  );
}
