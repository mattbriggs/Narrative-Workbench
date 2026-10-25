// demo-data.js
// Sample narrative data that defines data SHAPE only (spec Table 39, item 5):
// it illustrates the views and MUST NOT ship as fixed product content. No
// visual values live here.

export const DEMO = {
  navigator: [
    { id: "work", label: "Work", kind: "work" },
    { id: "act1", label: "Act I", kind: "act" },
    { id: "scene4", label: "Scene 4 - The Letter", kind: "scene" },
    { id: "actorA", label: "Actor A", kind: "actor" },
    { id: "actorB", label: "Actor B", kind: "actor" },
  ],
  objects: [
    { id: "actorA", label: "Actor A", kind: "actor", mass: 3 },
    { id: "actorB", label: "Actor B", kind: "actor", mass: 1 },
    { id: "letter", label: "The letter", kind: "object", mass: 2 },
  ],
  candidates: [
    { id: "cand-A", label: "Trajectory A", changed: "Actor B suspicion low to moderate" },
    { id: "cand-B", label: "Trajectory B", changed: "Actor B confronts Actor A" },
  ],
  evidence: {
    id: "ed1:span12",
    editionId: "ed1",
    region: "p.12",
    fingerprint: "sha256:9f2c",
    text: "He turned the envelope face down before she could read the name.",
  },
  anchorBroken: true,
  comparison: {
    baseline: "c8f2",
    intervention: "Move identity disclosure to the midpoint",
    rows: [
      { dimension: "World", deterministic: "Disclosure at scene 6", hypotheses: "", invariant: "Event history before disclosure" },
      { dimension: "Epistemic", deterministic: "Actor B learns earlier", hypotheses: "", invariant: "" },
      { dimension: "Affective", deterministic: "", hypotheses: "Tension rises sooner", invariant: "" },
      { dimension: "Structural", deterministic: "Act II reordered", hypotheses: "", invariant: "" },
      { dimension: "Formal", deterministic: "", hypotheses: "Irony reduced", invariant: "" },
      { dimension: "Reader model", deterministic: "", hypotheses: "Intended response: earlier alignment", invariant: "" },
      { dimension: "Provenance", deterministic: "Baseline c8f2; controls: world rules", hypotheses: "", invariant: "" },
    ],
  },
  job: { kind: "simulation", state: "partial" },
};
