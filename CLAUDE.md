# MVP 2005 decomp: start here

A matching decompilation of MVP Baseball 2005 (GameCube, EA). The goal is EA's code exactly as EA
wrote it, **named and commented as it is matched**. A PC port and mods start from that code later;
the decomp never bends the C to suit a port. The byte match (`build/<VERSION>/main.dol: OK`) proves
the code; the accuracy loop (`agents/pass.md`) proves the words.

Fidelity order: (1) EA's own form, 32-bit habits and all (a `// port:` note marks a hazard);
(2) only when that can't be found, a labelled `// fake match:` that leaves the logic exactly
unchanged; (3) never change what the game does to satisfy the compiler.

Read next, in this order: `agents/state.md` (where things stand, what is parked), `agents/pass.md`
(what a pass is and the four feedback loops), then `agents/brief.md` (every lane reads it first).
Cloud setup: `tools/cloud/README.md`.

This project learns from `mitsevox/tw2004` (Tiger Woods 2004, a finished 100% decomp). Its process
docs are borrowed from its matching era (commit `60f149c2`) and its infrastructure from its latest
state. A tw2004 rule applies here only once it is written in this repo.

## Hard rules (the owner's; never relax them)

- **Only exactly 100% counts.** Every commit ends with `main.dol: OK`.
- **Exact means named and commented, in the same commit** (owner, 2026-09-29). No function becomes
  exact without its name, its evidence row and its comment. No second pass will come.
- **Commits and PRs: no `Co-Authored-By`, no "Generated with", no AI footer.** (Carried from
  tw2004; confirm with the owner, `agents/state.md`.)
- **Never delete what you have not checked.** Chain the delete on the check. Agents never delete
  files at all.
- **No game files in git**: no `main.dol`, disc images, ELF/PDB/SELF, archives, art or other game
  data. The build gets `main.dol` from a private container (`tools/cloud/`, CI).
- **No official SDK files in the repo** (Nintendo or Metrowerks headers, libraries, documentation),
  and leaked SDK material is never discussed publicly. Decompiled SDK and runtime code taken from
  public decomps (each with its CREDITS/README) is fine.
- **Never edit C or headers through the shell** (sed, heredocs, echo, `python -c`): it strips
  backslashes. Use the editor tools; a repeated edit is a saved Python script whose diff is read.
- **Names and comments are true to the code**, with evidence logged for every name (`agents/pass.md`
  "Evidence").
- **At every phase change, re-read these rules and the agent docs**, and ask the owner about any
  rule written for the previous phase. Never carry an old rule into new work silently.
- **Downloads, purchases, posts, messages: ask the owner first.** Secrets (tokens) are created and
  stored by the owner; never ask for their values.
- The owner is **Lucas** (GitHub `mitsevox`).

## Build and verify

```
python configure.py        # downloads compilers and tools (wibo on Linux)
ninja                      # must end with: build/<VERSION>/main.dol: OK
ninja build/<VERSION>/report.json     # objdiff scores
```
`orig/<VERSION>/sys/main.dol` must exist first. In the cloud run `tools/cloud/setup.sh` (needs the
owner's `MVP_BUILD_TOKEN` secret). `<VERSION>` is the disc's game ID, still `GAMEID` until discovery.

## Working with the owner

- Plain, friendly English; short. Say what each code area does in the game, not just file names.
- Concept first, then the owner's green light, then small chunks.
- Numbers exactly as measured (report.json and the accuracy log), side by side. Estimates come from
  measured pace, never gut feel.
- Park anything that needs the owner's decision in `agents/state.md`.

## Current phase: scaffold (from 2026-09-29)

Next: discovery (`docs/discovery.md`), then the pilot (`agents/pass.md` "Loop 4").
