import React from "react";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AuthContext } from "../context/AuthContext";

export const defaultAuth = {
  user: { id: 1, username: "ana", email: "ana@example.com" },
  preferences: { theme: "system", language: "pt-BR", daily_study_goal_minutes: 60 },
  loading: false,
  login: vi.fn(),
  logout: vi.fn(),
  register: vi.fn(),
  updateProfile: vi.fn(),
  updatePreferences: vi.fn(),
};

export function renderWithProviders(ui, { route = "/", auth = defaultAuth } = {}) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <AuthContext.Provider value={auth}>{ui}</AuthContext.Provider>
    </MemoryRouter>,
  );
}
