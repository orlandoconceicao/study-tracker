import React from "react";
import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import RecentStudies from "./RecentStudies";
import { renderWithProviders } from "../../test/render";

describe("RecentStudies", () => {
  it("renders loading and empty states", () => {
    const { unmount } = renderWithProviders(<RecentStudies studies={[]} loading />);
    expect(screen.getByText(/Carregando seus estudos/i)).toBeInTheDocument();
    unmount();
    renderWithProviders(<RecentStudies studies={[]} loading={false} />);
    expect(screen.getByText(/Comece sua jornada de estudos/i)).toBeInTheDocument();
  });

  it("formats hours and minutes", () => {
    renderWithProviders(
      <RecentStudies
        loading={false}
        studies={[{ id: 1, subject: "Math", date: "2026-08-08", duration_minutes: 90, notes: "Algebra" }]}
      />,
    );
    expect(screen.getByText("1h 30min")).toBeInTheDocument();
    expect(screen.getByText(/Algebra/)).toBeInTheDocument();
  });
});
