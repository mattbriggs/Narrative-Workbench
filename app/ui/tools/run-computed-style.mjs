// run-computed-style.mjs  (spec SS10 verification check 2)
// At wide, medium, and narrow reference sizes, reads the COMPUTED styles of
// every property named in each component record (CMP-01..18) and key component
// states, and asserts they equal the token-derived expected values. Expected
// values are read from the DTCG-generated CSS variables in-page, so the suite
// verifies that components actually resolve to the token values (CLAUDE.md C-2)
// rather than to any hardcoded number. Exits non-zero on any mismatch.
//
// Reference sizes (spec SS5): wide 1440x900, medium 1024x768, narrow 390x800.
// Box/colour properties are viewport-invariant and asserted at the wide
// reference; the responsive layout tracks are asserted at all three sizes.

import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { join, extname, resolve } from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const UI_ROOT = resolve(new URL("../", import.meta.url).pathname);
const MIME = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css", ".json": "application/json" };

function startServer() {
  const server = createServer(async (req, res) => {
    try {
      const rel = decodeURIComponent(req.url.split("?")[0]);
      const file = join(UI_ROOT, rel === "/" ? "/index.html" : rel);
      if (!file.startsWith(UI_ROOT)) return res.writeHead(403).end("no");
      res.writeHead(200, { "content-type": (MIME[extname(file)] || "application/octet-stream") + "; charset=utf-8" }).end(await readFile(file));
    } catch {
      res.writeHead(404).end("no");
    }
  });
  return new Promise((r) => server.listen(0, () => r(server)));
}

