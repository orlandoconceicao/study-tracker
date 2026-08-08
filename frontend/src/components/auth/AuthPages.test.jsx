import React from "react";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { LoginPage, RegisterPage } from "./AuthPages";
import { defaultAuth, renderWithProviders } from "../../test/render";

describe("authentication pages", () => {
  it("submits login credentials and navigates on success", async () => {
    const login = vi.fn().mockResolvedValue(undefined);
    renderWithProviders(<Routes><Route path="/login" element={<LoginPage />} /><Route path="/dashboard" element={<p>Dashboard</p>} /></Routes>, { route: "/login", auth: { ...defaultAuth, login } });
    const user = userEvent.setup();
    await user.type(screen.getByLabelText(/Usu.rio/i), "ana");
    await user.type(screen.getByLabelText("Senha"), "password123");
    await user.click(screen.getByRole("button", { name: "Entrar" }));
    await waitFor(() => expect(login).toHaveBeenCalledWith({ username: "ana", password: "password123" }));
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  it("shows an error when login fails", async () => {
    const login = vi.fn().mockRejectedValue(new Error("invalid"));
    renderWithProviders(<LoginPage />, { route: "/login", auth: { ...defaultAuth, login } });
    const user = userEvent.setup();
    await user.type(screen.getByLabelText(/Usu.rio/i), "ana");
    await user.type(screen.getByLabelText("Senha"), "wrong");
    await user.click(screen.getByRole("button", { name: "Entrar" }));
    expect(await screen.findByText(/senha inv.lidos/i)).toBeInTheDocument();
  });

  it("validates password confirmation before registering", async () => {
    const register = vi.fn();
    renderWithProviders(<RegisterPage />, { route: "/register", auth: { ...defaultAuth, register } });
    const user = userEvent.setup();
    await user.type(screen.getByLabelText(/Usu.rio/i), "ana");
    await user.type(screen.getByLabelText("E-mail"), "ana@example.com");
    const passwords = screen.getAllByLabelText(/Senha|Confirmar senha/i);
    await user.type(passwords[0], "password123");
    await user.type(passwords[1], "different123");
    await user.click(screen.getByRole("button", { name: "Criar conta" }));
    expect(register).not.toHaveBeenCalled();
    expect(screen.getByText(/n.o coincidem/i)).toBeInTheDocument();
  });

  it("toggles password visibility", async () => {
    renderWithProviders(<LoginPage />, { route: "/login" });
    const password = screen.getByLabelText("Senha");
    await userEvent.click(screen.getByRole("button", { name: "Mostrar" }));
    expect(password).toHaveAttribute("type", "text");
    await userEvent.click(screen.getByRole("button", { name: "Ocultar" }));
    expect(password).toHaveAttribute("type", "password");
  });
});
