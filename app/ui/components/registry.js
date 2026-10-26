// registry.js
// Defines the 18 shared components CMP-01..CMP-18 as custom elements, each with
// its ARIA/native role and stable component id (spec SS6). Screens compose these
// tags; they must not redefine a component's role, states, or keyboard contract.
// Visual styling lives entirely in components.css via role tokens.

/** Define a custom element that sets a role and a data-cmp id on connect. */
function defineComponent(tag, cmpId, { role, ariaLabel } = {}) {
  if (customElements.get(tag)) return;
  class Component extends HTMLElement {
    connectedCallback() {
      this.dataset.cmp = cmpId;
      if (role && !this.hasAttribute("role")) this.setAttribute("role", role);
      if (ariaLabel && !this.hasAttribute("aria-label")) this.setAttribute("aria-label", ariaLabel);
    }
  }
  customElements.define(tag, Component);
}

/** Register every component. Idempotent. */
export function registerComponents() {
  defineComponent("nw-shell", "CMP-01", { role: "application", ariaLabel: "Narrative Workbench" });
  defineComponent("nw-global-bar", "CMP-02", { role: "banner" });
  defineComponent("nw-command-bar", "CMP-03", { role: "toolbar", ariaLabel: "Workbench commands" });
  defineComponent("nw-navigator", "CMP-04", { role: "navigation", ariaLabel: "Navigator" });
  defineComponent("nw-primary", "CMP-05", { role: "main" });
  defineComponent("nw-inspector", "CMP-06", { role: "complementary", ariaLabel: "Inspector" });
  defineComponent("nw-trace-drawer", "CMP-07", { role: "region", ariaLabel: "Trace and validation" });
  defineComponent("nw-badge", "CMP-08", {});
  defineComponent("nw-proposal-preview", "CMP-09", { role: "dialog", ariaLabel: "Review proposed change" });
  defineComponent("nw-canvas", "CMP-10", { role: "group", ariaLabel: "Narrative objects" });
  defineComponent("nw-candidate-tray", "CMP-11", { role: "listbox", ariaLabel: "Candidate trajectories" });
  defineComponent("nw-evidence-span", "CMP-12", { role: "article" });
  defineComponent("nw-assertion-card", "CMP-13", { role: "article" });
  defineComponent("nw-comparison-matrix", "CMP-14", { role: "region", ariaLabel: "Comparison matrix" });
  defineComponent("nw-job-status", "CMP-15", { role: "status" });
  defineComponent("nw-conflict-resolver", "CMP-16", { role: "dialog", ariaLabel: "Resolve semantic conflict" });
  defineComponent("nw-region-tabs", "CMP-17", { role: "tablist", ariaLabel: "Regions" });
  defineComponent("nw-pane-message", "CMP-18", {});
}