// The component-record property checklist, evaluated in the browser. Each entry
// names a selector, the setup mode, and property checks. A check is:
//   { prop, dim:"--token" } compares getComputedStyle[prop] to the token px/px-value
//   { prop, color:"--token" } compares a colour to the token colour (via a probe)
//   { prop, exact:"value" } compares to an exact keyword
function browserChecklist() {
  const NW = window.NW;
  const root = document.documentElement;
  const failures = [];

  const dimOf = (v) => getComputedStyle(root).getPropertyValue(v).trim();
  const colorOf = (v) => {
    const s = document.createElement("span");
    s.style.color = `var(${v})`;
    document.body.appendChild(s);
    const c = getComputedStyle(s).color;
    s.remove();
    return c;
  };
  const cs = (sel) => {
    const el = document.querySelector(sel);
    return el ? getComputedStyle(el) : null;
  };

  function assert(label, sel, checks) {
    const style = cs(sel);
    if (!style) {
      failures.push(`${label}: selector ${sel} not found`);
      return;
    }
    for (const c of checks) {
      const actual = style[c.prop];
      let expected;
      if ("dim" in c) expected = dimOf(c.dim);
      else if ("color" in c) expected = colorOf(c.color);
      else expected = c.exact;
      if (actual !== expected) failures.push(`${label} ${sel} ${c.prop}: expected ${expected} got ${actual}`);
    }
  }

  // ---- Composition-mode components ----
  NW.setMode("composition");
  NW.selectNode("scene4"); // materialize a selected navigator row

  assert("CMP-01 shell", "nw-shell", [{ prop: "display", exact: "grid" }]);
  assert("CMP-02 global-bar", "nw-global-bar", [
    { prop: "display", exact: "flex" },
    { prop: "height", dim: "--dimension-role-global-bar-height" },
    { prop: "paddingLeft", dim: "--dimension-role-space-region" },
    { prop: "paddingRight", dim: "--dimension-role-space-region" },
    { prop: "columnGap", dim: "--dimension-role-space-stack" },
    { prop: "alignItems", exact: "center" },
    { prop: "backgroundColor", color: "--color-role-surface-strong" },
    { prop: "color", color: "--color-role-text-on-strong" },
  ]);
  assert("CMP-03 command-bar", "nw-command-bar", [
    { prop: "display", exact: "flex" },
    { prop: "height", dim: "--dimension-role-command-bar-height" },
    { prop: "paddingLeft", dim: "--dimension-role-space-stack" },
    { prop: "columnGap", dim: "--dimension-role-space-tight" },
    { prop: "borderBottomWidth", dim: "--dimension-role-separator-width" },
    { prop: "borderBottomColor", color: "--color-role-border-default" },
  ]);
  assert("CMP-04 navigator", "nw-navigator", [
    { prop: "display", exact: "flex" },
    { prop: "flexDirection", exact: "column" },
    { prop: "overflowY", exact: "auto" },
    { prop: "borderRightWidth", dim: "--dimension-role-separator-width" },
    { prop: "borderRightColor", color: "--color-role-border-default" },
    { prop: "paddingTop", dim: "--dimension-role-space-stack" },
  ]);
  assert("CMP-04 selected row", 'nw-navigator [role="treeitem"][aria-selected="true"]', [
    { prop: "backgroundColor", color: "--color-role-surface-selection" },
    { prop: "color", color: "--color-role-text-primary" },
    { prop: "borderRadius", dim: "--radius-role-control" },
  ]);
  assert("CMP-05 primary", "nw-primary", [
    { prop: "overflowY", exact: "auto" },
    { prop: "paddingTop", dim: "--dimension-role-space-region" },
  ]);
  assert("CMP-06 inspector", "nw-inspector", [
    { prop: "overflowY", exact: "auto" },
    { prop: "paddingTop", dim: "--dimension-role-space-stack" },
    { prop: "borderLeftWidth", dim: "--dimension-role-separator-width" },
    { prop: "borderLeftColor", color: "--color-role-border-default" },
  ]);
  assert("CMP-07 trace-drawer", "nw-trace-drawer", [
    { prop: "borderTopWidth", dim: "--dimension-role-separator-width" },
    { prop: "borderTopColor", color: "--color-role-border-strong" },
    { prop: "height", dim: "--dimension-role-trace-default" },
    { prop: "minHeight", dim: "--dimension-role-trace-min" },
    { prop: "paddingTop", dim: "--dimension-role-space-stack" },
  ]);
  assert("CMP-10 object-card", "nw-canvas .object-card", [
    { prop: "minWidth", dim: "--dimension-role-card-min-width" },
    { prop: "paddingTop", dim: "--dimension-role-space-stack" },
    { prop: "borderTopWidth", dim: "--dimension-role-separator-width" },
    { prop: "borderTopColor", color: "--color-role-border-default" },
    { prop: "borderTopLeftRadius", dim: "--radius-role-control" },
  ]);
  assert("CMP-11 candidate-tray", "nw-candidate-tray", [
    { prop: "display", exact: "flex" },
    { prop: "flexDirection", exact: "column" },
    { prop: "rowGap", dim: "--dimension-role-space-inline" },
  ]);
  // Candidate selected state.
  NW.app.selectCandidate("cand-A");
  assert("CMP-11 option selected", 'nw-candidate-tray [role="option"][aria-selected="true"]', [
    { prop: "backgroundColor", color: "--color-role-surface-selection" },
    { prop: "paddingTop", dim: "--dimension-role-space-stack" },
  ]);

  // ---- Criticism-mode components ----
  NW.setMode("criticism");
  assert("CMP-12 evidence-span", "nw-evidence-span", [
    { prop: "display", exact: "block" },
    { prop: "paddingTop", dim: "--dimension-role-space-stack" },
    { prop: "borderTopWidth", dim: "--dimension-role-separator-width" },
    { prop: "borderTopColor", color: "--color-role-border-default" },
    { prop: "borderTopLeftRadius", dim: "--radius-role-control" },
  ]);
  assert("CMP-13 assertion-card", "nw-assertion-card", [
    { prop: "display", exact: "block" },
    { prop: "paddingTop", dim: "--dimension-role-space-stack" },
    { prop: "borderInlineStartWidth", dim: "--dimension-role-space-tight" },
    { prop: "borderInlineStartColor", color: "--color-role-border-strong" },
  ]);
  assert("CMP-08 badge machine", 'nw-badge[data-kind="machine"]', [
    { prop: "display", exact: "inline-flex" },
    { prop: "minHeight", dim: "--dimension-role-badge-min-height" },
    { prop: "paddingTop", dim: "--dimension-role-focus-offset" },
    { prop: "paddingLeft", dim: "--dimension-role-space-inline" },
    { prop: "columnGap", dim: "--dimension-role-space-tight" },
    { prop: "borderTopLeftRadius", dim: "--radius-role-control" },
    { prop: "backgroundColor", color: "--color-role-status-machine-fill" },
    { prop: "color", color: "--color-role-status-machine-text" },
  ]);
  assert("CMP-08 badge broken", 'nw-badge[data-kind="broken"]', [
    { prop: "backgroundColor", color: "--color-role-status-warning-fill" },
    { prop: "color", color: "--color-role-status-warning-text" },
  ]);
  // Disabled Commit command shows the muted (not-colour-only) state.
  assert("CMP-03 disabled command", 'nw-command-bar button[aria-disabled="true"]', [
    { prop: "color", color: "--color-role-text-muted" },
  ]);

  // ---- Counterfactual matrix ----
  NW.setMode("counterfactual");
  assert("CMP-14 matrix table", "nw-comparison-matrix table", [
    { prop: "borderCollapse", exact: "collapse" },
  ]);
  // The table fills its container (spec "width:100%"); assert by measurement,
  // not against a token (100% is not a token value).
  {
    const table = document.querySelector("nw-comparison-matrix table");
    const host = document.querySelector("nw-comparison-matrix");
    if (table && host && Math.abs(table.getBoundingClientRect().width - host.getBoundingClientRect().width) > 1) {
      failures.push(`CMP-14 matrix table does not fill its container: ${table.getBoundingClientRect().width} vs ${host.getBoundingClientRect().width}`);
    }
  }
  assert("CMP-14 matrix cell", "nw-comparison-matrix td", [
    { prop: "paddingTop", dim: "--dimension-role-space-inline" },
    { prop: "paddingLeft", dim: "--dimension-role-space-stack" },
    { prop: "borderTopWidth", dim: "--dimension-role-separator-width" },
  ]);

  // ---- Proposal preview dialog (CMP-09) ----
  NW.setMode("composition");
  NW.connectObjects();
  assert("CMP-09 dialog", "nw-proposal-preview .modal-dialog", [
    { prop: "paddingTop", dim: "--dimension-role-space-loose" },
    { prop: "borderTopWidth", dim: "--dimension-role-separator-width" },
    { prop: "borderTopColor", color: "--color-role-border-strong" },
    { prop: "borderTopLeftRadius", dim: "--radius-role-panel" },
    { prop: "insetBlockStart", dim: "--dimension-role-dialog-inset" },
  ]);
  NW.app.cancelProposal();

  // ---- Conflict resolver (CMP-16) ----
  NW.openConflict();
  assert("CMP-16 dialog", "nw-conflict-resolver .modal-dialog", [
    { prop: "paddingTop", dim: "--dimension-role-space-loose" },
    { prop: "borderTopLeftRadius", dim: "--radius-role-panel" },
  ]);
  NW.app.resolveConflict("a reason");

  // ---- Pane message (CMP-18) geometry via a probe instance ----
  const pm = document.createElement("nw-pane-message");
  document.querySelector("nw-primary").appendChild(pm);
  assert("CMP-18 pane-message", "nw-pane-message", [
    { prop: "maxWidth", dim: "--dimension-role-pane-message-max" },
    { prop: "marginTop", dim: "--dimension-role-space-xloose" },
    { prop: "paddingTop", dim: "--dimension-role-space-region" },
  ]);
  pm.remove();

  return failures;
}

