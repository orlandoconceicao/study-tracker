import React from "react";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import Settings from "./settings";
import api from "../services/api";
import { defaultAuth, renderWithProviders } from "../test/render";

vi.mock("../services/api", () => ({ default: { get: vi.fn(), patch: vi.fn() } }));

describe("Settings", () => {
  it("loads and saves reminder preferences", async () => {
    api.get.mockResolvedValueOnce({ data: { enabled: false, reminder_time: null, timezone: "America/Manaus" } });
    api.patch.mockResolvedValueOnce({});
    renderWithProviders(<Settings />, { auth: defaultAuth });
    expect(await screen.findByRole("radio", { name: /UTC.4/i })).toBeChecked();
    await userEvent.click(screen.getByRole("radio", { name: /UTC.3/i }));
    await userEvent.click(screen.getByRole("checkbox"));
    await userEvent.type(screen.getByLabelText(/^Hor.rio$/i), "20:00");
    await userEvent.click(screen.getByRole("button", { name: "Salvar lembrete" }));
    await waitFor(() => expect(api.patch).toHaveBeenCalledWith("/notifications/settings/", { enabled: true, reminder_time: "20:00", timezone: "America/Sao_Paulo" }));
    expect(screen.getByText(/prefer.ncias de lembrete atualizadas/i)).toBeInTheDocument();
  });

  it("updates the profile through auth context", async () => {
    api.get.mockResolvedValueOnce({ data: {} });
    const updateProfile = vi.fn().mockResolvedValue({});
    renderWithProviders(<Settings />, { auth: { ...defaultAuth, updateProfile } });
    const username = screen.getByLabelText(/Nome de usu.rio/i);
    await userEvent.clear(username);
    await userEvent.type(username, "ana_updated");
    await userEvent.click(screen.getByRole("button", { name: "Salvar perfil" }));
    await waitFor(() => expect(updateProfile).toHaveBeenCalledWith({ username: "ana_updated", email: "ana@example.com" }));
    expect(screen.getByText(/Perfil atualizado com sucesso/i)).toBeInTheDocument();
  });

  it("shows backend validation errors", async () => {
    api.get.mockResolvedValueOnce({ data: {} });
    const updateProfile = vi.fn().mockRejectedValue({ response: { data: { email: ["Este e-mail já está em uso."] } } });
    renderWithProviders(<Settings />, { auth: { ...defaultAuth, updateProfile } });
    await userEvent.click(screen.getByRole("button", { name: "Salvar perfil" }));
    expect(await screen.findByText("Este e-mail já está em uso.")).toBeInTheDocument();
  });

  it("reports reminder loading failure", async () => {
    api.get.mockRejectedValueOnce(new Error("network"));
    renderWithProviders(<Settings />);
    expect(await screen.findByText(/carregar suas prefer.ncias/i)).toBeInTheDocument();
  });
});
