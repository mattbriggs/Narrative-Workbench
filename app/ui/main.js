// main.js
// Bootstraps the Narrative Workbench shell: registers components, builds the
// five screens over one synchronized shell, wires the statecharts/store, and
// enforces the global invariants (selection never mutates the commit; direct
// manipulation opens a proposal preview; acceptance is distinct from commit).
// Exposes `window.NW` so the headless scenario harness can drive and inspect it.

import { registerComponents } from "./components/registry.js";
import { Store, initialState } from "./state/store.mjs";
import { ProposalState, step as proposalStep } from "./statecharts/proposal.mjs";
import { JobState } from "./statecharts/job.mjs";
import { installResponsive } from "./responsive.js";
import { installKeyboard } from "./a11y/keyboard.js";
import { DEMO } from "./screens/demo-data.js";
import {
  renderGlobalBar,
  renderCommandBar,
  renderNavigator,
  renderPrimary,
  renderInspector,
  renderTraceDrawer,
  renderRegionTabs,
  renderProposalPreview,
  renderConflictResolver,
} from "./screens/screens.js";

/** The application controller. One instance owns the shell. */
class App {
  constructor(shell) {
    this.shell = shell;
    this.store = new Store({ ...initialState(), workId: "work-1", branchId: "main", commitId: "c42" });
    this.mode = "composition";
    this.activeRegion = "nw-primary"; // narrow-screen active tab
    this.drawerOpen = true;
    this.lastFocused = null;
    this.data = DEMO;
    this.publicationStatus = DEMO.anchorBroken ? "blocked" : "ready";
    this.conflictOpen = false;
  }

  /** Current observable state plus app-local fields (read by the harness). */
  snapshot() {
    return {
      ...this.store.state,
      mode: this.mode,
      activeRegion: this.activeRegion,
      drawerOpen: this.drawerOpen,
      publicationStatus: this.publicationStatus,
      conflictOpen: this.conflictOpen,
    };
  }

  /** The actor's authority for committing canonical state (drives CMP-03). */
  get commitAuthority() {
    return this.mode === "composition" ? "allowed" : "approvalRequired";
  }

  render() {
    const s = this.snapshot();
    this.shell.innerHTML = "";

    const globalBar = renderGlobalBar(s);
    const commandBar = renderCommandBar(s, this.commitAuthority, (cmd) => this.onCommand(cmd));
    const workArea = document.createElement("div");
    workArea.className = "work-area";

    const navigator = renderNavigator(s, this.data, (id) => this.selectNode(id));
    const primary = renderPrimary(s, this.data, {
      onConnect: () => this.connectObjects(),
      onSelectCandidate: (id) => this.selectCandidate(id),
      onRealign: () => this.realignAnchor(),
    });
    const inspector = renderInspector(s, this.data);
    navigator.classList.add("region");
    primary.classList.add("region");
    inspector.classList.add("region");
    this.applyActiveRegion(navigator, primary, inspector);
    workArea.append(navigator, primary, inspector);

    const drawer = renderTraceDrawer(s, this.drawerOpen);
    const tabs = renderRegionTabs(s, this.activeRegion, (region) => this.activateRegion(region));

    this.shell.append(globalBar, commandBar, workArea, drawer, tabs);

    if (s.proposalState === ProposalState.DRAFT || s.proposalState === ProposalState.AWAITING_APPROVAL || s.proposalState === ProposalState.ACCEPTED) {
      this.shell.append(
        renderProposalPreview(s, {
          onAccept: () => this.acceptProposal(),
          onCommit: () => this.commitProposal(),
          onCancel: () => this.cancelProposal(),
        })
      );
    }
    if (this.conflictOpen) {
      this.shell.append(renderConflictResolver((reason) => this.resolveConflict(reason)));
    }
  }

  applyActiveRegion(navigator, primary, inspector) {
    const narrow = this.shell.dataset.viewport === "narrow";
    for (const [tag, el] of [["nw-navigator", navigator], ["nw-primary", primary], ["nw-inspector", inspector]]) {
      el.dataset.active = String(!narrow || this.activeRegion === tag);
    }
  }

  // -- interactions ------------------------------------------------------

  setMode(mode) {
    this.mode = mode;
    this.render();
  }

