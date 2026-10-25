// screens.js
// Render functions composing the shared components into the five screens
// (spec SS8): Shell, Composition Studio, Criticism Parlor, Counterfactual
// Laboratory, and the Proposal Review overlay. No literal visual values here;
// all styling is in components.css via role tokens. `data-role` attributes are
// stable hooks for the scenario harness.

import { ProposalState } from "../statecharts/proposal.mjs";

/** Minimal DOM helper: el(tag, props, children). */
function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === "text") node.textContent = v;
    else if (k === "html") node.innerHTML = v;
    else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2).toLowerCase(), v);
    else if (v !== null && v !== undefined) node.setAttribute(k, v);
  }
  for (const c of [].concat(children)) if (c) node.append(c);
  return node;
}

/** CMP-08 provenance/lifecycle badge: text + optional icon, never color alone. */
function badge(kind, label) {
  return el("nw-badge", { "data-kind": kind, "aria-label": label }, [
    el("span", { "aria-hidden": "true", text: "● " }),
    el("span", { "data-role": "badge-text", text: label }),
  ]);
}

export function renderGlobalBar(s) {
  return el("nw-global-bar", {}, [
    el("span", { class: "title", text: "Narrative Workbench" }),
    el("span", { class: "context", "data-role": "mode-label", text: `Mode: ${s.mode}` }),
    el("span", { class: "context", "data-role": "work-label", text: `Work: ${s.workId}` }),
    el("span", { class: "context", "data-role": "branch-label", text: `Branch: ${s.branchId}` }),
    el("span", { class: "context", "data-role": "commit-label", text: `Commit: ${s.commitId}` }),
    el("span", { class: "context", "data-role": "sync-label", text: `Sync: ${s.syncState}` }),
  ]);
}

export function renderCommandBar(s, authority, onCommand) {
  const commands = ["Work", "Branch", "Commit", "Undo", "Redo", "Run", "Compare", "Export", "Share"];
  const bar = el("nw-command-bar", {});
  for (const label of commands) {
    const key = label.toLowerCase();
    const disabled = label === "Commit" && authority !== "allowed";
    const btn = el("button", {
      type: "button",
      "data-command": key,
      ...(disabled ? { "aria-disabled": "true" } : {}),
      text: label,
      onclick: () => !disabled && onCommand(key),
    });
    bar.append(btn);
    if (disabled) {
      bar.append(el("span", { class: "reason", "data-role": "commit-reason", text: "Commit requires narrative designer authority" }));
    }
  }
  return bar;
}

export function renderNavigator(s, data, onSelect) {
  const nav = el("nw-navigator", {});
  const tree = el("div", { role: "tree", "aria-label": "Units, threads, evidence" });
  for (const node of data.navigator) {
    tree.append(
      el("div", {
        role: "treeitem",
        tabindex: "0",
        "data-id": node.id,
        "aria-selected": String(s.selectedId === node.id),
        text: node.label,
        onclick: () => onSelect(node.id),
        onkeydown: (e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onSelect(node.id);
          }
        },
      })
    );
  }
  nav.append(tree);
  return nav;
}

export function renderPrimary(s, data, handlers) {
  const primary = el("nw-primary", {}, [
    el("h2", { "data-role": "primary-title", text: primaryTitle(s.mode) }),
    el("p", { "data-role": "projection-label", text: `Showing commit ${s.commitId} (projection ${s.projectionVersion ?? "n/a"})` }),
  ]);
  if (s.mode === "composition") primary.append(compositionCanvas(data, handlers, s.selectedId));
  else if (s.mode === "criticism") primary.append(criticismCanvas(s, data, handlers));
  else if (s.mode === "counterfactual") primary.append(comparisonMatrix(data));
  primary.append(jobStatus(data.job));
  return primary;
}

function primaryTitle(mode) {
  return { composition: "Composition Studio", criticism: "Criticism Parlor", counterfactual: "Counterfactual Laboratory" }[mode];
}

