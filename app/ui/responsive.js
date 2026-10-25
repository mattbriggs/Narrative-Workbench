// responsive.js
// Drives the responsive layout without literal px in media queries. Breakpoints
// come from the DTCG token file (read from CSS variables), keeping the token
// file the single source of visual values (CLAUDE.md C-2). The controller sets
// `data-viewport` = wide | medium | narrow on the shell (spec SS5, CMP-17).

/** Read a px-valued CSS custom property from :root as an integer. */
function readPx(name) {
  const raw = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return parseInt(raw, 10);
}

/** Classify a viewport width against the token breakpoints. */
export function classify(width, bpMedium, bpWide) {
  if (width < bpMedium) return "narrow";
  if (width < bpWide) return "medium";
  return "wide";
}

/** Apply the current viewport class to the shell; returns the class applied. */
export function applyViewport(shell, width = window.innerWidth) {
  const bpMedium = readPx("--dimension-role-bp-medium");
  const bpWide = readPx("--dimension-role-bp-wide");
  const cls = classify(width, bpMedium, bpWide);
  shell.dataset.viewport = cls;
  return cls;
}

/** Install a resize listener that keeps the viewport class current. */
export function installResponsive(shell) {
  applyViewport(shell);
  window.addEventListener("resize", () => applyViewport(shell));
}