  selectNode(id) {
    this.store.select(id); // never changes commitId (enforced in the store)
    this.render();
  }

  selectCandidate(id) {
    this.store._patch({ selectedId: id });
    this.render();
  }

  connectObjects() {
    // Direct manipulation creates a draft proposal and opens the preview;
    // canonical commit is unchanged (SRS REQ-070, scenario "direct manipulation").
    const r = proposalStep(ProposalState.NONE, { type: "mutatingGesture" });
    this.store.setProposalState(r.state);
    this.lastFocused = document.activeElement;
    this.render();
    this._advanceToApproval();
  }

  _advanceToApproval() {
    // Submit -> validate -> awaiting approval (schema complete, may propose).
    let st = this.store.state.proposalState;
    st = proposalStep(st, { type: "submit", schemaComplete: true, mayPropose: true }).state;
    st = proposalStep(st, { type: "contextResolved" }).state;
    st = proposalStep(st, { type: "hardChecksPass" }).state;
    this.store.setProposalState(st);
    this.render();
    this.focusDialogHeading();
  }

  acceptProposal() {
    const r = proposalStep(this.store.state.proposalState, { type: "approve", authorized: this.commitAuthority !== "denied" });
    if (r.ok) {
      this.store.setProposalState(r.state); // accepted: commit still unchanged
    }
    this.render();
  }

  commitProposal() {
    const r = proposalStep(this.store.state.proposalState, { type: "commit", parentUnchanged: true });
    if (r.ok) {
      const next = "c" + (parseInt(this.store.state.commitId.slice(1), 10) + 1);
      this.store._patch({ proposalState: ProposalState.COMMITTED, commitId: next });
      this.restoreFocus();
      // Reset lifecycle for the next gesture.
      this.store.setProposalState(ProposalState.NONE);
    }
    this.render();
  }

  cancelProposal() {
    this.store.setProposalState(ProposalState.NONE);
    this.restoreFocus();
    this.render();
  }

  onCommand(cmd) {
    if (cmd === "commit") {
      if (this.commitAuthority === "allowed") this.connectObjects();
    } else if (cmd === "compare") {
      this.setMode("counterfactual");
    }
  }

  realignAnchor() {
    this.publicationStatus = "ready";
    this.data = { ...this.data, anchorBroken: false };
    this.render();
  }

  openConflict() {
    this.conflictOpen = true;
    this.render();
  }

  resolveConflict(reason) {
    if (!reason || !reason.trim()) {
      const msg = this.shell.querySelector('[data-role="conflict-reason-error"]');
      if (msg) msg.textContent = "Reason is required";
      return false;
    }
    this.conflictOpen = false;
    this.render();
    return true;
  }

  toggleDrawer() {
    this.drawerOpen = !this.drawerOpen;
    this.render();
    if (!this.drawerOpen) this.restoreFocus();
  }

  closeTop() {
    if (this.conflictOpen) {
      this.conflictOpen = false;
      this.render();
      return;
    }
    const st = this.store.state.proposalState;
    if (st === ProposalState.DRAFT || st === ProposalState.AWAITING_APPROVAL) {
      this.cancelProposal();
      return;
    }
    if (this.drawerOpen) this.toggleDrawer();
  }

  activateRegion(region) {
    this.activeRegion = region; // narrow tab switch; selection/commit retained
    this.render();
  }

  focusDialogHeading() {
    const heading = this.shell.querySelector('[data-role="dialog-heading"]');
    if (heading) {
      heading.setAttribute("tabindex", "-1");
      heading.focus();
    }
  }

  restoreFocus() {
    if (this.lastFocused && document.contains(this.lastFocused)) this.lastFocused.focus();
  }
}

function boot() {
  registerComponents();
  const shell = document.getElementById("shell");
  const app = new App(shell);
  installResponsive(shell);
  installKeyboard(shell, { toggleDrawer: () => app.toggleDrawer(), closeTop: () => app.closeTop() });
  app.render();
  window.NW = {
    app,
    store: app.store,
    snapshot: () => app.snapshot(),
    setMode: (m) => app.setMode(m),
    selectNode: (id) => app.selectNode(id),
    connectObjects: () => app.connectObjects(),
    openConflict: () => app.openConflict(),
  };
}

if (typeof document !== "undefined") {
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
}
