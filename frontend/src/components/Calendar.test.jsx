import React from "react";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import Calendar from "./Calendar";
import { studiesApi } from "../services/studies";
import { renderWithProviders } from "../test/render";

vi.mock("../services/studies", () => ({ studiesApi: { calendar: vi.fn(), list: vi.fn() } }));

describe("Calendar", () => {
  it("loads a month and opens studied-day details", async () => {
    const now = new Date();
    const key = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-01`;
    studiesApi.calendar.mockResolvedValueOnce({ data: { [key]: { studied: true, total_minutes: 45 } } });
    studiesApi.list.mockResolvedValueOnce({ data: [{ id: 1, subject: "Math", duration_minutes: 45, notes: "Algebra" }] });
    renderWithProviders(<Calendar />);
    const day = await screen.findByTitle("45 minutos estudados");
    await userEvent.click(day);
    expect(studiesApi.list).toHaveBeenCalledWith({ start_date: key, end_date: key });
    expect(await screen.findByText("Math")).toBeInTheDocument();
  });

  it("shows a month loading error", async () => {
    studiesApi.calendar.mockRejectedValueOnce(new Error("network"));
    renderWithProviders(<Calendar />);
    expect(await screen.findByText(/carregar o calend.rio/i)).toBeInTheDocument();
  });
});
