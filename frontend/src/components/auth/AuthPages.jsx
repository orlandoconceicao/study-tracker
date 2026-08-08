import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import AuthLayout from "./AuthLayout";
import AuthInput from "./AuthInput";
import "../../styles/auth.css";

function Shell({ children, title, subtitle, footer }) {
  return (
    <AuthLayout>
      <div className="auth-card">
        <div>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </div>
        {children}
        <footer>{footer}</footer>
      </div>
    </AuthLayout>
  );
}
export function LoginPage() {
  const { login } = useAuth(),
    nav = useNavigate(),
    [form, setForm] = useState({ username: "", password: "" }),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(form);
      nav("/dashboard");
    } catch {
      setError("Usuário ou senha inválidos.");
    } finally {
      setLoading(false);
    }
  };
  return (
    <Shell
      title="Bem-vindo de volta"
      subtitle="Entre para continuar acompanhando seu progresso."
      footer={
        <>
          Ainda não tem uma conta? <Link to="/register">Criar conta</Link>
        </>
      }
    >
      <form onSubmit={submit}>
        <AuthInput
          label="Usuário"
          placeholder="Digite seu usuário"
          value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })}
          required
          disabled={loading}
        />
        <AuthInput
          label="Senha"
          type="password"
          placeholder="Digite sua senha"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
          disabled={loading}
        />
        {error && <p className="auth-error">{error}</p>}
        <button className="auth-submit" disabled={loading}>
          {loading ? "Entrando..." : "Entrar"}
        </button>
      </form>
    </Shell>
  );
}
export function RegisterPage() {
  const { register } = useAuth(),
    nav = useNavigate(),
    [form, setForm] = useState({
      username: "",
      email: "",
      password: "",
      confirm: "",
    }),
    [error, setError] = useState(""),
    [loading, setLoading] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    if (form.password !== form.confirm)
      return setError("As senhas não coincidem.");
    setError("");
    setLoading(true);
    try {
      await register({
        username: form.username,
        email: form.email,
        password: form.password,
      });
      nav("/login");
    } catch {
      setError("Verifique os campos e tente novamente.");
    } finally {
      setLoading(false);
    }
  };
  return (
    <Shell
      title="Crie sua conta"
      subtitle="Comece a acompanhar sua rotina de estudos."
      footer={
        <>
          Já possui uma conta? <Link to="/login">Entrar</Link>
        </>
      }
    >
      <form onSubmit={submit}>
        <AuthInput
          label="Usuário"
          placeholder="Digite seu usuário"
          value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })}
          required
          disabled={loading}
        />
        <AuthInput
          label="E-mail"
          type="email"
          placeholder="voce@email.com"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
          disabled={loading}
        />
        <AuthInput
          label="Senha"
          type="password"
          placeholder="Crie uma senha"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          minLength="8"
          required
          disabled={loading}
        />
        <AuthInput
          label="Confirmar senha"
          type="password"
          placeholder="Digite a senha novamente"
          value={form.confirm}
          onChange={(e) => setForm({ ...form, confirm: e.target.value })}
          required
          disabled={loading}
        />
        {error && <p className="auth-error">{error}</p>}
        <button className="auth-submit" disabled={loading}>
          {loading ? "Criando conta..." : "Criar conta"}
        </button>
      </form>
    </Shell>
  );
}