// Layout-track checks per viewport (the responsive-varying properties).
function browserLayout(viewport) {
  const NW = window.NW;
  const failures = [];
  const root = document.documentElement;
  const dimOf = (v) => getComputedStyle(root).getPropertyValue(v).trim();
  const colorOf = (v) => {
    const s = document.createElement("span");
    s.style.color = `var(${v})`;
    document.body.appendChild(s);
    const c = getComputedStyle(s).color;
    s.remove();
    return c;
  };
  const shell = document.querySelector("nw-shell");
  const wa = document.querySelector("nw-shell .work-area");
  const tabsDisplay = getComputedStyle(document.querySelector("nw-region-tabs")).display;
  const cols = getComputedStyle(wa).gridTemplateColumns.split(" ");
  const rows = getComputedStyle(shell).gridTemplateRows.split(" ");

  if (!rows.slice(0, 2).join(" ").startsWith(dimOf("--dimension-role-global-bar-height")))
    failures.push(`${viewport} shell rows start: ${rows.slice(0, 2).join(" ")}`);

  if (viewport === "wide") {
    if (shell.dataset.viewport !== "wide") failures.push(`wide: data-viewport=${shell.dataset.viewport}`);
    if (cols.length !== 3) failures.push(`wide: expected 3 work-area columns, got ${cols.length}`);
    if (cols[0] !== dimOf("--dimension-role-navigator-wide")) failures.push(`wide: navigator track ${cols[0]}`);
    if (cols[2] !== dimOf("--dimension-role-inspector-wide")) failures.push(`wide: inspector track ${cols[2]}`);
    if (tabsDisplay !== "none") failures.push(`wide: region tabs should be hidden, got ${tabsDisplay}`);
  } else if (viewport === "medium") {
    if (shell.dataset.viewport !== "medium") failures.push(`medium: data-viewport=${shell.dataset.viewport}`);
    if (cols.length !== 2) failures.push(`medium: expected 2 work-area columns, got ${cols.length}`);
    if (cols[0] !== dimOf("--dimension-role-navigator-wide")) failures.push(`medium: navigator track ${cols[0]}`);
    if (tabsDisplay !== "none") failures.push(`medium: region tabs should be hidden, got ${tabsDisplay}`);
  } else {
    if (shell.dataset.viewport !== "narrow") failures.push(`narrow: data-viewport=${shell.dataset.viewport}`);
    if (cols.length !== 1) failures.push(`narrow: expected 1 work-area column, got ${cols.length}`);
    if (tabsDisplay === "none") failures.push(`narrow: region tabs should be visible`);
    // Active narrow tab uses strong selection, not a tint.
    const activeTab = document.querySelector('nw-region-tabs [role="tab"][aria-selected="true"]');
    const bg = getComputedStyle(activeTab).backgroundColor;
    if (bg !== colorOf("--color-role-surface-strong")) failures.push(`narrow: active tab bg ${bg}`);
  }
  return failures;
}

