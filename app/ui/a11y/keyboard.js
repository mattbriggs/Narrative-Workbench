// keyboard.js
// Global keyboard model (spec SS7, Table 28). F6 / Shift+F6 cycle regions in the
// order global bar, navigator, primary, inspector, trace drawer (SRS REQ-006);
// Ctrl/Cmd+J toggles the trace drawer and restores focus on close (CMP-07);
// Escape closes the topmost non-committed dialog/drawer and restores focus.

/** The region focus order (SRS REQ-006). */
export const REGION_ORDER = ["nw-global-bar", "nw-navigator", "nw-primary", "nw-inspector", "nw-trace-drawer"];

/**
 * Install the global keyboard model on a shell.
 * @param {HTMLElement} shell
 * @param {{toggleDrawer:Function, closeTop:Function}} actions
 */
export function installKeyboard(shell, actions) {
  let regionIndex = 0;

  function focusRegion(index) {
    const tag = REGION_ORDER[index];
    const el = shell.querySelector(tag);
    if (el) {
      if (!el.hasAttribute("tabindex")) el.setAttribute("tabindex", "-1");
      el.focus();
    }
  }

  shell.addEventListener("keydown", (event) => {
    const meta = event.ctrlKey || event.metaKey;
    if (event.key === "F6") {
      event.preventDefault();
      const step = event.shiftKey ? -1 : 1;
      regionIndex = (regionIndex + step + REGION_ORDER.length) % REGION_ORDER.length;
      focusRegion(regionIndex);
    } else if (meta && (event.key === "j" || event.key === "J")) {
      event.preventDefault();
      actions.toggleDrawer();
    } else if (event.key === "Escape") {
      actions.closeTop();
    }
  });
}
