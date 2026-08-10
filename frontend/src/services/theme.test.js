import { afterEach, describe, expect, it, vi } from "vitest";
import { applyTheme, resolveTheme, THEME_STORAGE_KEY } from "./theme";

describe("tema da interface", () => {
  afterEach(() => {
    localStorage.clear();
    delete document.documentElement.dataset.theme;
    document.documentElement.style.colorScheme = "";
    vi.restoreAllMocks();
  });

  it("aplica e persiste os temas claro e escuro", () => {
    applyTheme("dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe("dark");
    applyTheme("light");
    expect(document.documentElement.dataset.theme).toBe("light");
  });

  it("resolve o tema do sistema com prefers-color-scheme", () => {
    expect(resolveTheme("system", { matches: true })).toBe("dark");
    expect(resolveTheme("system", { matches: false })).toBe("light");
  });
});
