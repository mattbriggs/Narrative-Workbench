// Node test runner tests for the observable store (SRS SS8.1, REQ-002).
import { test } from "node:test";
import assert from "node:assert/strict";

import { Store, initialState } from "./store.mjs";
import { ProposalState } from "../statecharts/proposal.mjs";

test("initial state matches the observable contract defaults", () => {
  const s = initialState();
  assert.equal(s.mode, "composition");
  assert.equal(s.proposalState, ProposalState.NONE);
  assert.equal(s.syncState, "current");
  assert.equal(s.commitId, null);
});

test("selection updates selectedId but never the commit", () => {
  const store = new Store({ ...initialState(), commitId: "c42" });
  let seen = null;
  const off = store.subscribe((st) => (seen = st));
  store.select("actorA", "actor");
  assert.equal(store.state.selectedId, "actorA");
  assert.equal(store.state.commitId, "c42"); // unchanged
  assert.equal(seen.selectedId, "actorA");
  off();
});

test("subscribers can unsubscribe", () => {
  const store = new Store();
  let count = 0;
  const off = store.subscribe(() => (count += 1));
  store.setProposalState(ProposalState.DRAFT);
  off();
  store.setProposalState(ProposalState.SUBMITTED);
  assert.equal(count, 1);
});

test("projectionReady sets version and current sync", () => {
  const store = new Store({ ...initialState(), commitId: "c1" });
  store.projectionReady("v9");
  assert.equal(store.state.projectionVersion, "v9");
  assert.equal(store.state.syncState, "current");
});

test("selection guard throws if a patch smuggles a commit change (REQ-002)", () => {
  class BadStore extends Store {
    _patch(patch) {
      // Simulate a defect that changes the commit during selection.
      super._patch({ ...patch, commitId: "cHACK" });
    }
  }
  const store = new BadStore({ ...initialState(), commitId: "c42" });
  assert.throws(() => store.select("actorA"), /must not change canonical commit/);
});
