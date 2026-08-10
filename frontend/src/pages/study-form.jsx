import React, { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { studiesApi } from "../services/studies";
import { collection, educationApi } from "../services/education";

export default function StudyForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    date: new Date().toISOString().slice(0, 10),
    duration_minutes: "",
    subject: "",
    notes: "",
    child: localStorage.getItem("study_active_child") || "",
  });
  const [children, setChildren] = useState([]);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    educationApi.getChildren().then((response) => setChildren(collection(response).filter((child) => child.active))).catch(() => setChildren([]));
    if (!id) return;

    studiesApi.get(id)
      .then((response) => setForm({ ...response.data, child: response.data.child || "" }))
      .catch(() => setError("Estudo não encontrado."));
  }, [id]);

  const submit = async (event) => {
    event.preventDefault();
    const data = { ...form, child: form.child ? Number(form.child) : null, duration_minutes: Number(form.duration_minutes) };

    try {
      setSaving(true);
      setError("");
      if (id) {
        await studiesApi.update(id, data);
      } else {
        await studiesApi.create(data);
      }
      navigate("/dashboard");
    } catch {
      setError("Verifique os campos e tente novamente.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="page-content study-form-page">
      <header className="page-hero">
        <div>
          <span className="eyebrow">{id ? "ATUALIZAR SESSÃO" : "NOVA SESSÃO"}</span>
          <h1>{id ? "Editar estudo" : "Registrar estudo"}</h1>
          <p>Preencha os dados da sua sessão de estudo.</p>
        </div>
      </header>

      <form className="panel study-form" onSubmit={submit}>
        <div className="study-form-fields">
          <label className="study-subject-field" htmlFor="study-child">Filho<select id="study-child" value={form.child} onChange={(event) => { setForm({ ...form, child: event.target.value }); if (event.target.value) localStorage.setItem("study_active_child", event.target.value); }}><option value="">Estudo do responsável</option>{children.map((child) => <option key={child.id} value={child.id}>{child.name} · {child.grade_name}</option>)}</select></label>
          <label htmlFor="study-date">Data<input id="study-date" type="date" required value={form.date} onChange={(event) => setForm({ ...form, date: event.target.value })} /></label>
          <label htmlFor="study-duration">Duração (minutos)<input id="study-duration" type="number" min="1" placeholder="Ex.: 60" required value={form.duration_minutes} onChange={(event) => setForm({ ...form, duration_minutes: event.target.value })} /></label>
          <label className="study-subject-field" htmlFor="study-subject">Assunto<input id="study-subject" type="text" placeholder="Ex.: Matemática" required value={form.subject} onChange={(event) => setForm({ ...form, subject: event.target.value })} /></label>
          <label className="study-notes-field" htmlFor="study-notes">Observação<textarea id="study-notes" rows="5" placeholder="O que você estudou nesta sessão?" value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} /></label>
        </div>

        {error && <p className="auth-error">{error}</p>}
        <div className="study-form-actions">
          <Link to="/studies" className="button secondary-button">Cancelar</Link>
          <button type="submit" disabled={saving}>{saving ? "Salvando..." : "Salvar estudo"}</button>
        </div>
      </form>
    </section>
  );
}
