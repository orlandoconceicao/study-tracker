import React, { useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import api from "../services/api";

const initialReminder = {
  enabled: false,
  reminder_time: "",
  timezone: "America/Cuiaba",
};

const timezoneGroups = [
  {
    label: "UTC−2",
    description: "Fernando de Noronha",
    timezone: "America/Noronha",
    options: [["America/Noronha", "Fernando de Noronha (PE)"]],
  },
  {
    label: "UTC−3 — Horário de Brasília",
    description: "Brasília, Sul, Sudeste, Nordeste, Pará e Tocantins",
    timezone: "America/Sao_Paulo",
    options: [
      ["America/Sao_Paulo", "Brasília, Sul e Sudeste"],
      ["America/Araguaina", "Araguaína (TO)"],
      ["America/Bahia", "Salvador (BA)"],
      ["America/Belem", "Belém (PA)"],
      ["America/Fortaleza", "Fortaleza (CE)"],
      ["America/Maceio", "Maceió (AL)"],
      ["America/Recife", "Recife (PE)"],
      ["America/Santarem", "Santarém (PA)"],
    ],
  },
  {
    label: "UTC−4 — Horário da Amazônia",
    description: "Mato Grosso, Mato Grosso do Sul, Amazonas, Rondônia e Roraima",
    timezone: "America/Cuiaba",
    options: [
      ["America/Boa_Vista", "Boa Vista (RR)"],
      ["America/Campo_Grande", "Campo Grande (MS)"],
      ["America/Cuiaba", "Cuiabá (MT)"],
      ["America/Manaus", "Manaus (AM)"],
      ["America/Porto_Velho", "Porto Velho (RO)"],
    ],
  },
  {
    label: "UTC−5 — Horário do Acre",
    description: "Acre e oeste do Amazonas",
    timezone: "America/Rio_Branco",
    options: [
      ["America/Eirunepe", "Eirunepé (AM)"],
      ["America/Rio_Branco", "Rio Branco (AC)"],
    ],
  },
];

const errorMessage = (error, fallback) => {
  const data = error.response?.data;
  if (typeof data?.detail === "string") return data.detail;
  const firstError = Object.values(data || {}).flat()[0];
  return typeof firstError === "string" ? firstError : fallback;
};

export default function Settings() {
  const { user, updateProfile } = useAuth();
  const [profile, setProfile] = useState({ username: "", email: "" });
  const [reminder, setReminder] = useState(initialReminder);
  const [loading, setLoading] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingReminder, setSavingReminder] = useState(false);
  const [profileStatus, setProfileStatus] = useState({ text: "", type: "" });
  const [reminderStatus, setReminderStatus] = useState({ text: "", type: "" });
  const selectedTimezoneGroup =
    timezoneGroups.find((group) =>
      group.options.some(([value]) => value === reminder.timezone),
    ) || timezoneGroups[2];

  useEffect(() => {
    if (user)
      setProfile({ username: user.username || "", email: user.email || "" });
  }, [user]);

  useEffect(() => {
    api
      .get("/notifications/settings/")
      .then(({ data }) =>
        setReminder({
          ...initialReminder,
          ...data,
          reminder_time: data.reminder_time || "",
        }),
      )
      .catch(() =>
        setReminderStatus({
          text: "Não foi possível carregar suas preferências de lembrete.",
          type: "error",
        }),
      )
      .finally(() => setLoading(false));
  }, []);

  const saveProfile = async (event) => {
    event.preventDefault();
    setSavingProfile(true);
    setProfileStatus({ text: "", type: "" });
    try {
      await updateProfile(profile);
      setProfileStatus({
        text: "Perfil atualizado com sucesso.",
        type: "success",
      });
    } catch (error) {
      setProfileStatus({
        text: errorMessage(error, "Não foi possível atualizar o perfil."),
        type: "error",
      });
    } finally {
      setSavingProfile(false);
    }
  };

  const saveReminder = async (event) => {
    event.preventDefault();
    setSavingReminder(true);
    setReminderStatus({ text: "", type: "" });
    try {
      await api.patch("/notifications/settings/", reminder);
      setReminderStatus({
        text: "Preferências de lembrete atualizadas.",
        type: "success",
      });
    } catch (error) {
      setReminderStatus({
        text: errorMessage(
          error,
          "Não foi possível salvar as preferências de lembrete.",
        ),
        type: "error",
      });
    } finally {
      setSavingReminder(false);
    }
  };

  return (
    <section className="page-content settings-page">
      <header className="page-hero">
        <div>
          <span className="eyebrow">PREFERÊNCIAS</span>
          <h1>Configurações</h1>
          <p>Gerencie seu perfil e seus lembretes de estudo.</p>
        </div>
      </header>
      <div className="settings-grid">
        <form className="card settings-section" onSubmit={saveProfile}>
          <span className="eyebrow">PERFIL</span>
          <h2>Perfil</h2>
          <p className="section-description">
            Atualize suas informações pessoais.
          </p>
          <div className="settings-fields profile-fields">
            <label>
              Nome de usuário
              <input
                required
                value={profile.username}
                onChange={(event) =>
                  setProfile({ ...profile, username: event.target.value })
                }
              />
            </label>
            <label>
              E-mail
              <input
                type="email"
                required
                value={profile.email}
                onChange={(event) =>
                  setProfile({ ...profile, email: event.target.value })
                }
              />
            </label>
          </div>
          {profileStatus.text && (
            <p
              className={
                profileStatus.type === "error"
                  ? "auth-error"
                  : "success-message"
              }
            >
              {profileStatus.text}
            </p>
          )}
          <div className="settings-actions">
            <button type="submit" disabled={savingProfile}>
              {savingProfile ? "Salvando..." : "Salvar perfil"}
            </button>
          </div>
        </form>
        <form className="card settings-section" onSubmit={saveReminder}>
          <span className="eyebrow">NOTIFICAÇÕES</span>
          <h2>Lembrete diário</h2>
          <p className="section-description">
            Escolha quando deseja receber seu lembrete de estudo por e-mail.
          </p>
          {loading ? (
            <p className="muted">Carregando preferências...</p>
          ) : (
            <>
              <p className="reminder-recipient">
                Os lembretes serão enviados para:{" "}
                <strong>{user?.email || "e-mail não informado"}</strong>
              </p>
              <label className="toggle-row">
                <span>
                  <strong>Ativar lembrete</strong>
                  <small>Receba um lembrete diário no horário escolhido.</small>
                </span>
                <input
                  type="checkbox"
                  checked={reminder.enabled}
                  onChange={(event) =>
                    setReminder({ ...reminder, enabled: event.target.checked })
                  }
                />
              </label>
              <div className="settings-fields">
                <label>
                  Horário
                  <input
                    type="time"
                    value={reminder.reminder_time}
                    onChange={(event) =>
                      setReminder({
                        ...reminder,
                        reminder_time: event.target.value,
                      })
                    }
                  />
                </label>
                <div className="timezone-field">
                  <span className="field-label">Fuso horário</span>
                  <div
                    className="timezone-options"
                    role="radiogroup"
                    aria-label="Fusos horários do Brasil"
                  >
                    {timezoneGroups.map((group) => (
                      <label
                        key={group.label}
                        className={
                          selectedTimezoneGroup.label === group.label
                            ? "timezone-option active"
                            : "timezone-option"
                        }
                      >
                        <input
                          type="radio"
                          name="timezone"
                          value={group.timezone}
                          checked={selectedTimezoneGroup.label === group.label}
                          onChange={() =>
                            setReminder({
                              ...reminder,
                              timezone: group.timezone,
                            })
                          }
                        />
                        <span className="timezone-option-copy">
                          <strong>{group.label.split(" — ")[0]}</strong>
                          <small>{group.description}</small>
                        </span>
                        <span className="timezone-check" aria-hidden="true">✓</span>
                      </label>
                    ))}
                  </div>
                  <small className="timezone-hint">
                    Zona utilizada: <code>{selectedTimezoneGroup.timezone}</code>
                  </small>
                </div>
              </div>
              {reminderStatus.text && (
                <p
                  className={
                    reminderStatus.type === "error"
                      ? "auth-error"
                      : "success-message"
                  }
                >
                  {reminderStatus.text}
                </p>
              )}
              <div className="settings-actions">
                <button type="submit" disabled={savingReminder}>
                  {savingReminder ? "Salvando..." : "Salvar lembrete"}
                </button>
              </div>
            </>
          )}
        </form>
        <aside className="settings-info">
          <span aria-hidden="true">✦</span>
          <p>Você receberá o lembrete no e-mail cadastrado no seu perfil.</p>
        </aside>
      </div>
    </section>
  );
}
