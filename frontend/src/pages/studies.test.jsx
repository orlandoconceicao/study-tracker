import React from "react";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import Studies from "./studies";
import { studiesApi } from "../services/studies";
import { renderWithProviders } from "../test/render";

vi.mock("../services/studies", () => ({ studiesApi: { list: vi.fn(), remove: vi.fn() } }));

const study = { id: 1, subject: "Matemática", date: "2026-08-08", duration_minutes: 90, notes: "Álgebra" };

describe("Studies", () => {
  it("renders loading, results and applies filters", async () => {
    studiesApi.list.mockResolvedValue({ data: [study] });
    renderWithProviders(<Studies />, { route: "/studies" });
    expect(screen.getByText(/Carregando seus estudos/i)).toBeInTheDocument();
    expect(await screen.findByText("Matemática")).toBeInTheDocument();
    expect(screen.getByText("1h 30min")).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText("Assunto"), "Mat");
    await userEvent.click(screen.getByRole("button", { name: "Filtrar" }));
    await waitFor(() => expect(studiesApi.list).toHaveBeenLastCalledWith(expect.objectContaining({ subject: "Mat" })));
  });

  it("keeps a study when deletion is cancelled", async () => {
    studiesApi.list.mockResolvedValueOnce({ data: [study] });
    vi.spyOn(window, "confirm").mockReturnValue(false);
    renderWithProviders(<Studies />, { route: "/studies" });
    await userEvent.click(await screen.findByRole("button", { name: "Excluir" }));
    expect(studiesApi.remove).not.toHaveBeenCalled();
  });

  it("deletes after confirmation and reloads", async () => {
    studiesApi.list.mockResolvedValueOnce({ data: [study] }).mockResolvedValueOnce({ data: [] });
    studiesApi.remove.mockResolvedValueOnce({});
    vi.spyOn(window, "confirm").mockReturnValue(true);
    renderWithProviders(<Studies />, { route: "/studies" });
    await userEvent.click(await screen.findByRole("button", { name: "Excluir" }));
    await waitFor(() => expect(studiesApi.remove).toHaveBeenCalledWith(1));
    expect(await screen.findByText("Nenhum estudo encontrado")).toBeInTheDocument();
  });

  it("renders a server error", async () => {
    studiesApi.list.mockRejectedValueOnce({ response: { data: { detail: "Falha específica" } } });
    renderWithProviders(<Studies />, { route: "/studies" });
    expect(await screen.findByText("Falha específica")).toBeInTheDocument();
  });
});
