// Node built-in test runner tests for the UI statecharts (SRS SS3.8/3.11, SS7).
import { test } from "node:test";
import assert from "node:assert/strict";

import { ProposalState, step as pstep, isDurable } from "./proposal.mjs";
import { JobState, step as jstep, mayShowCommitted } from "./job.mjs";
import { SyncState, select, projectionReady, projectionFailed, retry } from "./selection.mjs";

test("proposal happy path: acceptance is distinct from commit", () => {
  let s = ProposalState.NONE;
  s = pstep(s, { type: "mutatingGesture" }).state;
  assert.equal(s, ProposalState.DRAFT);
  s = pstep(s, { type: "submit", schemaComplete: true, mayPropose: true }).state;
  assert.equal(s, ProposalState.SUBMITTED);
  s = pstep(s, { type: "contextResolved" }).state;
  s = pstep(s, { type: "hardChecksPass" }).state;
  assert.equal(s, ProposalState.AWAITING_APPROVAL);
  s = pstep(s, { type: "approve", authorized: true }).state;
  assert.equal(s, ProposalState.ACCEPTED);
  assert.equal(isDurable(s), false);
  s = pstep(s, { type: "commit", parentUnchanged: true }).state;
  assert.equal(isDurable(s), true);
});

test("proposal: incomplete schema and unauthorized are refused with reasons", () => {
  assert.match(pstep(ProposalState.DRAFT, { type: "submit", schemaComplete: false, mayPropose: true }).reason, /incomplete/);
  assert.match(pstep(ProposalState.DRAFT, { type: "submit", schemaComplete: true, mayPropose: false }).reason, /may not propose/);
  assert.match(pstep(ProposalState.AWAITING_APPROVAL, { type: "approve", authorized: false }).reason, /authority/);
});

test("proposal: hard failure rejects and revision loops", () => {
  assert.equal(pstep(ProposalState.VALIDATING, { type: "hardInvariantFails" }).state, ProposalState.REJECTED);
  const r = pstep(ProposalState.AWAITING_APPROVAL, { type: "requestRevision" }).state;
  assert.equal(r, ProposalState.REVISION_REQUESTED);
  assert.equal(pstep(r, { type: "edit" }).state, ProposalState.DRAFT);
});

test("proposal: parent changed opens conflict; resolved allows commit", () => {
  assert.match(pstep(ProposalState.ACCEPTED, { type: "commit", parentUnchanged: false }).reason, /conflict/);
  assert.equal(pstep(ProposalState.ACCEPTED, { type: "commit", conflictResolved: true }).state, ProposalState.COMMITTED);
});

test("proposal: unhandled event is a no-mutation", () => {
  const r = pstep(ProposalState.COMMITTED, { type: "mutatingGesture" });
  assert.equal(r.ok, false);
  assert.match(r.reason, /no transition/);
});

test("job: partial output is never shown committed", () => {
  let s = JobState.IDLE;
  s = jstep(s, { type: "enqueue" }).state;
  s = jstep(s, { type: "workerStarted" }).state;
  s = jstep(s, { type: "partialResult" }).state;
  assert.equal(s, JobState.PARTIAL);
  assert.equal(mayShowCommitted(s), false);
  s = jstep(s, { type: "moreWork" }).state;
  s = jstep(s, { type: "completed" }).state;
  assert.equal(mayShowCommitted(s), true);
});

test("job: failure retries into a new attempt; cancel paths", () => {
  assert.equal(jstep(JobState.RUNNING, { type: "failed" }).state, JobState.FAILED);
  assert.equal(jstep(JobState.FAILED, { type: "retry" }).state, JobState.QUEUED);
  assert.equal(jstep(JobState.QUEUED, { type: "cancel" }).state, JobState.CANCELLED);
  assert.equal(jstep(JobState.RUNNING, { type: "cancelAcknowledged" }).state, JobState.CANCELLED);
  assert.equal(jstep(JobState.IDLE, { type: "nope" }).ok, false);
});

test("selection: stale projection is discarded, matching one applies", () => {
  let sel = { selectedId: null, syncState: SyncState.CURRENT, commitId: "c42", projectionVersion: null, lastValidVersion: null };
  sel = select(sel, "actorA");
  assert.equal(sel.syncState, SyncState.REBUILDING);
  assert.equal(sel.selectedId, "actorA");
  // Stale projection for a different commit is discarded.
  sel = projectionReady(sel, "cOLD", "v1");
  assert.equal(sel.syncState, SyncState.REBUILDING);
  // Matching projection applies.
  sel = projectionReady(sel, "c42", "v2");
  assert.equal(sel.syncState, SyncState.CURRENT);
  assert.equal(sel.projectionVersion, "v2");
});

test("selection: failed rebuild keeps last valid and can retry", () => {
  let sel = { selectedId: "x", syncState: SyncState.CURRENT, commitId: "c1", projectionVersion: "v1", lastValidVersion: "v1" };
  sel = projectionFailed(sel);
  assert.equal(sel.syncState, SyncState.FAILED);
  assert.equal(sel.lastValidVersion, "v1");
  sel = retry(sel);
  assert.equal(sel.syncState, SyncState.REBUILDING);
});
