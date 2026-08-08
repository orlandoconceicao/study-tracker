import React from "react";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import StudyForm from "./study-form";
import { studiesApi } from "../services/studies";
import { renderWithProviders } from "../test/render";

vi.mock("../services/studies", () => ({ studiesApi: { get: vi.fn(), create: vi.fn(), update: vi.fn() } }));

const app = <Routes><Route path="/studies/new" element={<StudyForm />} /><Route path="/studies/:id/edit" element={<StudyForm />} /><Route path="/dashboard" element={<p>Dashboard</p>} /></Routes>;

describe("StudyForm", () => {
  it("creates a study with numeric duration and navigates", async () => {
    studiesApi.create.mockResolvedValueOnce({});
    renderWithProviders(app, { route: "/studies/new" });
    const user = userEvent.setup();
    await user.clear(screen.getByLabelText("Data"));
    await user.type(screen.getByLabelText("Data"), "2026-08-08");
    await user.type(screen.getByLabelText(/Dura/i), "45");
    await user.type(screen.getByLabelText("Assunto"), "Django");
    await user.type(screen.getByLabelText(/Observa/i), "Testes");
    await user.click(screen.getByRole("button", { name: "Salvar estudo" }));
    await waitFor(() => expect(studiesApi.create).toHaveBeenCalledWith({ date: "2026-08-08", duration_minutes: 45, subject: "Django", notes: "Testes" }));
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  it("loads and updates an existing study", async () => {
    studiesApi.get.mockResolvedValueOnce({ data: { date: "2026-08-01", duration_minutes: 30, subject: "Math", notes: "Algebra" } });
    studiesApi.update.mockResolvedValueOnce({});
    renderWithProviders(app, { route: "/studies/9/edit" });
    expect(await screen.findByDisplayValue("Math")).toBeInTheDocument();
    await userEvent.clear(screen.getByLabelText("Assunto"));
    await userEvent.type(screen.getByLabelText("Assunto"), "Physics");
    await userEvent.click(screen.getByRole("button", { name: "Salvar estudo" }));
    await waitFor(() => expect(studiesApi.update).toHaveBeenCalledWith("9", expect.objectContaining({ subject: "Physics", duration_minutes: 30 })));
  });

  it("shows API errors without navigating", async () => {
    studiesApi.create.mockRejectedValueOnce(new Error("bad request"));
    renderWithProviders(app, { route: "/studies/new" });
    const user = userEvent.setup();
    await user.type(screen.getByLabelText(/Dura/i), "10");
    await user.type(screen.getByLabelText("Assunto"), "Math");
    await user.click(screen.getByRole("button", { name: "Salvar estudo" }));
    expect(await screen.findByText(/Verifique os campos/i)).toBeInTheDocument();
  });
});
