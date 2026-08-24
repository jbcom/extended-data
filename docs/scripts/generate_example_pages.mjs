import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";

const groups = {
  core: ["basic_usage.py", "composed_workflows.py", "file_operations.py", "serialization.py", "string_transformations.py"],
  inputs: ["basic_usage.py", "decorator_api.py", "encoding_decoding.py"],
  logging: ["basic_logging.py", "exit_run_formatting.py", "markers_and_storage.py", "verbosity_control.py"],
};
const title = (value) => value.replace(/\.py$/, "").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
const check = process.argv.includes("--check");

for (const [group, files] of Object.entries(groups)) {
  const sections = await Promise.all(files.map(async (file) => {
    const relative = `packages/extended-data/examples/${group}/${file}`;
    const source = await readFile(new URL(`../../${relative}`, import.meta.url), "utf8");
    return `## ${title(file)}\n\n[View source](https://github.com/jbcom/extended-data/blob/main/${relative})\n\n\`\`\`python\n${source.trim()}\n\`\`\`\n`;
  }));
  const content = `---\ntitle: ${title(group)} Examples\ndescription: Runnable examples rendered from their tested Python sources.\n---\n\n# ${title(group)} Examples\n\n${sections.join("\n")}`;
  const destination = new URL(`../examples/${group}.md`, import.meta.url);
  if (check) {
    const current = await readFile(destination, "utf8");
    if (createHash("sha256").update(current).digest("hex") !== createHash("sha256").update(content).digest("hex")) throw new Error(`stale example page: ${destination.pathname}`);
  } else await writeFile(destination, content);
}
