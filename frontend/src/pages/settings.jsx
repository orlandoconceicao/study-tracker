import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import api from "../services/api";

const initialReminder = { enabled: false, reminder_time: "", timezone: "America/Cuiaba" };
const initialPreferences = { theme: "system", language: "pt-BR", daily_study_goal_minutes: 60 };
const timezones = [
  ["America/Noronha", "Fernando de Noronha (UTC−2)"], ["America/Sao_Paulo", "Brasília (UTC−3)"],
  ["America/Cuiaba", "Cuiabá (UTC−4)"], ["America/Manaus", "Manaus (UTC−4)"],
  ["America/Rio_Branco", "Rio Branco (UTC−5)"],
];
const emptyStatus = { text: "", type: "" };
const message = (error, fallback) => {
  const data = error.response?.data;
  if (typeof data?.detail === "string") return data.detail;
  const value = Object.values(data || {})[0];
  return (Array.isArray(value) ? value[0] : value) || fallback;
};
const dateTime = (value) => value ? new Intl.DateTimeFormat("pt-BR", { dateStyle: "long", timeStyle: "short" }).format(new Date(value)) : "Não disponível";

function Status({ value }) {
  return value.text ? <p className={value.type === "error" ? "auth-error" : "success-message"} role="status">{value.text}</p> : null;
}