function compositionCanvas(data, handlers, selectedId) {
  const canvas = el("nw-canvas", {});
  const list = el("div", { role: "list", "aria-label": "Narrative objects" });
  for (const obj of data.objects) {
    list.append(
      el("div", { class: "object-card", role: "listitem", "data-id": obj.id }, [
        el("div", { class: "object-kind", text: `${obj.kind} - mass ${obj.mass}` }),
        el("div", { text: obj.label }),
      ])
    );
  }
  canvas.append(list);
  canvas.append(el("button", { type: "button", "data-action": "connect", text: "Connect objects", onclick: () => handlers.onConnect() }));

  const tray = el("nw-candidate-tray", {});
  for (const cand of data.candidates) {
    tray.append(
      el("div", { role: "option", "data-id": cand.id, "aria-selected": String(selectedId === cand.id), onclick: () => handlers.onSelectCandidate(cand.id) }, [
        el("div", { text: cand.label }),
        el("div", { class: "object-kind", text: cand.changed }),
      ])
    );
  }
  canvas.append(tray);
  return canvas;
}

function criticismCanvas(s, data, handlers) {
  const wrap = el("div", {});
  const ev = el("nw-evidence-span", { "data-role": "evidence-span" }, [
    el("div", { class: "source-text", text: data.evidence.text }),
    el("div", { class: "anchor-id", text: `${data.evidence.editionId} ${data.evidence.region} ${data.evidence.fingerprint}` }),
  ]);
  if (data.anchorBroken) {
    ev.append(badge("broken", "Broken anchor"));
    ev.append(el("button", { type: "button", "data-action": "realign", text: "Realign anchor", onclick: () => handlers.onRealign() }));
  }
  wrap.append(ev);

  const card = el("nw-assertion-card", { "data-role": "assertion-card" }, [
    el("div", { class: "diff-label", text: "Claim" }),
    el("div", { text: "Delayed disclosure sustains dramatic irony." }),
    badge("machine", "Machine proposal"),
  ]);
  wrap.append(card);
  return wrap;
}

function comparisonMatrix(data) {
  const matrix = el("nw-comparison-matrix", {});
  const table = el("table", { "aria-label": "Counterfactual comparison" });
  const head = el("tr", {}, [
    el("th", { scope: "col", text: "Dimension" }),
    el("th", { scope: "col", text: "Deterministic effects" }),
    el("th", { scope: "col", text: "Generated hypotheses" }),
    el("th", { scope: "col", text: "Invariants" }),
  ]);
  table.append(el("thead", {}, head));
  const body = el("tbody", {});
  for (const row of data.comparison.rows) {
    body.append(
      el("tr", { "data-dimension": row.dimension }, [
        el("th", { scope: "row", text: row.dimension }),
        el("td", { class: "data", "data-role": "deterministic", text: row.deterministic }),
        el("td", { class: "data", "data-role": "hypotheses", text: row.hypotheses }),
        el("td", { class: "data", text: row.invariant }),
      ])
    );
  }
  table.append(body);
  matrix.append(table);
  return matrix;
}

function jobStatus(job) {
  const label = job.state.charAt(0).toUpperCase() + job.state.slice(1);
  const node = el("nw-job-status", { "data-role": "job-status", "aria-live": "polite" }, [
    el("span", { "data-role": "job-state-text", text: `Job: ${label}` }),
  ]);
  // Partial output MUST NOT show an Accepted badge (SRS REQ-112).
  if (job.state === "complete") node.append(badge("accepted", "Accepted"));
  return node;
}

export function renderInspector(s, data) {
  const inspector = el("nw-inspector", {});
  if (s.mode === "criticism") {
    inspector.append(el("div", { class: "field-label", text: "Source" }));
    inspector.append(
      el("div", {
        "data-role": "source-readonly",
        "data-readonly": "true",
        "aria-readonly": "true",
        text: "Fingerprint source edition cannot be edited",
      })
    );
    inspector.append(el("div", { class: "field-label", text: "Lens" }));
    inspector.append(el("div", { text: "Structural narratology" }));
  } else if (s.mode === "counterfactual") {
    inspector.append(el("div", { class: "field-label", text: "Declared intervention" }));
    inspector.append(el("div", { "data-role": "intervention", text: data.comparison.intervention }));
    inspector.append(el("div", { class: "field-label", text: "Preserved variables" }));
    inspector.append(el("div", { text: "World rules; event history before disclosure" }));
  } else {
    for (const [label, value] of [
      ["World truth", "Letter names Actor A as informant"],
      ["Actor belief", "Actor B trusts Actor A"],
      ["Reader expectation", "Alliance is stable"],
    ]) {
      inspector.append(el("div", { class: "field-label", text: label }));
      inspector.append(el("div", { text: value }));
    }
  }
  return inspector;
}

