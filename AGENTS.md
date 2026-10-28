# Agent instructions

Read [CONTRIBUTING.md](CONTRIBUTING.md) before working: it defines the review tiers, the task loop, matching integrity, the evidence records and the hostile-review checklist. The [README](README.md) names the targets, the owner and the build commands.

- Keep original executables, disc images, assets and trial output out of public Git. Use the pinned, owner-approved build environment and do not alter supporting dependencies or their access controls; report dependency problems in an issue for the owner's decision.
- Work on a dedicated branch in your own checkout or worktree. Open a draft PR early with the unit names and target ids in its title; check open PRs before starting. Preserve unrelated changes and coordinate live overlaps on shared files.
- Keep recovered facts, hypotheses, function-level matches, combined-build results and review verdicts distinct. Report what was actually checked, on which revision and for which targets.
- Preserve useful partial reconstruction in normal source files as `NonMatching` objects so CI measures it. Original bytes stay in the verified linked build until promotion. Matching incompleteness alone is not a review failure.
- Record evidence for names, boundaries, types and compiler profiles in `config/<target id>/evidence.tsv` ([format](config/README.md)) in the same PR as the change it supports.
- State the PR's tier in its Scope line and complete the records that tier requires. An author cannot provide its own independent review. A `SHIP` verdict means that review passed; it does not approve a merge.
- **Only the project owner authorizes and performs merges into `main`.** No agent enables auto-merge, pushes to `main`, force-pushes `main` or another contributor's branch, or changes branch rules, repository settings, the build image or its digest. Push a work branch or open a PR only when authorized for the task, then leave it for the owner's decision.
- Address review feedback without weakening checks, hiding mismatches or changing project rules to accommodate a patch. Propose workflow improvements through a separate PR.
- Keep handoffs concise: changes, evidence, validation per target, unresolved findings and review state. Do not add running status diaries to the repository.

Before calling a shared change safe for every target, an agent has done four things, per active target:

1. Built every active target and confirmed `config/<target id>/build.sha1` on each.
2. Run objdiff per target for each touched unit and reported the `Matching` state and progress delta in the PR's Targets table.
3. Run `python3 tools/versions.py diff` on every file it added a `#if VERSION_` block to, and read the result.
4. Added evidence rows to each affected target's `evidence.tsv`.

## Project

These are the owner's rules for this repository. They come first here; where they are stricter or more specific than the sections above, they win. The process docs they name are under `docs/process/`; the hostile review checklist is `docs/review-checklist.md`, and the evidence for every name is `config/GV4E69-rev0/name_sources.tsv` (so `evidence.tsv` stays empty).

A matching decompilation of MVP Baseball 2005 (GameCube, GV4E69, USA; EA). The goal is EA's code
exactly as EA wrote it, **named and commented as it is matched**. A PC port and mods start from that code later;
the decomp never bends the C to suit a port. The byte match (`build/<target id>/main.dol: OK`) proves
the code; the accuracy loop (`docs/process/pass.md`) proves the words.

Fidelity order: (1) EA's own form, 32-bit habits and all (a `// port:` note marks a hazard);
(2) only when that can't be found, a labelled `// fake match:` that leaves the logic exactly
unchanged; (3) never change what the game does to satisfy the compiler.

Read next, in this order: `docs/process/state.md` (where things stand, what is parked), `docs/process/pass.md`
(what a pass is, the per-file loop and the feedback loops), `docs/fidelity.md` (how the code must
read; owner, 2026-09-30), then `docs/process/brief.md` (every lane reads it first).
Cloud setup: `tools/cloud/README.md`.

This project learns from `mitsevox/tw2004` (Tiger Woods 2004, a finished 100% decomp). Its process
docs are borrowed from its matching era (commit `60f149c2`) and its infrastructure from its latest
state. A tw2004 rule applies here only once it is written in this repo.

### Hard rules (the owner's; never relax them)

- **Only exactly 100% counts.** Every commit ends with `main.dol: OK`.
- **Exact means named and commented, in the same commit** (owner, 2026-09-29). No function becomes
  exact without its name, its evidence row and its comment. No second pass will come.
- **Never delete what you have not checked.** Chain the delete on the check. Agents never delete
  files at all.
- **No game files in git**: no `main.dol`, disc images, ELF/PDB/SELF, archives, art or other game
  data. The build gets `main.dol` from a private container (`tools/cloud/`, CI).
- **No official SDK files in the repo** (Nintendo or Metrowerks headers, libraries, documentation),
  and leaked SDK material is never discussed publicly. Decompiled SDK and runtime code taken from
  public decomps (each with its CREDITS/README) is fine.
- **Never edit C or headers through the shell** (sed, heredocs, echo, `python -c`): it strips
  backslashes. Use the editor tools; a repeated edit is a saved Python script whose diff is read.
- **Names and comments are true to the code**, with evidence logged for every name (`docs/process/pass.md`
  "Evidence").
- **At every phase change, re-read these rules and the agent docs**, and ask the owner about any
  rule written for the previous phase. Never carry an old rule into new work silently.
- **Downloads, purchases, posts, messages: ask the owner first.** Secrets (tokens) are created and
  stored by the owner; never ask for their values.
- The owner is **Lucas** (GitHub `mitsevox`).

### Build and verify

```
python configure.py        # downloads compilers and tools (wibo on Linux)
ninja                      # must end with: build/<target id>/main.dol: OK
ninja build/<target id>/report.json     # objdiff scores
```
`orig/<target id>/sys/main.dol` must exist first. In the cloud run `tools/cloud/setup.sh` (needs the
owner's `MVP_BUILD_TOKEN` secret). The target id is `GV4E69-rev0` (USA, revision 0; `main.dol` SHA-1
`da6becdbea614d03c4b5eae9f8a0fb08e0a184dd`).

### Working with the owner

- Plain, friendly English; short. Say what each code area does in the game, not just file names.
- Concept first, then the owner's green light, then small chunks.
- Numbers exactly as measured (report.json and the accuracy log), side by side. Estimates come from
  measured pace, never gut feel.
- Park anything that needs the owner's decision in `docs/process/state.md`.

### Current phase: decomping (from 2026-09-30)

Scaffold, discovery and the pilot are done. Game units go through the per-file loop in
`docs/process/pass.md` under `docs/fidelity.md`; none merges without the hostile review's SHIP. Where
things stand and what is next: `docs/process/state.md`.
