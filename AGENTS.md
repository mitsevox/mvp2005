# Agent instructions

Read [CONTRIBUTING.md](CONTRIBUTING.md) before working: it defines the review tiers, the task loop, matching integrity, the evidence records and the hostile-review checklist. The [README](README.md) names the targets, the owner and the build commands.

- Keep original executables, disc images, assets, official SDK files (headers, libraries, documentation) and trial output out of public Git, and never discuss leaked material in public. Use the pinned, owner-approved build environment and do not alter supporting dependencies or their access controls; report dependency problems in an issue for the owner's decision.
- Work on a dedicated branch in your own checkout or worktree. Open a draft PR early with the unit names and target ids in its title; check open PRs before starting. Preserve unrelated changes and coordinate live overlaps on shared files.
- Keep recovered facts, hypotheses, function-level matches, combined-build results and review verdicts distinct. Report what was actually checked, on which revision and for which targets.
- Preserve useful partial reconstruction in normal source files as `NonMatching` objects so CI measures it. Original bytes stay in the verified linked build until promotion. Matching incompleteness alone is not a review failure.
- Record evidence for names, boundaries, types and compiler profiles in `config/<target id>/evidence.tsv` ([format](config/README.md)) in the same PR as the change it supports.
- State the PR's tier in its Scope line and complete the records that tier requires. An author cannot provide its own independent review. A `SHIP` verdict means that review passed; it does not approve a merge.
- **Only the project owner authorizes and performs merges into `main`.** No agent enables auto-merge, pushes to `main`, force-pushes `main` or another contributor's branch, or changes branch rules, repository settings, the build image or its digest. Push a work branch or open a PR only when authorized for the task, then leave it for the owner's decision.
- Address review feedback without weakening checks, hiding mismatches or changing project rules to accommodate a patch. Propose workflow improvements through a separate PR.
- Keep handoffs concise: changes, evidence, validation per target, unresolved findings and review state. Do not add running status diaries to the repository.
- A function becomes exact only with its name, its evidence and its comment in the same PR; there is no later naming pass.
- Never delete a file you have not checked first: make the delete depend on the check. Edit C, C++ and headers with an editor or a saved script whose diff you read, never with sed, heredocs, echo or `python -c` (they mangle backslashes).
- Ask the owner before downloads, purchases, posts or messages anywhere. Tokens and secrets are the owner's to create and store; never ask for their values.
- Working with the owner: plain, short English that says what each code area does in the game; the concept first, then the owner's green light, then small steps; numbers exactly as measured, never estimated by feel. At every change of project phase, re-read these rules and ask the owner about any rule written for the previous phase.

Before calling a shared change safe for every target, an agent has done four things, per active target:

1. Built every active target and confirmed `config/<target id>/build.sha1` on each.
2. Run objdiff per target for each touched unit and reported the `Matching` state and progress delta in the PR's Targets table.
3. Run `python3 tools/versions.py diff` on every file it added a `#if VERSION_` block to, and read the result.
4. Added evidence rows to each affected target's `evidence.tsv`.

## Project

- **What it is.** MVP Baseball 2005 for the GameCube (EA, 2005). One target, `GV4E69-rev0` (USA, revision 0; `main.dol` SHA-1 `da6becdbea614d03c4b5eae9f8a0fb08e0a184dd`). `orig/GV4E69-rev0/sys/main.dol` must exist before `python configure.py && ninja`; a cloud session gets it with `tools/cloud/setup.sh` (needs the owner's `MVP_BUILD_TOKEN` secret; `tools/cloud/README.md`).
- **Toolchain.** Game code and EA's libraries are C++ from SN ProDG (GCC 2.95), linked with SN's `ngcld`; Nintendo's SDK libraries are CodeWarrior-built. Game-code flags are settled per library, not game-wide yet (geomlib: `-Os -G0 -ffloat-store`). Evidence and the ProDG compile rule: [docs/compiler.md](docs/compiler.md).
- **Style guide.** [docs/fidelity.md](docs/fidelity.md) says how the C must read: EA's form, `// MATCH:` and `// fake match:` notes, banned tricks, the tried-ledger in `docs/tried/`, and what the hostile review fails here. The reference file is `src/common/geomlib/geomgroup.cpp`. Library imports (SDK, SN runtime, nfsmw SND) keep upstream's form, credited in `CREDITS.md`.
- **Evidence.** Names and types are tiered T1 to T4 (fidelity rule 1) and logged in `config/GV4E69-rev0/name_sources.tsv`, so `evidence.tsv` stays empty here. Library names are in `linked_names.tsv`, imported units in `imported_units.tsv`.
- **References.** EA's names from the binary: [docs/names.md](docs/names.md) (`tools/research/typeids.py`). MVP's own DWARF for 25 render objects: [docs/disc-inspection.md](docs/disc-inspection.md) (`tools/research/dwarf_lookup.py <Type>`; the export is private in `mitsevox/mvp2005-build`). Related EA builds with symbols: [docs/reference-builds/](docs/reference-builds/README.md) (`tools/research/refmatch.py`); map hits inside MVP's game code are mostly look-alikes. The file map: [docs/filemap.md](docs/filemap.md). SDK and middleware: [docs/sdk.md](docs/sdk.md).
- **Matching tools.** `python tools/match/trial.py src/<unit>.cpp <symbol> --src <scratch>/variant.cpp` compiles one variant with the unit's flags and diffs that function (exit 0 when identical); `ninja` and the report stay the final word.
