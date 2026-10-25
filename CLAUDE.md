# CLAUDE.md

Standing rules for every session in this repository. The governing spec is
`Narrative_Workbench_Visual_and_Interaction_Specification.docx` ("the spec").

## Stack

- **App:** Tauri, with a Rust backend and a JavaScript frontend.
- **Engine:** a Python sidecar that uses NetworkX for the narrative graph.

Don't add other frameworks, languages, or graph libraries unless the user asks.

## Cloud sessions

`scripts/cloud-setup.sh` runs at the start of each cloud session and installs
the toolchain. The Python engine uses the `.venv` at the repo root.

A cloud machine has no display, so it can't open the Tauri desktop window. In
the cloud, build and test the Rust and Python parts, and serve the web front
end to headless Chromium (Playwright) for the spec's screenshot checks. Don't
claim the desktop app was checked. The user checks it on their Mac.

## Design tokens

- Use only the spec's **role tokens** (`{color.role.*}`, `{typography.role.*}`,
  `{dimension.role.*}`, `{radius.role.*}`, `{duration.role.*}`,
  `{fontFamily.role.*}`). In code they become CSS variables: replace dots with
  hyphens and add the prefix, for example `{color.role.text-primary}` becomes
  `var(--color-role-text-primary)`.
- Never write raw colour values (hex, `rgb()`, `hsl()`, named colours) in
  component code. The same applies to raw spacing, dimension, font-family, and
  duration values. The DTCG token file is the only place visual values live.
- Don't reference base tokens directly. Components use role-token aliases only.
- The spec's §10 token test fails the build if any literal value appears in
  component code.

## State-field vocabulary

These names are fixed: **body, impulse, boundary, sink, gate, pin, ghost**.
Use them as written in code, the UI, docs, and conversation. Don't rename
them, pluralise them into new terms, or introduce synonyms.

| Term     | Meaning (from the design sketches)                 |
| -------- | -------------------------------------------------- |
| body     | Narrative object; its size is its mass (resistance) |
| impulse  | A change applied to the field, numbered in order   |
| boundary | The edge of the active model                       |
| sink     | A terminal or attracting state                     |
| gate     | A constraint (friction)                            |
| pin      | An evidence pin that ties a claim to its source    |
| ghost    | Not yet defined in the design sources              |

## [PRE] items

Items marked `[PRE]` in the spec are proposed, not decided. Each one stays
**open (Proposed)** until the owner named in the spec's §9 register
(PRE-01 to PRE-20) signs it off. You may build against a [PRE] value, but:

- don't mark one as confirmed, closed, or accepted for an owner;
- don't remove or change a [PRE] provenance tag;
- record a sign-off only when the owner gives it, and include who and when;
- treat any implementation that depends on an open [PRE] item as not accepted.
