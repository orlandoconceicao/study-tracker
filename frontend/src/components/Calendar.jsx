import React, { useEffect, useState } from "react";
import { studiesApi } from "../services/studies";

const monthName = (date) =>
  date.toLocaleDateString("pt-BR", {
    month: "long",
    year: "numeric",
  });

export default function Calendar() {
  const [current, setCurrent] = useState(new Date());
  const [data, setData] = useState({});
  const [selected, setSelected] = useState(null);
  const [details, setDetails] = useState([]);
  const [error, setError] = useState("");

  const month = current.getMonth() + 1;
  const year = current.getFullYear();

  useEffect(() => {
    setError("");

    studiesApi
      .calendar({ month, year })
      .then((response) => {
        setData(response.data);
      })
      .catch(() => {
        setError("Não foi possível carregar o calendário.");
      });
  }, [month, year]);

  const openDay = async (key) => {
    if (!data[key]?.studied) return;

    setSelected(key);

    try {
      const response = await studiesApi.list({
        start_date: key,
        end_date: key,
      });

      setDetails(response.data);
    } catch {
      setDetails([]);
    }
  };

  const goToPreviousMonth = () => {
    setCurrent(new Date(year, month - 2, 1));
    setSelected(null);
    setDetails([]);
  };

  const goToNextMonth = () => {
    setCurrent(new Date(year, month, 1));
    setSelected(null);
    setDetails([]);
  };

  const offset = new Date(year, month - 1, 1).getDay();
  const days = new Date(year, month, 0).getDate();

  return (
    <div className="calendar">
      <div className="calendar-head">
        <button
          type="button"
          onClick={goToPreviousMonth}
          aria-label="Mês anterior"
        >
          ←
        </button>

        <h2>{monthName(current)}</h2>

        <button
          type="button"
          onClick={goToNextMonth}
          aria-label="Próximo mês"
        >
          →
        </button>
      </div>

      {error && <p className="auth-error">{error}</p>}

      <div className="calendar-weekdays">
        {["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"].map((day) => (
          <div className="calendar-weekday" key={day}>
            {day}
          </div>
        ))}
      </div>

      <div className="calendar-grid">
        {Array.from({ length: offset }).map((_, index) => (
          <div
            key={`empty-${index}`}
            aria-hidden="true"
          />
        ))}

        {Array.from({ length: days }, (_, index) => {
          const day = index + 1;

          const key = `${year}-${String(month).padStart(
            2,
            "0",
          )}-${String(day).padStart(2, "0")}`;

          const item = data[key];
          const studied = item?.studied;

          return (
            <button
              type="button"
              key={key}
              className={studied ? "studied" : ""}
              onClick={() => openDay(key)}
              title={
                studied
                  ? `${item.total_minutes} minutos estudados`
                  : "Nenhum estudo registrado"
              }
            >
              {day}
            </button>
          );
        })}
      </div>

      {selected && (
        <div className="calendar-details">
          <h3>
            {new Date(`${selected}T12:00`).toLocaleDateString("pt-BR")}
          </h3>

          {details.length > 0 ? (
            details.map((study) => (
              <p key={study.id}>
                <strong>{study.subject}</strong>
                {" · "}
                {study.duration_minutes} min
                {study.notes && ` — ${study.notes}`}
              </p>
            ))
          ) : (
            <p className="muted">
              Nenhum detalhe encontrado para este dia.
            </p>
          )}
        </div>
      )}
    </div>
  );
}