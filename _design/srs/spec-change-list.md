# Change list: Visual and Interaction Specification

Proposed changes to the Narrative Workbench Visual and Interaction Specification
(draft, 23 October 2026). They come from the readiness review on 2026-10-25,
which found 5 of the 9 readiness items passing. Section numbers refer to the
spec; the spec is in [visual-and-interaction-specification.md](visual-and-interaction-specification.md).

Each change keeps the spec's `[OBS]`/`[PRE]` tagging. New rules introduced here
are `[PRE]`, and the [PRE] register in §9 needs a row and an owner sign-off for
each one (see [pre-register.md](pre-register.md)).

**Status: Applied 2026-10-25.** PRE-21 to PRE-27 were confirmed and all ten
changes are in the spec. The readiness gate now passes 9 of 9 items.

Applying the list needed these adjustments:

- **CL-05:** DTCG has no `vh` unit, so the trace drawer maximum is
  `dimension.role.trace-max-viewport-ratio`, a `number` token (0.55), not
  `trace-max` 55vh. CMP-13's 4px accent border also needed a token, so
  `dimension.role.accent-border-width` (4px) was added. `badge-height` aliases
  `{dimension.base.5}`. CMP-17's height uses the existing
  `{dimension.role.control-height}`.
- **CL-02:** CMP-02 had no `focus-visible` state row, so one was added. It is
  deferred to the §10 visual checks.
- **CL-08:** The statecharts were rewritten to match the spec's state variables.
  Three variables were added to §7: `conflictState`, `inspectorState`, and
  `activeRegionTab`.
- **CL-09:** CMP-11 `selected` and CMP-17 `default` got scenario coverage, not
  deferral. In total 49 scenarios were added, one of them a Scenario Outline.

| ID | Change | Section | Priority | Unblocks readiness item |
| -- | ------ | ------- | -------- | ----------------------- |
| CL-01 | Bind "Implements into" to the confirmed stack | §1 | Required | Header table complete |
| CL-02 | Add a focus-ring token for dark surfaces | §4, CMP-02, CMP-17 | Required | Token JSON valid; WCAG target (PRE-20) |
| CL-03 | Darken muted text so it passes on every surface | §4 | Recommended | WCAG target (PRE-20) |
| CL-04 | Add a control-border token | §4, CMP-11, CMP-12 | Recommended | WCAG target (PRE-20) |
| CL-05 | Replace literal values in component rules with role tokens | §4, §5, §6 | Required | Token JSON valid; §10 token test |
| CL-06 | Correct the alias count | §4 | Required | Token JSON valid |
| CL-07 | Add the `committing` state to the proposal statechart | §7 | Required | Statecharts cover each region |
| CL-08 | Add statecharts for the drawers, tabs, and conflict resolver | §7 | Recommended | Statecharts cover each region |
| CL-09 | Give every component state a scenario or a deferral | §6 | Required | Every state has scenario coverage |
| CL-10 | Add register rows for the new [PRE] rules | §9 | Required | [PRE] register has dispositions |

---

## CL-01 Bind "Implements into" to the confirmed stack

**Section:** §1 Header table, row "Implements into".

**Problem:** The row still says "Technology-neutral responsive application", but
PRE-01 was confirmed on 2026-10-25 with a specific stack.

**Change:** Replace the row text with:

> [PRE] Tauri desktop application: Rust core and JavaScript web front end
> rendered in the platform WebView, with a Python sidecar using NetworkX for the
> narrative graph engine. Repository: Narrative-Workbench. Accessibility API:
> WAI-ARIA in the WebView, exposed through the platform WebView's accessibility
> bridge (WebKit on macOS). Confirmed under PRE-01 on 2026-10-25.

Also update §9 "Known differences", row 8 (Technology target), column
"Specification follows", to "Tauri, Rust, JS, and Python sidecar (PRE-01)".

---

## CL-02 Add a focus-ring token for dark surfaces

**Sections:** §4 token JSON and usage notes; CMP-02 Global context bar;
CMP-17 Responsive region tabs.

**Problem:** `{color.role.focus-ring}` (`#2C67A1`) against
`{color.role.surface-strong}` (`#173A63`) is 1.96:1. WCAG 2.2 SC 1.4.11 needs
3:1. Focus rings sit on the strong surface in the global context bar and on
active-mode and narrow-screen tabs, which use strong selection. As written, the
tokens confirmed in PRE-02 break the WCAG 2.2 AA target confirmed in PRE-20.

**Change:**

1. Add to `color.role` in the token JSON:

   ```json
   "focus-ring-on-strong": { "$value": "{color.base.white}" }
   ```

   White on `#173A63` is 11.53:1.