async function main() {
  const server = await startServer();
  const { port } = server.address();
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(`http://127.0.0.1:${port}/`);
  await page.waitForFunction(() => window.NW !== undefined);

  const all = [];

  const compFailures = await page.evaluate(browserChecklist);
  compFailures.forEach((f) => all.push(f));
  console.log(`Component-record checks: ${compFailures.length === 0 ? "all PASS" : compFailures.length + " FAIL"}`);

  for (const [name, w, h] of [["wide", 1440, 900], ["medium", 1024, 768], ["narrow", 390, 800]]) {
    await page.setViewportSize({ width: w, height: h });
    await page.waitForTimeout(40);
    // Re-render so narrow active-region/data-active is applied after resize.
    await page.evaluate(() => window.NW.app.render());
    const layoutFailures = await page.evaluate(browserLayout, name);
    layoutFailures.forEach((f) => all.push(f));
    console.log(`Layout checks @ ${name} (${w}x${h}): ${layoutFailures.length === 0 ? "all PASS" : layoutFailures.length + " FAIL"}`);
  }

  await browser.close();
  server.close();

  if (all.length) {
    console.log(`\nComputed-style suite FAILED with ${all.length} mismatch(es):`);
    all.forEach((f) => console.log("  - " + f));
    process.exit(1);
  }
  console.log("\nComputed-style suite PASSED: every checked property matches its token value at wide, medium, and narrow.");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
