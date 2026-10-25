// run-scenarios.mjs
// Serves the UI and drives it in headless Chromium (Playwright) to run the
// key SRS SS9 acceptance scenarios and capture screenshots of the five screens
// (spec SS10 checks 3-4, run headlessly in the cloud; the packaged desktop
// screenshot gate is verified on the user's Mac). Exits non-zero on any failure.
//
// Usage: node app/ui/tools/run-scenarios.mjs [screenshotDir]

import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { join, extname, resolve } from "node:path";
import { mkdirSync } from "node:fs";
import { createRequire } from "node:module";

// Playwright is installed in a shared tools dir; createRequire consults the
// global module paths that a relative ESM import would not.
const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const UI_ROOT = resolve(new URL("../", import.meta.url).pathname); // app/ui
const SHOT_DIR = process.argv[2] || resolve(UI_ROOT, "../../.screenshots");
mkdirSync(SHOT_DIR, { recursive: true });

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
};

function startServer() {
  const server = createServer(async (req, res) => {
    try {
      const urlPath = decodeURIComponent(req.url.split("?")[0]);
      const rel = urlPath === "/" ? "/index.html" : urlPath;
      const file = join(UI_ROOT, rel);
      if (!file.startsWith(UI_ROOT)) {
        res.writeHead(403).end("forbidden");
        return;
      }
      const body = await readFile(file);
      res.writeHead(200, { "content-type": MIME[extname(file)] || "application/octet-stream" }).end(body);
    } catch {
      res.writeHead(404).end("not found");
    }
  });
  return new Promise((r) => server.listen(0, () => r(server)));
}

const results = [];
function check(name, cond, detail = "") {
  results.push({ name, ok: !!cond, detail });
  console.log(`${cond ? "PASS" : "FAIL"}  ${name}${cond ? "" : "  <- " + detail}`);
}

async function main() {
  const server = await startServer();
  const { port } = server.address();
  const base = `http://127.0.0.1:${port}/`;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(base);
  await page.waitForFunction(() => window.NW !== undefined);

  const snap = () => page.evaluate(() => window.NW.snapshot());
  const text = (sel) => page.evaluate((s) => document.querySelector(s)?.textContent ?? null, sel);
  const attr = (sel, a) => page.evaluate(([s, aa]) => document.querySelector(s)?.getAttribute(aa) ?? null, [sel, a]);
  const exists = (sel) => page.evaluate((s) => !!document.querySelector(s), sel);

  // Screen 1/2: shell + Composition Studio (default).
  await page.screenshot({ path: join(SHOT_DIR, "01-shell-composition.png") });

  // S1: synchronized selection is non-mutating (REQ-002).
  const commitBefore = (await snap()).commitId;
  await page.evaluate(() => window.NW.selectNode("scene4"));
  const s1 = await snap();
  check("S1 selection is non-mutating", s1.selectedId === "scene4" && s1.commitId === commitBefore, `commit ${commitBefore} -> ${s1.commitId}`);
  check("S1 trace reflects selection", (await text('[data-role="trace-body"]'))?.includes("scene4"));

  // S2: direct manipulation opens a preview, not a commit (REQ-070).
  await page.click('[data-action="connect"]');
  const s2 = await snap();
  check("S2 preview opens on connect", await exists("nw-proposal-preview"));
  check("S2 commit unchanged by gesture", s2.commitId === commitBefore, `commit ${s2.commitId}`);
  await page.screenshot({ path: join(SHOT_DIR, "04-proposal-review.png") });

  // S3: acceptance is distinct from commit (REQ-076).
  await page.click('[data-action="accept"]');
  const s3a = await snap();
  check("S3 accept does not commit", s3a.proposalState === "accepted" && s3a.commitId === commitBefore);
  await page.click('[data-action="commit"]');
  const s3b = await snap();
  check("S3 commit changes canonical commit", s3b.commitId !== commitBefore, `commit ${s3b.commitId}`);
  check("S3 dialog closes after commit", !(await exists("nw-proposal-preview")));

  // S9: disabled Commit explains why (REQ-080) -- switch to criticism (approval required).
  await page.evaluate(() => window.NW.setMode("criticism"));
  check("S9 commit disabled in criticism", (await attr('[data-command="commit"]', "aria-disabled")) === "true");
  check("S9 disabled reason visible", (await text('[data-role="commit-reason"]'))?.includes("authority"));

  // S4: source span is immutable in Criticism Parlor (REQ-051).
  check("S4 source read-only text", (await text('[data-role="source-readonly"]')) === "Fingerprint source edition cannot be edited");
  check("S4 source aria-readonly", (await attr('[data-role="source-readonly"]', "aria-readonly")) === "true");

  // S5: broken anchor blocks publication (REQ-057).
  check("S5 broken-anchor badge", await page.evaluate(() => document.querySelector('nw-evidence-span [data-role="badge-text"]')?.textContent === "Broken anchor"));
  check("S5 publication blocked", (await snap()).publicationStatus === "blocked");
  check("S5 realign action present", await exists('[data-action="realign"]'));

  // S7: color-independent lifecycle badge (REQ color-independence).
  check("S7 machine-proposal text present", await page.evaluate(() => [...document.querySelectorAll('[data-role="badge-text"]')].some((b) => b.textContent === "Machine proposal")));
  await page.screenshot({ path: join(SHOT_DIR, "02-criticism.png") });

  // S6: partial job output is never shown committed (REQ-112).
  await page.evaluate(() => window.NW.setMode("composition"));
  check("S6 job shows Partial", (await text('[data-role="job-state-text"]'))?.includes("Partial"));
  check("S6 partial has no Accepted badge", await page.evaluate(() => !document.querySelector('[data-role="job-status"] nw-badge[data-kind="accepted"]')));

  // Screen 4: Counterfactual Laboratory + reader-model label.
  await page.evaluate(() => window.NW.setMode("counterfactual"));
  check("S-CF reader model labeled Intended", await page.evaluate(() => {
    const row = document.querySelector('tr[data-dimension="Reader model"] [data-role="hypotheses"]');
    return row && row.textContent.includes("Intended response");
  }));
  check("S-CF matrix has seven dimensions", await page.evaluate(() => document.querySelectorAll("nw-comparison-matrix tbody tr").length === 7));
  await page.screenshot({ path: join(SHOT_DIR, "03-counterfactual.png") });

  // S11: override requires a reason (CMP-16).
  await page.evaluate(() => window.NW.openConflict());
  await page.click('[data-action="override"]');
  check("S11 override needs reason", (await text('[data-role="conflict-reason-error"]')) === "Reason is required" && (await exists("nw-conflict-resolver")));

  // S8: narrow layout keeps context and selection (REQ-152).
  await page.evaluate(() => window.NW.setMode("composition"));
  await page.evaluate(() => window.NW.selectNode("scene4"));
  await page.setViewportSize({ width: 390, height: 800 });
  await page.waitForTimeout(50);
  check("S8 region tabs visible when narrow", await page.evaluate(() => getComputedStyle(document.querySelector("nw-region-tabs")).display !== "none"));
  check("S8 context labels retained", (await text('[data-role="commit-label"]'))?.startsWith("Commit:"));
  check("S8 selection retained when narrow", (await snap()).selectedId === "scene4");
  await page.screenshot({ path: join(SHOT_DIR, "05-narrow.png") });

  await browser.close();
  server.close();

  const failed = results.filter((r) => !r.ok);
  console.log(`\n${results.length - failed.length}/${results.length} scenario checks passed. Screenshots in ${SHOT_DIR}`);
  if (failed.length) process.exit(1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