2. Add a usage-notes row:

   | Rule | Requirement |
   | ---- | ----------- |
   | Focus on strong surfaces | [PRE] Inside `{color.role.surface-strong}` regions, and on any control with strong selection, the focus ring uses `{color.role.focus-ring-on-strong}`. Everywhere else it uses `{color.role.focus-ring}`. |

3. In CMP-02 and CMP-17, change the `focus-visible` state text to name
   `{color.role.focus-ring-on-strong}`.

---

## CL-03 Darken muted text so it passes on every surface

**Section:** §4 token JSON.

**Problem:** `{color.role.text-muted}` (`#687684`) passes on the canvas (4.65:1)
but fails 4.5:1 on `surface-subtle` (4.30:1) and `surface-selection` (4.11:1).
The spec doesn't forbid muted text on those surfaces, and selected navigator
rows are likely to carry secondary text.

**Change:** Change `color.base.ink-500` from `#687684` to `#5B6875`. That gives
5.70:1 on the canvas, 5.26:1 on subtle, and 5.04:1 on selection.

**Alternative:** Keep the value and add a usage rule: "[PRE] `text-muted` is
allowed only on `surface-canvas`."

---

## CL-04 Add a control-border token

**Sections:** §4 token JSON and usage notes; CMP-11; CMP-12.

**Problem:** `{color.role.border-default}` (`#D9E0E7`) is 1.33:1 on the canvas.
That's fine for separators between regions. It fails SC 1.4.11 where a border is
the only visible edge of an interactive object, such as trajectory options
(CMP-11) and evidence spans (CMP-12).

**Change:**

1. Add to `color.role`:

   ```json
   "border-control": { "$value": "{color.base.ink-500}" }
   ```

   This is at least 4.65:1 on the canvas, or 5.04:1 or more after CL-03.

2. Add a usage-notes row: "[PRE] `border-default` is for separators only. Any
   border that identifies an interactive object uses `border-control`."

3. In CMP-11 Box and CMP-12 Box, change `border token` and
   `{color.role.border-default}` to `{color.role.border-control}`.

---

## CL-05 Replace literal values in component rules with role tokens

**Sections:** §4 token JSON; §5 table and "Wide-screen track contract"; §6 Box
rules for CMP-01 to CMP-18.

**Problem:** Every component's Box rule writes sizes as raw values (`44px`,
`252px`, `1px`, and so on). The §4 token rules say component code MUST use
role tokens, and the §10 token test fails on literal dimensions. Built as
written, the spec fails its own acceptance test. Several of the values already
have role tokens that the text never uses.

**Change, part 1:** Rewrite Box rules to use the role tokens that already exist.

| Literal | Use | Where |
| ------- | --- | ----- |
| `44px` | `{dimension.role.global-bar-height}` | CMP-01, CMP-02, §5 |
| `36px` | `{dimension.role.command-bar-height}` | CMP-01, CMP-03, §5 |
| `252px` | `{dimension.role.navigator-wide}` | CMP-04, §5 |
| `320px` | `{dimension.role.inspector-wide}` | CMP-06, §5 |
| `220px` (trace) | `{dimension.role.trace-default}` | CMP-07, §5 |
| `1px` | `{dimension.role.separator-width}` | CMP-03, 04, 06, 07, 12, §5 |
| `3px` (focus) | `{dimension.role.focus-width}` | §4 usage notes, CMP-03 |
| `8px` | `{dimension.role.space-inline}` | CMP-08, 10, 11, 13, 14 |
| `12px` | `{dimension.role.space-stack}` | CMP-02, 03, 06, 10, 11, 12, 13, 14 |
| `16px` | `{dimension.role.space-region}` | CMP-02, 05, 18 |
| `4px` radius | `{radius.role.control}` | CMP-08, 12 (already used) |

**Change, part 2:** Add these role tokens for values that have none.