export function renderTraceDrawer(s, open) {
  const drawer = el("nw-trace-drawer", { "data-role": "trace-drawer", "data-open": String(open) });
  drawer.append(
    el("button", {
      type: "button",
      "data-role": "drawer-disclosure",
      "aria-expanded": String(open),
      text: open ? "Hide trace" : "Show trace",
    })
  );
  const tablist = el("div", { role: "tablist", "aria-label": "Trace, validation, jobs, provenance" });
  for (const tab of ["Trace", "Validation", "Jobs", "Provenance"]) {
    tablist.append(el("button", { role: "tab", "aria-selected": String(tab === "Trace"), text: tab }));
  }
  drawer.append(tablist);
  if (open) {
    drawer.append(el("div", { class: "data", "data-role": "trace-body", text: `Before/after for ${s.selectedId ?? "(nothing selected)"}` }));
  }
  return drawer;
}

export function renderRegionTabs(s, active, onActivate) {
  const tabs = el("nw-region-tabs", {});
  for (const [tag, label] of [["nw-navigator", "Navigator"], ["nw-primary", "Work"], ["nw-inspector", "Inspector"], ["nw-trace-drawer", "Trace"]]) {
    tabs.append(
      el("button", {
        role: "tab",
        "data-region": tag,
        "aria-selected": String(active === tag),
        text: label,
        onclick: () => onActivate(tag),
      })
    );
  }
  return tabs;
}

export function renderProposalPreview(s, handlers) {
  const preview = el("nw-proposal-preview", { "aria-modal": "true" });
  preview.append(el("div", { class: "modal-backdrop", "aria-hidden": "true" }));
  const dialog = el("div", { class: "modal-dialog" });
  dialog.append(el("h2", { "data-role": "dialog-heading", text: "Review proposed change" }));
  dialog.append(el("p", { "data-role": "proposal-state", text: `State: ${s.proposalState}` }));
  dialog.append(el("p", { "data-role": "commit-in-dialog", text: `Canonical commit: ${s.commitId}` }));
  dialog.append(
    el("ul", {}, [
      el("li", {}, [el("span", { class: "diff-label", text: "Added: " }), el("span", { text: "typed relation Actor A - Actor B" })]),
      el("li", {}, [el("span", { class: "diff-label", text: "Invariant: " }), el("span", { text: "knowledge check passes" })]),
    ])
  );
  dialog.append(el("p", { text: "Authority: a narrative designer must accept." }));

  const accept = el("button", {
    type: "button",
    "data-action": "accept",
    ...(s.proposalState === ProposalState.AWAITING_APPROVAL ? {} : { "aria-disabled": "true" }),
    text: "Accept",
    onclick: () => s.proposalState === ProposalState.AWAITING_APPROVAL && handlers.onAccept(),
  });
  const commit = el("button", {
    type: "button",
    "data-action": "commit",
    ...(s.proposalState === ProposalState.ACCEPTED ? {} : { "aria-disabled": "true" }),
    text: "Commit",
    onclick: () => s.proposalState === ProposalState.ACCEPTED && handlers.onCommit(),
  });
  const cancel = el("button", { type: "button", "data-action": "cancel", text: "Cancel", onclick: () => handlers.onCancel() });
  dialog.append(accept, commit, cancel);
  preview.append(dialog);
  return preview;
}

export function renderConflictResolver(onOverride) {
  const resolver = el("nw-conflict-resolver", { "aria-modal": "true" });
  resolver.append(el("div", { class: "modal-backdrop", "aria-hidden": "true" }));
  const dialog = el("div", { class: "modal-dialog" });
  dialog.append(el("h2", { "data-role": "conflict-heading", tabindex: "-1", text: "Resolve semantic conflict" }));
  dialog.append(el("p", { text: "Actor B lacks the fact on one branch but acts on it on the other." }));
  const input = el("input", { type: "text", "data-role": "conflict-reason", "aria-label": "Override reason" });
  dialog.append(input);
  dialog.append(el("div", { class: "reason", "data-role": "conflict-reason-error", "aria-live": "assertive", text: "" }));
  dialog.append(el("button", { type: "button", "data-action": "override", text: "Override with reason", onclick: () => onOverride(input.value) }));
  resolver.append(dialog);
  return resolver;
}
