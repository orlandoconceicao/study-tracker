import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { studiesApi } from "../services/studies";

export default function StudyForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    date: new Date().toISOString().slice(0, 10),
    duration_minutes: "",
    subject: "",
    notes: "",
  });
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;

    studiesApi.get(id)
      .then((response) => setForm(response.data))
      .catch(() => setError("Estudo não encontrado."));
  }, [id]);

  const submit = async (event) => {
    event.preventDefault();
    const data = { ...form, duration_minutes: Number(form.duration_minutes) };

    try {
      if (id) {
        await studiesApi.update(id, data);
      } else {
        await studiesApi.create(data);
      }
      navigate("/dashboard");
    } catch {
      setError("Verifique os campos e tente novamente.");
    }
  };

  return (
    <>
      <h1>{id ? "Editar estudo" : "Registrar estudo"}</h1>
      <form onSubmit={submit}>
        <label>Data</label>
        <input type="date" required value={form.date} onChange={(event) => setForm({ ...form, date: event.target.value })} />

        <label>Duração (minutos)</label>
        <input type="number" min="1" required value={form.duration_minutes} onChange={(event) => setForm({ ...form, duration_minutes: event.target.value })} />

        <label>Assunto</label>
        <input type="text" required value={form.subject} onChange={(event) => setForm({ ...form, subject: event.target.value })} />

        <label>Observação</label>
        <textarea value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })} />

        {error && <p className="error">{error}</p>}
        <button type="submit">Salvar estudo</button>
      </form>
    </>
  );
}