| New token | Value | Replaces | Where |
| --------- | ----- | -------- | ----- |
| `dimension.role.space-tight` | `{dimension.base.1}` (4px) | `4px` gaps | CMP-03, CMP-08, CMP-13 |
| `dimension.role.space-loose` | `{dimension.base.5}` (24px) | `24px` padding | CMP-09 |
| `dimension.role.space-section` | `{dimension.base.6}` (32px) | `32px` margins | CMP-09, CMP-18 |
| `dimension.role.focus-offset` | 2px | `2px` focus offset | §4 usage notes, CMP-03, CMP-17 |
| `dimension.role.badge-height` | 24px | `min-height:24px` | CMP-08 |
| `dimension.role.badge-padding-block` | 2px | `padding:2px 8px` | CMP-08 |
| `dimension.role.primary-min` | 520px | `minmax(520px,1fr)` | CMP-05, §5 |
| `dimension.role.navigator-medium` | 220px | medium navigator width | §5 |
| `dimension.role.inspector-drawer` | 420px | `min(420px, 90vw)` | §5, CMP-06 |
| `dimension.role.trace-min` | 120px | trace minimum | CMP-07, §5 |
| `dimension.role.trace-max` | 55vh | trace maximum | CMP-07, §5 |
| `dimension.role.dialog-width` | 720px | `min(720px, …)` | CMP-09 |
| `dimension.role.dialog-inset` | 48px | `calc(100vh - 48px)` | CMP-09 |
| `dimension.role.card-min` | 160px | object card minimum | CMP-10 |
| `dimension.role.message-max` | 560px | `max-width:560px` | CMP-18 |
| `dimension.role.breakpoint-medium` | 768px | breakpoints | §5, CMP-16, CMP-17 |
| `dimension.role.breakpoint-wide` | 1200px | breakpoints | §5 |
| `typography.role.tab-label-narrow` | 11px label override | "11px label token override" (no token exists) | CMP-17 |

Breakpoints can't be CSS custom properties inside media queries. Add a token
rule: "[PRE] Breakpoint tokens are resolved at build time into media queries.
They are the only tokens that may appear as generated literals in stylesheets."

Viewport-relative values (`100vw`, `100vh`, `90vw`, `100%`) and `1fr`/`auto`
are layout keywords, not design values. Add them to the §10 token test's allow
list.

**Then:** Re-run the alias check after adding tokens and update the count
(see CL-06).

---

## CL-06 Correct the alias count

**Section:** §4, "Complete DTCG token JSON".

**Problem:** The validation note says "30 aliases were checked". The token file
has 35 aliases, all of which resolve.

**Change:** Replace the note with the result of a fresh check after CL-02 to
CL-05, for example: "[PRE] Mechanical validation result: JSON parsed; N tokens;
M aliases checked; 0 unresolved; 0 cycles; every token has a `$type`."

---

## CL-07 Add the `committing` state to the proposal statechart

**Section:** §7, "Proposal lifecycle statechart".

**Problem:** The chart goes straight from `accepted` to `committed`. But:

