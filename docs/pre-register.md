# [PRE] Register — disposition tracker

The governing spec (§9, Table 40) prescribes 20 rules because the design is
silent or intentionally open. Each stays **open (Proposed)** until its named
owner confirms or overrides it. This file records disposition only; it MUST NOT
mark an item Confirmed on an owner's behalf, and it MUST NOT remove or alter a
`[PRE]` provenance tag (`CLAUDE.md` C-4).

Implementations MAY build against a `[PRE]` value, but any feature that depends
on an open `[PRE]` item is **not accepted** until the owner signs off. Record a
sign-off only when the owner gives it, with who and when.

| ID | Rule | Location | Owner | Status | Signed off by | Date |
| --- | --- | --- | --- | --- | --- | --- |
| PRE-01 | Bind repository, module, UI framework, platform, and accessibility API. | §1–2 | Developer lead | Proposed | — | — |
| PRE-02 | Confirm DTCG palette, typography, spacing, status, focus, and motion tokens. | §4 | Lead UX designer | Proposed | — | — |
| PRE-03 | Confirm Inter and IBM Plex Mono or approve replacements and loaded weights. | §4 | Lead UX designer | Proposed | — | — |
| PRE-04 | Confirm reference, default, and minimum viewport sizes and breakpoints. | §5 | Lead UX designer | Proposed | — | — |
| PRE-05 | Confirm 252px Navigator, 320px Inspector, 220px Trace, 520px primary minimum. | §5 | Lead UX designer | Proposed | — | — |
| PRE-06 | Confirm internal-pane scrolling and no outer scroll at wide and medium sizes. | §5 | Lead UX designer | Proposed | — | — |
| PRE-07 | Confirm ARIA or native accessibility roles for CMP-01 through CMP-18. | §6 | Information architect | Proposed | — | — |
| PRE-08 | Confirm global region-cycle, command search, trace, and undo shortcuts. | §7 | Product manager + developer lead | Proposed | — | — |
| PRE-09 | Confirm empty, loading, error, disabled, permission, and offline copy patterns. | CMP-18 | Product manager | Proposed | — | — |
| PRE-10 | Confirm visible disabled reasons and when disabled controls remain focusable. | CMP-03 CMP-18 | Information architect | Proposed | — | — |
| PRE-11 | Confirm tree, listbox, toolbar, tabs, and modal-dialog APG keyboard patterns. | §6–7 | Information architect | Proposed | — | — |
| PRE-12 | Confirm Proposal preview and Conflict resolver dialog geometry and focus. | CMP-09 CMP-16 | Lead UX designer | Proposed | — | — |
| PRE-13 | Confirm graph object size, semantic zoom, list alternative, and connect workflow. | CMP-10 | Lead UX designer | Proposed | — | — |
| PRE-14 | Confirm comparison-matrix columns, sticky headers, and horizontal overflow. | CMP-14 | Lead UX designer | Proposed | — | — |
| PRE-15 | Confirm live-region policy for job lifecycle and failures. | CMP-15 | Information architect | Proposed | — | — |
| PRE-16 | Confirm narrow-screen labels, active-tab default, and 360px behavior. | CMP-17 | Lead UX designer | Proposed | — | — |
| PRE-17 | Confirm selection synchronization behavior during projection failures. | §7 | Developer lead | Proposed | — | — |
| PRE-18 | Confirm that unhandled events produce no mutation and a visible reason. | §7 | Developer lead | Proposed | — | — |
| PRE-19 | Confirm shipped copy introduced by the specification. | §6–8 | Product manager | Proposed | — | — |
| PRE-20 | Confirm WCAG 2.2 AA as the web target or equivalent native criteria. | §4 §10 | Product manager | Proposed | — | — |

**Status summary:** 20 Proposed, 0 Confirmed, 0 Overridden. No feature in this build may be marked accepted while it depends on a still-Proposed item.

## Related open questions (from the SRS §10)

OQ-01…OQ-12 remain open. **OQ-12 (the meaning of `ghost` in the state-field vocabulary) is undefined in all design sources; no implementation may use the term until the owner defines it.**
