import React from "react";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Settings from "./settings";
import api from "../services/api";
import { defaultAuth, renderWithProviders } from "../test/render";

vi.mock("../services/api", () => ({ default: { get: vi.fn(), patch: vi.fn(), post: vi.fn(), delete: vi.fn() } }));

const loadSettings = () => {
  api.get.mockResolvedValueOnce({ data: { enabled: false, reminder_time: null, timezone: "America/Manaus" } });
  api.get.mockResolvedValueOnce({ data: { theme: "system", language: "pt-BR", daily_study_goal_minutes: 60 } });
};

describe("Settings", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("carrega e salva lembretes", async () => {
    loadSettings(); api.patch.mockResolvedValueOnce({});
    renderWithProviders(<Settings />, { auth: defaultAuth });
    expect(await screen.findByLabelText(/Fuso hor.rio/i)).toHaveValue("America/Manaus");
    await userEvent.selectOptions(screen.getByLabelText(/Fuso hor.rio/i), "America/Sao_Paulo");
    await userEvent.click(screen.getByRole("checkbox"));
    await userEvent.type(screen.getByLabelText(/^Hor.rio$/i), "20:00");
    await userEvent.click(screen.getByRole("button", { name: "Salvar lembrete" }));
    await waitFor(() => expect(api.patch).toHaveBeenCalledWith("/notifications/settings/", { enabled: true, reminder_time: "20:00", timezone: "America/Sao_Paulo" }));
    expect(screen.getByText(/Lembrete atualizado com sucesso/i)).toBeInTheDocument();
  });

  it("edita o perfil e atualiza o AuthContext", async () => {
    loadSettings(); const updateProfile = vi.fn().mockResolvedValue({});
    renderWithProviders(<Settings />, { auth: { ...defaultAuth, updateProfile } });
    const username = await screen.findByLabelText(/Nome de usu.rio/i);
    await userEvent.clear(username); await userEvent.type(username, "ana_updated");
    await userEvent.click(screen.getByRole("button", { name: "Salvar perfil" }));
    await waitFor(() => expect(updateProfile).toHaveBeenCalledWith({ first_name: "", last_name: "", username: "ana_updated", email: "ana@example.com" }));
    expect(screen.getByText(/Perfil atualizado com sucesso/i)).toBeInTheDocument();
  });

  it("altera senha e salva preferências", async () => {
    loadSettings(); api.post.mockResolvedValueOnce({});
    const updatePreferences = vi.fn().mockResolvedValue({ theme: "dark", language: "pt-BR", daily_study_goal_minutes: 60 });
    renderWithProviders(<Settings />, { auth: { ...defaultAuth, updatePreferences } });
    await screen.findByLabelText(/Meta di.ria/i);
    await userEvent.type(screen.getByLabelText("Senha atual"), "password123");
    await userEvent.type(screen.getByLabelText("Nova senha"), "nova-senha-123");
    await userEvent.type(screen.getByLabelText("Confirmar nova senha"), "nova-senha-123");
    await userEvent.click(screen.getByRole("button", { name: "Alterar senha" }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith("/auth/change-password/", { current_password: "password123", new_password: "nova-senha-123", confirm_password: "nova-senha-123" }));
    await userEvent.selectOptions(screen.getByLabelText("Tema"), "dark");
    await userEvent.click(screen.getByRole("button", { name: "Salvar preferências" }));
    await waitFor(() => expect(updatePreferences).toHaveBeenCalledWith({ theme: "dark", language: "pt-BR", daily_study_goal_minutes: 60 }));
  });

  it("exibe erros e permite logout", async () => {
    loadSettings(); const updateProfile = vi.fn().mockRejectedValue({ response: { data: { email: ["Este e-mail já está em uso."] } } }); const logout = vi.fn();
    renderWithProviders(<Settings />, { auth: { ...defaultAuth, updateProfile, logout } });
    const email = await screen.findByLabelText("E-mail", { selector: "input" });
    await userEvent.clear(email); await userEvent.type(email, "outra@example.com");
    await userEvent.click(screen.getByRole("button", { name: "Salvar perfil" }));
    expect(await screen.findByText("Este e-mail já está em uso.")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Sair da conta" }));
    expect(logout).toHaveBeenCalled();
  });

});
