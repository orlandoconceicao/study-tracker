import React from "react";
import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import NotFound from "./not-found";
import { renderWithProviders } from "../test/render";

describe("NotFound", () => {
  it("identifies the missing route and offers a valid destination", () => {
    renderWithProviders(<NotFound />, { route: "/missing" });

    expect(screen.getByRole("heading", { name: "Página não encontrada" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Voltar ao dashboard" })).toHaveAttribute("href", "/dashboard");
  });
});
