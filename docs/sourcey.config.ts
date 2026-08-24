import { defineConfig, markdown } from "sourcey";
import { readdirSync } from "node:fs";
import { join } from "node:path";

const generatedApiPages = readdirSync(join(import.meta.dirname, "reference/generated"))
  .filter((file) => file.endsWith(".md"))
  .map((file) => `reference/generated/${file.slice(0, -3)}`)
  .sort();

const pages = {
  gettingStarted: ["guides/getting-started", "guides/package-surface"],
  core: ["core/primitives", "core/containers", "core/workflows"],
  operations: ["operations/inputs", "operations/logging"],
  examples: ["examples/core", "examples/inputs", "examples/logging"],
  architecture: ["guides/architecture", "guides/pillars", "guides/ownership-map"],
  maintainers: ["guides/publishing", "guides/PUBLISHING_CHECKLIST"],
  reference: ["reference/index", ...generatedApiPages],
};

export default defineConfig({
  name: "Extended Data",
  theme: {
    preset: "default",
    colors: { primary: "#0f766e", light: "#14b8a6", dark: "#115e59" },
    fonts: { sans: "Inter", mono: "JetBrains Mono" },
    css: ["./styles.css"],
  },
  logo: { light: "./assets/extended-data-hero.png", dark: "./assets/extended-data-hero.png", href: "/" },
  favicon: "./assets/favicon.png",
  repo: "https://github.com/jbcom/extended-data",
  editBranch: "main",
  navigation: {
    tabs: [
      { tab: "Documentation", slug: "", source: markdown({ groups: [
        { group: "Getting Started", pages: pages.gettingStarted }, { group: "Core", pages: pages.core },
        { group: "Operations", pages: pages.operations }, { group: "Examples", pages: pages.examples },
      ] }) },
      { tab: "Architecture", slug: "architecture", source: markdown({ groups: [{ group: "Design", pages: pages.architecture }] }) },
      { tab: "API Reference", slug: "api", source: markdown({ groups: [{ group: "Python API", pages: pages.reference }] }) },
      { tab: "Maintainers", slug: "maintainers", source: markdown({ groups: [{ group: "Release and publishing", pages: pages.maintainers }] }) },
    ],
  },
  navbar: { links: [{ type: "github", href: "https://github.com/jbcom/extended-data" }] },
  footer: { links: [{ type: "github", href: "https://github.com/jbcom/extended-data" }] },
});
