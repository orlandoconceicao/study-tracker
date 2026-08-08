import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { studiesApi } from "../services/studies";

const formatDuration = (minutes) => {
  const hours = Math.floor(minutes / 60);
  const remaining = minutes % 60;
  return `${hours ? `${hours}h ` : ""}${remaining ? `${remaining}min` : ""}`.trim() || "0min";
};

const formatDate = (date) =>
  new Date(`${date}T12:00`).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });

const friendlyError = (error) =>
  error.response?.data?.detail || "Não foi possível carregar seus estudos. Tente novamente.";

export default function Studies() {
  const [items, setItems] = useState([]);
  const [filters, setFilters] = useState({ start_date: "", end_date: "", subject: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [removingId, setRemovingId] = useState(null);

  const load = useCallback(async (activeFilters = filters) => {
    setLoading(true);
    setError("");
    try {
      const { data } = await studiesApi.list(activeFilters);
      setItems(data);
    } catch (requestError) {
      setError(friendlyError(requestError));
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    load({ start_date: "", end_date: "", subject: "" });
  }, []);

  const remove = async (id) => {
    if (!window.confirm("Excluir este estudo?")) return;
    setRemovingId(id);
    setError("");
    try {
      await studiesApi.remove(id);
      await load();
    } catch (requestError) {
      setError(friendlyError(requestError));
    } finally {
      setRemovingId(null);
    }
  };

  return (
    <section className="page-content">
      <header className="page-hero">
        <div>
          <span className="eyebrow">SEU HISTÓRICO</span>
          <h1>Estudos</h1>
          <p>Acompanhe suas sessões e mantenha sua consistência.</p>
        </div>
        <Link to="/studies/new" className="button add-study">+ Adicionar estudo</Link>
      </header>

      <form className="panel filters-panel" onSubmit={(event) => { event.preventDefault(); load(); }}>
        <div className="section-heading compact-heading">
          <div>
            <span className="eyebrow">FILTROS</span>
            <h2>Encontrar estudos</h2>
          </div>
        </div>
        <div className="filter-fields">
          <label>Data inicial<input type="date" value={filters.start_date} onChange={(event) => setFilters({ ...filters, start_date: event.target.value })} /></label>
          <label>Data final<input type="date" value={filters.end_date} onChange={(event) => setFilters({ ...filters, end_date: event.target.value })} /></label>
          <label>Assunto<input type="text" placeholder="Ex.: Matemática" value={filters.subject} onChange={(event) => setFilters({ ...filters, subject: event.target.value })} /></label>
          <button type="submit">Filtrar</button>
        </div>
      </form>

      <section className="card studies-card">
        <div className="section-heading">
          <div>
            <span className="eyebrow">ATIVIDADE</span>
            <h2>Seus estudos</h2>
            {!loading && !error && <p className="section-description">{items.length} {items.length === 1 ? "registro" : "registros"}</p>}
          </div>
        </div>

        {loading ? <p className="muted">Carregando seus estudos...</p> : error ? <p className="auth-error">{error}</p> : items.length ? (
          <div className="studies-list">
            {items.map((study) => (
              <article className="study-record" key={study.id}>
                <div className="study-mark">{study.subject.slice(0, 1).toUpperCase()}</div>
                <div className="study-record-content">
                  <div className="study-record-title"><h3>{study.subject}</h3><span>{formatDuration(study.duration_minutes)}</span></div>
                  <p>{formatDate(study.date)}</p>
                  {study.notes && <p className="study-notes">{study.notes}</p>}
                </div>
                <div className="study-actions">
                  <Link to={`/studies/${study.id}/edit`} className="text-button">Editar</Link>
                  <button type="button" className="text-button danger" disabled={removingId === study.id} onClick={() => remove(study.id)}>{removingId === study.id ? "Excluindo..." : "Excluir"}</button>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state"><h3>Nenhum estudo encontrado</h3><p>Comece registrando sua primeira sessão de estudo.</p><Link to="/studies/new" className="button">+ Adicionar estudo</Link></div>
        )}
      </section>
    </section>
  );
}
