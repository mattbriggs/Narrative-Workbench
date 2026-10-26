// proposal.mjs
// Proposal lifecycle state machine (SRS SS3.8, REQ-071), mirroring the engine
// and Rust application layer. Acceptance is distinct from commit (REQ-076): the
// `accepted` state does not change canonical state; only `committed` persists.
// An unhandled (state, event) pair returns a no-mutation result with a visible
// reason (REQ-188).

export const ProposalState = Object.freeze({
  NONE: "none",
  DRAFT: "draft",
  SUBMITTED: "submitted",
  VALIDATING: "validating",
  REJECTED: "rejected",
  AWAITING_APPROVAL: "awaitingApproval",
  REVISION_REQUESTED: "revisionRequested",
  ACCEPTED: "accepted",
  COMMITTING: "committing",
  COMMITTED: "committed",
});

/**
 * Apply an event to a proposal state.
 * @param {string} state current ProposalState
 * @param {{type:string, schemaComplete?:boolean, mayPropose?:boolean, authorized?:boolean, parentUnchanged?:boolean, conflictResolved?:boolean}} event
 * @returns {{ok:true, state:string} | {ok:false, reason:string}}
 */
export function step(state, event) {
  const S = ProposalState;
  switch (`${state}:${event.type}`) {
    case `${S.NONE}:mutatingGesture`:
      return ok(S.DRAFT);
    case `${S.DRAFT}:submit`:
      if (!event.schemaComplete) return no("proposal schema is incomplete");
      if (!event.mayPropose) return no("actor may not propose");
      return ok(S.SUBMITTED);
    case `${S.SUBMITTED}:contextResolved`:
      return ok(S.VALIDATING);
    case `${S.VALIDATING}:hardInvariantFails`:
      return ok(S.REJECTED);
    case `${S.VALIDATING}:hardChecksPass`:
      return ok(S.AWAITING_APPROVAL);
    case `${S.AWAITING_APPROVAL}:requestRevision`:
      return ok(S.REVISION_REQUESTED);
    case `${S.REVISION_REQUESTED}:edit`:
      return ok(S.DRAFT);
    case `${S.AWAITING_APPROVAL}:approve`:
      return event.authorized
        ? ok(S.ACCEPTED)
        : no("commit requires narrative designer authority");
    case `${S.ACCEPTED}:commit`:
      return event.parentUnchanged || event.conflictResolved
        ? ok(S.COMMITTED)
        : no("parent commit changed; resolve the semantic conflict");
    default:
      return no(`no transition from ${state} on ${event.type}`);
  }
}

/** True when the state means canonical state is durable. */
export function isDurable(state) {
  return state === ProposalState.COMMITTED;
}

const ok = (state) => ({ ok: true, state });
const no = (reason) => ({ ok: false, reason });
