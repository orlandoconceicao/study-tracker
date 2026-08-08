import React from "react";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import Layout from "./Layout";
import { defaultAuth, renderWithProviders } from "../test/render";

const routes = <Routes><Route path="/login" element={<p>Login screen</p>} /><Route element={<Layout />}><Route path="/dashboard" element={<p>Private content</p>} /></Route></Routes>;

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
});
