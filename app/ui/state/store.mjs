// store.mjs
// Observable application state (SRS SS8.1). The store holds the minimum
// observable contract and enforces the global invariant that changing selection
// or projection never changes canonical state (REQ-002, REQ-181).

import { ProposalState } from "../statecharts/proposal.mjs";
import { SyncState } from "../statecharts/selection.mjs";
import { JobState } from "../statecharts/job.mjs";

/** Initial state values (SRS SS8.1 table). */
export function initialState() {
  return {
    mode: "composition",
    workId: null,
    branchId: null,
    commitId: null,
    projectionVersion: null,
    selectedId: null,
    selectedKind: null,
    proposalState: ProposalState.NONE,
    validationState: "idle",
    authorityState: "denied",
    branchState: "active",
    jobState: JobState.IDLE,
    syncState: SyncState.CURRENT,
    drawerState: "closed",
    viewportClass: "wide",
  };
}

/**
 * A tiny observable store. Subscribers are notified after each committed
 * change. Keeps `commitId` immutable across selection changes.
 */
export class Store {
  constructor(state = initialState()) {
    this._state = { ...state };
    this._subs = new Set();
  }

  /** Current immutable snapshot. */
  get state() {
    return { ...this._state };
  }

  /** Subscribe to changes; returns an unsubscribe function. */
  subscribe(fn) {
    this._subs.add(fn);
    return () => this._subs.delete(fn);
  }

  /**
   * Change selection. Updates `selectedId`/`selectedKind` and enters the
   * rebuilding sync state, but MUST NOT change `commitId` (REQ-002).
   * @throws if a caller tries to smuggle a commit change through selection.
   */
  select(id, kind = null) {
    const before = this._state.commitId;
    this._patch({ selectedId: id, selectedKind: kind, syncState: SyncState.REBUILDING });
    if (this._state.commitId !== before) {
      throw new Error("selection must not change canonical commit (REQ-002)");
    }
  }

  /** Set the proposal state (driven by the proposal statechart). */
  setProposalState(s) {
    this._patch({ proposalState: s });
  }

  /** Mark a projection ready at a version. */
  projectionReady(version) {
    this._patch({ syncState: SyncState.CURRENT, projectionVersion: version });
  }

  /** Internal: apply a patch and notify subscribers. */
  _patch(patch) {
    this._state = { ...this._state, ...patch };
    for (const fn of this._subs) fn(this.state);
  }
}
