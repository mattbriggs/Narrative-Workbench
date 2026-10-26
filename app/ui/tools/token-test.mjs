// token-test.mjs  (spec SS10 verification check 1)
// Fails the build if component or screen code contains literal visual values,
// or references base tokens directly, or if any DTCG alias is unresolved.
// Components MUST reference role-token CSS variables only (CLAUDE.md C-2).
//
// Usage: node app/ui/tools/token-test.mjs
// Exit 0 = pass, 1 = fail (prints each offending file:line).

import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, extname } from "node:path";
import { execFileSync } from "node:child_process";

const ROOT = new URL("../../../", import.meta.url).pathname; // repo root
const SCAN_DIRS = [join(ROOT, "app/ui/components"), join(ROOT, "app/ui/screens")];
const TOKENS = join(ROOT, "design-tokens/tokens.dtcg.json");

// Patterns that must never appear as literals in component code.
const FORBIDDEN = [
  { name: "hex color", re: /#[0-9A-Fa-f]{3,8}\b/ },
  { name: "rgb()/rgba()", re: /\brgba?\s*\(/ },
  { name: "hsl()/hsla()", re: /\bhsla?\s*\(/ },
  { name: "px length", re: /(?<![\w-])\d+(?:\.\d+)?px\b/ },
  { name: "rem length", re: /(?<![\w-])\d+(?:\.\d+)?rem\b/ },
  { name: "ms duration", re: /(?<![\w-])\d+(?:\.\d+)?ms\b/ },
  { name: "font-family literal", re: /font-family\s*:(?!\s*var\()/i },
  { name: "base-token reference", re: /var\(\s*--(?:color|dimension|radius|duration|fontFamily)-base-/ },
];

// Allowed exceptions: lines that are clearly non-visual (e.g. ARIA, data, comments
// referencing spec ids) are still scanned; the patterns above are visual-only.

function walk(dir) {
  let files = [];
  let entries;
  try { entries = readdirSync(dir); } catch { return files; }
  for (const e of entries) {
    const p = join(dir, e);
    const s = statSync(p);
    if (s.isDirectory()) files = files.concat(walk(p));
    else if ([".js", ".mjs", ".css", ".html"].includes(extname(p))) files.push(p);
  }
  return files;
}

const offenses = [];
for (const dir of SCAN_DIRS) {
  for (const file of walk(dir)) {
    const text = readFileSync(file, "utf8").split("\n");
    text.forEach((line, i) => {
      // Skip lines that only use a role-token var and nothing literal.
      for (const { name, re } of FORBIDDEN) {
        if (re.test(line)) offenses.push(`${file}:${i + 1}  [${name}]  ${line.trim()}`);
      }
    });
  }
}

// Verify DTCG aliases resolve (reuse the build script's exit code).
let aliasOk = true;
try {
  execFileSync("node", [join(ROOT, "design-tokens/build-tokens.mjs"), TOKENS, "/tmp/.nw-token-check.css"], { stdio: "pipe" });
} catch (err) {
  aliasOk = false;
  console.error("Alias resolution failed:\n" + (err.stderr?.toString() ?? err.message));
}

if (offenses.length || !aliasOk) {
  if (offenses.length) {
    console.error(`Token test FAILED: ${offenses.length} literal/base-token offense(s):`);
    offenses.forEach((o) => console.error("  " + o));
  }
  process.exit(1);
}
console.log("Token test PASSED: no literal visual values; role tokens only; 0 unresolved aliases.");