export default function Settings() {
  const { user, preferences: authPreferences, updateProfile, updatePreferences, logout } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState({ first_name: "", last_name: "", username: "", email: "" });
  const [savedProfile, setSavedProfile] = useState(profile);
  const [reminder, setReminder] = useState(initialReminder);
  const [savedReminder, setSavedReminder] = useState(initialReminder);
  const [preferences, setPreferences] = useState(initialPreferences);
  const [savedPreferences, setSavedPreferences] = useState(initialPreferences);
  const [passwords, setPasswords] = useState({ current_password: "", new_password: "", confirm_password: "" });
  const [deleteData, setDeleteData] = useState({ current_password: "", confirmation: "" });
  const [showDelete, setShowDelete] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState("");
  const [statuses, setStatuses] = useState({});
  const setStatus = (key, text, type = "success") => setStatuses((old) => ({ ...old, [key]: { text, type } }));

  useEffect(() => {
    if (user) {
      const value = { first_name: user.first_name || "", last_name: user.last_name || "", username: user.username || "", email: user.email || "" };
      setProfile(value); setSavedProfile(value);
    }
  }, [user]);
  useEffect(() => {
    api.get("/notifications/settings/")
      .then((notificationResponse) => {
        const notification = { ...initialReminder, ...notificationResponse.data, reminder_time: notificationResponse.data.reminder_time || "" };
        setReminder(notification); setSavedReminder(notification);
      })
      .catch((error) => setStatus("load", message(error, "Não foi possível carregar suas preferências."), "error"))
      .finally(() => setLoading(false));
  }, []);
  useEffect(() => {
    const value = { ...initialPreferences, ...authPreferences };
    setPreferences(value); setSavedPreferences(value);
  }, [authPreferences]);

  const changed = (a, b) => JSON.stringify(a) !== JSON.stringify(b);
  const profileValid = profile.username.trim() && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profile.email);
  const passwordValid = passwords.current_password && passwords.new_password.length >= 8 && passwords.new_password === passwords.confirm_password;
  const reminderValid = !reminder.enabled || reminder.reminder_time;
  const accountLabel = useMemo(() => user?.username ? `Usuário autenticado: ${user.username}` : "Usuário autenticado", [user]);

  const submit = async (key, action, success) => {
    setSaving(key); setStatus(key, "", "");
    try { await action(); setStatus(key, success); } catch (error) { setStatus(key, message(error, "Não foi possível salvar as alterações."), "error"); }
    finally { setSaving(""); }
  };
  const saveProfile = (event) => { event.preventDefault(); submit("profile", async () => { const result = await updateProfile(profile); setSavedProfile({ ...profile }); return result; }, "Perfil atualizado com sucesso."); };
  const savePassword = (event) => { event.preventDefault(); submit("password", async () => { await api.post("/auth/change-password/", passwords); setPasswords({ current_password: "", new_password: "", confirm_password: "" }); }, "Senha alterada com sucesso."); };
  const saveReminder = (event) => { event.preventDefault(); submit("reminder", async () => { await api.patch("/notifications/settings/", { ...reminder, reminder_time: reminder.reminder_time || null }); setSavedReminder({ ...reminder }); }, "Lembrete atualizado com sucesso."); };
  const savePreferences = (event) => { event.preventDefault(); submit("preferences", async () => { const saved = await updatePreferences(preferences); setSavedPreferences({ ...saved }); }, "Preferências atualizadas com sucesso."); };
  const signOut = () => { logout(); navigate("/login", { replace: true }); };
  const deleteAccount = (event) => { event.preventDefault(); submit("delete", async () => { await api.delete("/auth/account/", { data: deleteData }); logout(); navigate("/login", { replace: true }); }, "Conta desativada com sucesso."); };

  return <section className="page-content settings-page">
    <header className="page-hero"><div><span className="eyebrow">PREFERÊNCIAS</span><h1>Configurações</h1><p>Gerencie sua conta, perfil, segurança e preferências.</p></div></header>
    <Status value={statuses.load || emptyStatus} />
    <div className="settings-grid">
      <form className="card settings-section" onSubmit={saveProfile}><span className="eyebrow">PERFIL</span><h2>Perfil</h2><p className="section-description">Atualize suas informações pessoais.</p>
        <div className="settings-fields profile-fields"><label>Nome<input maxLength="150" value={profile.first_name} onChange={(e) => setProfile({ ...profile, first_name: e.target.value })} /></label><label>Sobrenome<input maxLength="150" value={profile.last_name} onChange={(e) => setProfile({ ...profile, last_name: e.target.value })} /></label><label>Nome de usuário<input required maxLength="150" value={profile.username} onChange={(e) => setProfile({ ...profile, username: e.target.value })} /></label><label>E-mail<input type="email" required maxLength="254" value={profile.email} onChange={(e) => setProfile({ ...profile, email: e.target.value })} /></label></div>
        <Status value={statuses.profile || emptyStatus} /><div className="settings-actions"><button disabled={saving === "profile" || !profileValid || !changed(profile, savedProfile)}>{saving === "profile" ? "Salvando..." : "Salvar perfil"}</button></div>
      </form>
      <form className="card settings-section" onSubmit={saveReminder}><span className="eyebrow">LEMBRETES</span><h2>Lembrete diário</h2><p className="section-description">Escolha quando receber seu lembrete de estudo.</p>
        {loading ? <p className="muted">Carregando preferências...</p> : <><p className="reminder-recipient">Os lembretes serão enviados para: <strong>{profile.email || "e-mail não informado"}</strong></p><label className="toggle-row"><span><strong>Ativar lembrete</strong><small>Receba um e-mail diariamente.</small></span><input type="checkbox" checked={reminder.enabled} onChange={(e) => setReminder({ ...reminder, enabled: e.target.checked })} /></label><div className="settings-fields"><label>Horário<input aria-label="Horário" type="time" required={reminder.enabled} value={reminder.reminder_time} onChange={(e) => setReminder({ ...reminder, reminder_time: e.target.value })} /></label><label>Fuso horário<select value={reminder.timezone} onChange={(e) => setReminder({ ...reminder, timezone: e.target.value })}>{timezones.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label></div><Status value={statuses.reminder || emptyStatus} /><div className="settings-actions"><button disabled={saving === "reminder" || !reminderValid || !changed(reminder, savedReminder)}>{saving === "reminder" ? "Salvando..." : "Salvar lembrete"}</button></div></>}
      </form>
      <form className="card settings-section" onSubmit={savePassword}><span className="eyebrow">SEGURANÇA</span><h2>Alterar senha</h2><p className="section-description">Use pelo menos 8 caracteres na nova senha.</p><div className="settings-fields profile-fields"><label>Senha atual<input type="password" autoComplete="current-password" required value={passwords.current_password} onChange={(e) => setPasswords({ ...passwords, current_password: e.target.value })} /></label><label>Nova senha<input type="password" autoComplete="new-password" minLength="8" required value={passwords.new_password} onChange={(e) => setPasswords({ ...passwords, new_password: e.target.value })} /></label><label>Confirmar nova senha<input type="password" autoComplete="new-password" required value={passwords.confirm_password} onChange={(e) => setPasswords({ ...passwords, confirm_password: e.target.value })} /></label></div><Status value={statuses.password || emptyStatus} /><div className="settings-actions"><button disabled={saving === "password" || !passwordValid}>{saving === "password" ? "Alterando..." : "Alterar senha"}</button></div></form>
      <form className="card settings-section" onSubmit={savePreferences}><span className="eyebrow">INTERFACE</span><h2>Preferências</h2><p className="section-description">Personalize sua experiência e sua meta de estudo.</p><div className="settings-fields profile-fields"><label>Tema<select value={preferences.theme} onChange={(e) => setPreferences({ ...preferences, theme: e.target.value })}><option value="system">Usar configuração do sistema</option><option value="light">Claro</option><option value="dark">Escuro</option></select></label><label>Idioma<select value={preferences.language} onChange={(e) => setPreferences({ ...preferences, language: e.target.value })}><option value="pt-BR">Português (Brasil)</option></select></label><label>Meta diária de estudo (minutos)<input type="number" min="1" max="1440" required value={preferences.daily_study_goal_minutes} onChange={(e) => setPreferences({ ...preferences, daily_study_goal_minutes: Number(e.target.value) })} /></label></div><Status value={statuses.preferences || emptyStatus} /><div className="settings-actions"><button disabled={saving === "preferences" || !changed(preferences, savedPreferences)}>{saving === "preferences" ? "Salvando..." : "Salvar preferências"}</button></div></form>
      <section className="card settings-section account-card"><span className="eyebrow">CONTA E SESSÃO</span><h2>Conta</h2><dl className="account-details"><div><dt>Usuário desde</dt><dd>{dateTime(user?.date_joined)}</dd></div><div><dt>Último acesso</dt><dd>{dateTime(user?.last_login)}</dd></div><div><dt>Sessão</dt><dd>{accountLabel}</dd></div><div><dt>E-mail</dt><dd>{profile.email || "Não informado"}</dd></div></dl><div className="settings-actions"><button type="button" className="secondary-button" onClick={signOut}>Sair da conta</button></div></section>
      <section className="card settings-section danger-zone"><span className="eyebrow">ZONA DE PERIGO</span><h2>Excluir minha conta</h2><p className="section-description">Sua conta será desativada e você perderá o acesso imediatamente.</p>{!showDelete ? <div className="settings-actions"><button type="button" className="danger-button" onClick={() => setShowDelete(true)}>Excluir minha conta</button></div> : <form onSubmit={deleteAccount}><div className="danger-confirmation"><label>Senha atual<input type="password" required value={deleteData.current_password} onChange={(e) => setDeleteData({ ...deleteData, current_password: e.target.value })} /></label><label>Digite EXCLUIR MINHA CONTA<input required value={deleteData.confirmation} onChange={(e) => setDeleteData({ ...deleteData, confirmation: e.target.value })} /></label></div><Status value={statuses.delete || emptyStatus} /><div className="settings-actions split-actions"><button type="button" className="secondary-button" onClick={() => setShowDelete(false)}>Cancelar</button><button className="danger-button" disabled={saving === "delete" || !deleteData.current_password || deleteData.confirmation !== "EXCLUIR MINHA CONTA"}>{saving === "delete" ? "Excluindo..." : "Confirmar exclusão"}</button></div></form>}</section>
    </div>
  </section>;
}
