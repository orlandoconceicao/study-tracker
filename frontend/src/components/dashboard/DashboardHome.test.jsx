import React from "react";
import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import DashboardHome from "./DashboardHome";
import { studiesApi } from "../../services/studies";
import { renderWithProviders } from "../../test/render";

vi.mock("../../services/studies", () => ({
  studiesApi: { statistics: vi.fn(), list: vi.fn() },
}));
vi.mock("../Calendar", () => ({ default: () => <div>Calendar mock</div> }));

const stats = {
  total_studied_days: 3,
  current_streak: 2,
  best_streak: 4,
};

describe("DashboardHome", () => {
  it("loads the summary and the five most recent studies", async () => {
    studiesApi.statistics.mockResolvedValueOnce({ data: stats });
    studiesApi.list.mockResolvedValueOnce({
      data: Array.from({ length: 6 }, (_, index) => ({
        id: index + 1,
        subject: `Subject ${index + 1}`,
        date: "2026-08-08",
        duration_minutes: 60,
        notes: "",
      })),
    });
    renderWithProviders(<DashboardHome />);
    expect(screen.getByText(/Carregando seu resumo/i)).toBeInTheDocument();
    expect(await screen.findByText("3 dias")).toBeInTheDocument();
    expect(screen.getByText("2 dias")).toBeInTheDocument();
    expect(screen.getByText("Subject 5")).toBeInTheDocument();
    expect(screen.queryByText("Subject 6")).not.toBeInTheDocument();
  });

  it("shows an error when dashboard requests fail", async () => {
    studiesApi.statistics.mockRejectedValueOnce(new Error("network"));
    studiesApi.list.mockResolvedValueOnce({ data: [] });
    renderWithProviders(<DashboardHome />);
    expect(await screen.findByText(/carregar seu resumo de estudos/i)).toBeInTheDocument();
  });
});
