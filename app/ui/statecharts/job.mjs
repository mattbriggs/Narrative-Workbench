// job.mjs
// Long-job lifecycle (SRS SS3.11, REQ-110..113). State changes come from real
// job events, never a timer (REQ-111). Partial output is never committed
// (REQ-112). A retry creates a new attempt linked to the prior failure.

export const JobState = Object.freeze({
  IDLE: "idle",
  QUEUED: "queued",
  RUNNING: "running",
  PARTIAL: "partial",
  FAILED: "failed",
  CANCELLED: "cancelled",
  COMPLETE: "complete",
});

/**
 * @param {string} state current JobState
 * @param {{type:string}} event
 * @returns {{ok:true, state:string} | {ok:false, reason:string}}
 */
export function step(state, event) {
  const S = JobState;
  switch (`${state}:${event.type}`) {
    case `${S.IDLE}:enqueue`:
      return ok(S.QUEUED);
    case `${S.QUEUED}:workerStarted`:
      return ok(S.RUNNING);
    case `${S.RUNNING}:partialResult`:
      return ok(S.PARTIAL);
    case `${S.PARTIAL}:moreWork`:
      return ok(S.RUNNING);
    case `${S.RUNNING}:completed`:
      return ok(S.COMPLETE);
    case `${S.RUNNING}:failed`:
      return ok(S.FAILED);
    case `${S.QUEUED}:cancel`:
    case `${S.RUNNING}:cancelAcknowledged`:
      return ok(S.CANCELLED);
    case `${S.FAILED}:retry`:
      return ok(S.QUEUED); // new linked attempt
    default:
      return no(`no transition from ${state} on ${event.type}`);
  }
}

/** Partial output must never be shown as committed/accepted (REQ-112). */
export function mayShowCommitted(state) {
  return state === JobState.COMPLETE;
}

const ok = (state) => ({ ok: true, state });
const no = (reason) => ({ ok: false, reason });
