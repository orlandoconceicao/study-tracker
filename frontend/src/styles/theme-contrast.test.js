import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const css = readFileSync(resolve(process.cwd(), "src/styles/global.css"), "utf8");

const luminance = (hex) => {
  const channels = hex.match(/[a-f\d]{2}/gi).map((part) => parseInt(part, 16) / 255);
  const [red, green, blue] = channels.map((value) => value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4);
  return (0.2126 * red) + (0.7152 * green) + (0.0722 * blue);
};

const contrast = (foreground, background) => {
  const values = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
  return (values[0] + 0.05) / (values[1] + 0.05);
};

const variables = (selector) => {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const block = css.match(new RegExp(`${escaped}\\s*\\{([\\s\\S]*?)\\}`))[1];
  return Object.fromEntries([...block.matchAll(/--([\w-]+):\s*(#[a-f\d]{6})/gi)].map((match) => [match[1].replace(/^color-/, ""), match[2]]));
};

describe("theme contrast tokens", () => {
  const light = variables(":root");
  const dark = { ...light, ...variables(':root[data-theme="dark"]') };

  it.each([["light", light], ["dark", dark]])("keeps readable text in %s mode", (_, theme) => {
    const textPairs = [
      ["text", "background"], ["text", "surface"], ["muted", "background"],
      ["muted", "surface"], ["placeholder", "input-background"],
      ["on-primary", "primary"], ["link", "surface-raised"],
      ["on-primary-muted", "primary"], ["disabled-text", "disabled-background"],
      ["error", "danger-soft"], ["success", "success-soft"],
      ["warning", "warning-soft"],
    ];
    textPairs.forEach(([foreground, background]) => expect(contrast(theme[foreground], theme[background]), `${foreground} on ${background}`).toBeGreaterThanOrEqual(4.5));
    expect(contrast(theme["control-border"], theme["input-background"]), "control border").toBeGreaterThanOrEqual(3);
  });

  it("preserves semantic colors after the generic button rule", () => {
    expect(css).toMatch(/\.button\.secondary-button\s*\{[^}]*color:\s*var\(--color-link\)/s);
    expect(css).toMatch(/\.disabled-link\s*\{[^}]*opacity:\s*1/s);
    expect(css).toMatch(/\.section-heading a:not\(\.button\)/);
  });
});