- the `proposalState` variable lists `committing`;
- CMP-09 has a `committing` state ("Prevent duplicate submission and show
  parent commit");
- a §7 global invariant says an accepted proposal MUST NOT be shown as
  committed until persistence succeeds.

So there is no state for "saving in progress", and no path for a failed save.
The chart also has no transition out of `rejected`, and doesn't say that
`rejected` is final.

**Change:** Replace the two `accepted --commit` lines with:

```text
accepted --commit [parentUnchanged || conflictResolved] / freezeAndPersist--> committing
accepted --commit [parentChanged && !conflictResolved] / openConflictResolver--> accepted
committing --persistSucceeded / recordDeltaAndProvenance--> committed
committing --persistFailed / keepAcceptedAndExposeRecovery--> accepted
```

Add after the chart:

> [OBS] `rejected` and `committed` are final states. Rework after a rejection
> starts a new draft proposal linked to the rejected one; the rejected record
> is not reopened. (NW ADD v1.1 Figure 10 note: "Terminal records retain the
> proposal, checks, decision, alternatives, and provenance.")

Add a scenario to CMP-09:

```gherkin
@pre
Scenario: committing blocks duplicate submission
  Given an accepted proposal whose parent commit is unchanged
  When the user requests Commit
  Then proposalState is committing, the Commit control is disabled with a visible reason, and the parent commit is shown
  And proposalState becomes committed only after persistSucceeded
```

**Knock-on:** NW ADD v1.1 Figure 10 has the same gap. Raise it against the
architecture document as well.

---

## CL-08 Add statecharts for the drawers, tabs, and conflict resolver

**Section:** §7.

**Problem:** The five §7 statecharts cover navigation, proposals, branches,
selection and projection, and long jobs. These interactive regions have no
statechart, only state tables and a one-line Behaviour rule:

- CMP-06 Inspector drawer (medium screens)
- CMP-07 Trace and validation drawer
- CMP-16 Semantic conflict resolver
- CMP-17 Responsive region tabs

**Change:** Add four statecharts. Proposed content, for the owners to confirm:

```text
Trace drawer statechart
closed --toggle / moveFocusToHeading--> open
open --toggle / restoreFocusToInvoker--> closed
open --escape / restoreFocusToInvoker--> closed
open --selectTab(tab) / showTab--> open

Inspector drawer statechart (medium screens)
closed --openInspector / moveFocusToHeading--> open
open --escape / restoreFocusToInvoker--> closed
open --viewportBecomesWide / dockInspector--> docked
docked --viewportBecomesMedium / undockInspector--> closed

Conflict resolver statechart
unresolved --choose(fork) / createBranchWithBothParents--> forking
unresolved --choose(revise) / createEditableSuccessor--> revising
unresolved --choose(override) [authorized && rationaleNonEmpty] / recordOverride--> resolved
forking --forkCreated / recordChosenAction--> resolved
forking --forkFailed / preserveRationale--> error
revising --successorCreated / recordChosenAction--> resolved
error --retry / reuseRationale--> unresolved

Region tabs statechart (narrow screens)
work --selectTab(tab) / preserveScrollAndShow--> tab
tab --selectTab(other) / preserveScrollAndShow--> other
anyTab --viewportBecomesMedium / restoreRegions--> regions
```

---

## CL-09 Give every component state a scenario or a deferral

**Section:** §6, each component's "Accept." block.

**Problem:** Each component has one scenario, and the spec has no deferrals.
About 79 of the 98 component states aren't named in any component scenario.
The readiness gate needs every state to have a scenario or an explicit
deferral.

**Change:** Add a "State coverage" table to each component's Accept block:

| State | Covered by |
| ----- | ---------- |
| *state* | Scenario name, or "Deferred to §10 check 2/3: *reason*" |

Use one rule throughout. States that change behaviour or data get a Gherkin
scenario. States that only change appearance are deferred to the §10
computed-style and screenshot checks, which already test every state.

Proposed dispositions (✓ = already covered, by the component or a screen
scenario):

| Component | Add a scenario | Defer to §10 visual checks | Already covered |
| --------- | -------------- | -------------------------- | --------------- |
| CMP-01 | offline, error | default | rebuilding (Screen 1), narrow (Screen 1) |
| CMP-02 | validating, conflict | clean, overflow | dirty ✓ |
| CMP-03 | running | default, hover, focus-visible | disabled ✓ |
| CMP-04 | empty, loading | overflow | selected ✓, broken-reference (Screen 3) |
| CMP-05 | partial, error, empty | ready | rebuilding (Screen 1) |
| CMP-06 | nothing-selected, editable, validation-error, drawer | — | read-only ✓ |
| CMP-07 | validation-failed, job-running, empty | closed | open ✓ |
| CMP-08 | human, validated, accepted | source | machine ✓, broken (Screen 3) |
| CMP-09 | draft, validating, awaiting-approval, committing (CL-07) | — | accepted ✓, rejected (Screen 5) |
| CMP-10 | provisional, invalid | default, selected, overflow | — |
| CMP-11 | loading, empty | selected | available ✓, validated and accepted (Screen 2) |
| CMP-12 | loading, error | resolved, selected | broken ✓ |
| CMP-13 | machine-proposed, human-proposed, validated, contested | overflow | accepted ✓ |
| CMP-14 | unresolved, partial, empty | changed, overflow | ready (Screen 4) |
| CMP-15 | queued, running, failed, cancelled, complete | — | partial ✓ |
| CMP-16 | forking, revising, error | — | unresolved, override, resolved ✓ |
| CMP-17 | — | focus-visible, badge, overflow | default (Screen 1), active ✓ |
| CMP-18 | loading, error, disabled, no-permission, offline | — | empty ✓ |

That's 54 new scenarios. Each should be short and follow the existing
Given/When/Then style, using the state's own "Change from default" text as the
Then clause. CL-07 gives a worked example.

---

## CL-10 Add register rows for the new [PRE] rules

**Section:** §9, "Prescribed rule register".

**Change:** Add rows, all with status Proposed:

| ID | Rule | Location | Owner |
| -- | ---- | -------- | ----- |
| PRE-21 | Confirm `focus-ring-on-strong` and its usage rule. | §4, CMP-02, CMP-17 | Lead UX designer |
| PRE-22 | Confirm the darker `ink-500` value or the canvas-only rule for muted text. | §4 | Lead UX designer |
| PRE-23 | Confirm `border-control` and the separator-only rule for `border-default`. | §4, CMP-11, CMP-12 | Lead UX designer |
| PRE-24 | Confirm the new dimension and typography role tokens and the breakpoint rule. | §4, §5, §6 | Lead UX designer and developer lead |
| PRE-25 | Confirm the `committing` state, failed-save path, and final states. | §7, CMP-09 | Developer lead |
| PRE-26 | Confirm the drawer, conflict resolver, and region tab statecharts. | §7 | Information architect and developer lead |
| PRE-27 | Confirm the scenario-or-deferral rule and the per-state dispositions. | §6, §10 | Product manager |

Record each sign-off in [pre-register.md](pre-register.md).
