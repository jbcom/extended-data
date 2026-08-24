import { createHash } from "node:crypto";
import { readFile, readdir, writeFile } from "node:fs/promises";
import { join, relative } from "node:path";

const root = new URL("../../packages/extended-data/src/extended_data/", import.meta.url).pathname;
const output = new URL("../reference/generated/", import.meta.url).pathname;
const check = process.argv.includes("--check");
async function files(dir) { const entries = await readdir(dir, { withFileTypes: true }); return (await Promise.all(entries.map(e => e.isDirectory() ? files(join(dir,e.name)) : e.name.endsWith(".py") && e.name !== "__init__.py" ? [join(dir,e.name)] : []))).flat(); }
function doc(s) { return s.replace(/^\s*"""[\s\S]*?"""/m, m => m.slice(3,-3).trim()); }
const paths = await files(root);
const index = [];
for (const path of paths) { const source = await readFile(path, "utf8"); const module = relative(root,path).replace(/\.py$/,"").replaceAll("/", "."); const slug = module.replaceAll(".", "-"); const publicLines = source.split("\n").filter(line => /^(class|def|async def) [A-Za-z][A-Za-z0-9_]*/.test(line) && !line.includes(" _")).join("\n"); const content = `---\ntitle: ${module}\ndescription: Public API documentation generated from source.\n---\n\n# \`${module}\`\n\n\`\`\`python\n${publicLines || "# This module exports package-level helpers."}\n\`\`\`\n\n## Source\n\n[View source](https://github.com/jbcom/extended-data/blob/main/packages/extended-data/src/extended_data/${relative(root,path)})\n`; const file = join(output, `${slug}.md`); index.push(`- [\`${module}\`](generated/${slug})`); if (check) { if (createHash("sha256").update(await readFile(file)).digest("hex") !== createHash("sha256").update(content).digest("hex")) throw new Error(`stale API reference: ${file}`); } else { await writeFile(file, content); } }
const reference = `---\ntitle: Python API Reference\ndescription: Deterministic API documentation from the public Python source.\n---\n\n# Python API Reference\n\n${index.join("\n")}\n`;
if (!check) await writeFile(new URL("../reference/index.md", import.meta.url), reference);
