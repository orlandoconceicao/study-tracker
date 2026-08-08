import React from "react";
import { screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import Statistics from "./statistics";
import { studiesApi } from "../services/studies";
import { renderWithProviders } from "../test/render";

vi.mock("../services/studies", () => ({ studiesApi: { statistics: vi.fn() } }));

describe("Statistics", () => {
  it("renders loading and formatted statistics", async () => {
    studiesApi.statistics.mockResolvedValueOnce({ data: { total_studied_days: 4, total_hours: 2.5, current_streak: 2, best_streak: 3, average_minutes_per_day: 38, week_minutes: 90, month_minutes: 150 } });
    renderWithProviders(<Statistics />);
    expect(screen.getByText(/Carregando suas estat/i)).toBeInTheDocument();
    expect(await screen.findByText("2h 30min")).toBeInTheDocument();
    expect(screen.getByText("38 min")).toBeInTheDocument();
  });

  it("shows API error detail", async () => {
    studiesApi.statistics.mockRejectedValueOnce({ response: { data: { detail: "Sem acesso" } } });
    renderWithProviders(<Statistics />);
    expect(await screen.findByText("Sem acesso")).toBeInTheDocument();
  });
});
