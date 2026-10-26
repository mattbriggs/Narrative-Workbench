// selection.mjs
// Selection and projection state machine (SRS SS7 selection/projection chart).
// Changing selection or projection MUST NOT change canonical state (REQ-002,
// REQ-181). A stale projection (commit mismatch) is discarded; a failed rebuild
// preserves the last valid projection and exposes recovery (REQ-008).

export const SyncState = Object.freeze({
  CURRENT: "current",
  REBUILDING: "rebuilding",
  FAILED: "failed",
});

/**
 * @typedef {{selectedId:?string, syncState:string, commitId:?string, projectionVersion:?string, lastValidVersion:?string}} Sel
 */

/** Begin selecting a stable id; requests a projection rebuild (non-mutating). */
export function select(sel, stableId) {
  return { ...sel, selectedId: stableId, syncState: SyncState.REBUILDING };
}

/**
 * A projection finished rebuilding. Applied only if it matches the current
 * commit; a stale projection is discarded and the rebuild continues.
 */
export function projectionReady(sel, commitId, version) {
  if (commitId !== sel.commitId) {
    return { ...sel, syncState: SyncState.REBUILDING }; // discard stale
  }
  return { ...sel, syncState: SyncState.CURRENT, projectionVersion: version, lastValidVersion: version };
}

/** A projection rebuild failed; keep the last valid projection and expose recovery. */
export function projectionFailed(sel) {
  return { ...sel, syncState: SyncState.FAILED };
}

/** Retry a failed rebuild. */
export function retry(sel) {
  return { ...sel, syncState: SyncState.REBUILDING };
}
