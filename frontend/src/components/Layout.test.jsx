import React from "react";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Link, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import Layout from "./Layout";
import { defaultAuth, renderWithProviders } from "../test/render";

const routes = <Routes><Route path="/login" element={<p>Login screen</p>} /><Route element={<Layout />}><Route path="/dashboard" element={<><p>Private content</p><Link to="/studies/new">Add study</Link></>} /><Route path="/studies" element={<p>Studies screen</p>} /><Route path="/studies/new" element={<p>New study screen</p>} /></Route></Routes>;

describe("Layout route protection", () => {
  it("shows loading state", () => {
    renderWithProviders(routes, { route: "/dashboard", auth: { ...defaultAuth, loading: true } });
    expect(screen.getByText(/Carregando seu espa/i)).toBeInTheDocument();
  });

  it("redirects anonymous users to login", () => {
    renderWithProviders(routes, { route: "/dashboard", auth: { ...defaultAuth, user: null } });
    expect(screen.getByText("Login screen")).toBeInTheDocument();
  });

  it("renders private content and logs out", async () => {
    const logout = vi.fn();
    renderWithProviders(routes, { route: "/dashboard", auth: { ...defaultAuth, logout } });
    expect(screen.getByText("Private content")).toBeInTheDocument();
    await userEvent.click(screen.getAllByRole("button", { name: /Sair/i })[0]);
    expect(logout).toHaveBeenCalledOnce();
  });

  it("closes the mobile menu after navigating", async () => {
    renderWithProviders(routes, { route: "/dashboard", auth: defaultAuth });
    const menuButton = screen.getByRole("button", { name: "Abrir menu" });

    await userEvent.click(menuButton);
    expect(screen.getByRole("button", { name: "Fechar menu" })).toHaveAttribute("aria-expanded", "true");

    await userEvent.click(screen.getAllByRole("link", { name: /Estudos/i })[0]);

    expect(screen.getByText("Studies screen")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Abrir menu" })).toHaveAttribute("aria-expanded", "false");
  });

  it("closes the mobile menu when the route changes outside the sidebar", async () => {
    renderWithProviders(routes, { route: "/dashboard", auth: defaultAuth });
    await userEvent.click(screen.getByRole("button", { name: "Abrir menu" }));
    await userEvent.click(screen.getByRole("link", { name: "Add study" }));

    expect(screen.getByText("New study screen")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Abrir menu" })).toHaveAttribute("aria-expanded", "false");
  });
});
