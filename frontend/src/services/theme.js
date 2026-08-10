export const THEME_STORAGE_KEY = "study_theme";
export const SYSTEM_THEME_QUERY = "(prefers-color-scheme: dark)";

const systemMedia = () => window.matchMedia?.(SYSTEM_THEME_QUERY) || { matches: false };

export function resolveTheme(preference, media = systemMedia()) {
  return preference === "system" ? (media.matches ? "dark" : "light") : preference;
}

export function applyTheme(preference = "system") {
  const normalized = ["light", "dark", "system"].includes(preference) ? preference : "system";
  const resolved = resolveTheme(normalized);
  document.documentElement.dataset.theme = resolved;
  document.documentElement.style.colorScheme = resolved;
  localStorage.setItem(THEME_STORAGE_KEY, normalized);
  return resolved;
}

export function initializeTheme() {
  return applyTheme(localStorage.getItem(THEME_STORAGE_KEY) || "system");
}
