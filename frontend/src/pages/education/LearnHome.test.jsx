import React from "react";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LearnHome from "./LearnHome";
import { educationApi } from "../../services/education";
import { renderWithProviders } from "../../test/render";

vi.mock("../../services/education", () => ({
  collection: (response) => response.data?.results || response.data || [],
  educationApi: { getChildren: vi.fn(), getLevels: vi.fn(), getGrades: vi.fn(), getChildSubjects: vi.fn(), createChild: vi.fn(), updateChild: vi.fn() },
}));

const levels = [{ id: 1, name: "Ensino Fundamental II" }];
const grades = [{ id: 7, education_level: 1, name: "7º ano" }];
const prepare = (children = []) => {
  educationApi.getChildren.mockResolvedValue({ data: children });
  educationApi.getLevels.mockResolvedValue({ data: levels });
  educationApi.getGrades.mockResolvedValue({ data: grades });
};

describe("LearnHome", () => {
  beforeEach(() => { vi.clearAllMocks(); localStorage.clear(); });

  it("orienta o responsável a cadastrar um filho", async () => {
    prepare(); renderWithProviders(<LearnHome />);
    expect(await screen.findByText("Antes de começar")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Cadastrar filho" }));
    expect(screen.getByLabelText("Nome do filho")).toBeInTheDocument();
  });

  it("completa o perfil escolar usando níveis e séries do backend", async () => {
    prepare([{ id: 2, name: "João", education_level: null, grade: null, active: true }]);
    educationApi.updateChild.mockResolvedValue({ data: { id: 2 } });
    educationApi.getChildSubjects.mockResolvedValue({ data: [] });
    renderWithProviders(<LearnHome />);
    expect(await screen.findByText("Complete o perfil escolar")).toBeInTheDocument();
    await userEvent.selectOptions(screen.getByLabelText("Nível de escolaridade"), "1");
    await userEvent.selectOptions(screen.getByLabelText("Série/Ano"), "7");
    await userEvent.click(screen.getByRole("button", { name: "Salvar e continuar" }));
    await waitFor(() => expect(educationApi.updateChild).toHaveBeenCalledWith(2, { name: "João", education_level: 1, grade: 7, active: true }));
  });

  it("permite trocar o filho ativo sem misturar a seleção", async () => {
    const children = [{ id: 2, name: "João", education_level: 1, grade: 7, grade_name: "7º ano", active: true }, { id: 3, name: "Maria", education_level: 1, grade: 7, grade_name: "7º ano", active: true }];
    prepare(children); educationApi.getChildSubjects.mockResolvedValue({ data: [] });
    renderWithProviders(<LearnHome />);
    const selector = await screen.findByLabelText("Estudando com:");
    await userEvent.selectOptions(selector, "3");
    await waitFor(() => expect(localStorage.getItem("study_active_child")).toBe("3"));
    expect(educationApi.getChildSubjects).toHaveBeenCalledWith(3);
  });

  it("recupera um filho com curriculo publicado quando a selecao salva esta vazia", async () => {
    const children = [
      { id: 1, name: "Orlando", education_level: 1, grade: 7, grade_name: "7o ano", active: true },
      { id: 2, name: "Vitor", education_level: 1, grade: 8, grade_name: "8o ano", active: true },
    ];
    prepare(children);
    localStorage.setItem("study_active_child", "2");
    educationApi.getChildSubjects.mockImplementation((childId) => Promise.resolve({ data: childId === 1 ? [{ id: 10, subject: { id: 3, name: "Matematica", icon: "M" }, content_count: 5 }] : [] }));

    renderWithProviders(<LearnHome />);

    await waitFor(() => expect(localStorage.getItem("study_active_child")).toBe("1"));
    expect(educationApi.getChildSubjects).toHaveBeenCalledWith(2);
    expect(educationApi.getChildSubjects).toHaveBeenCalledWith(1);
  });
});
