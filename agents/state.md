# State (current facts only)

Updated 2026-09-29.

**Phase: scaffold.** The repo is dtk-template plus tw2004's CI and cloud setup and the process docs
(`agents/pass.md`, `agents/brief.md`, `docs/discovery.md`). Target: `GV4E69` (USA), `main.dol` SHA-1
`da6becdbea614d03c4b5eae9f8a0fb08e0a184dd`, 6,837,728 bytes.

**Build container:** `mitsevox/mvp2005-build` holds `main.dol` at its root, with no Dockerfile or
publish workflow yet, so there is no image for CI or `tools/cloud/fetch_orig.py`. It needs tw2004-build's
Dockerfile and workflow, the DOL at `orig/GV4E69/sys/main.dol`, and Read access for this repo on
the package (`tools/cloud/README.md`).

**First strings survey (2026-09-29, strings only):** `<< libsn version %d >>`, "Please See the ProDG
manual", ProDG malloc hooks, 75 `.cpp` source paths under `C:/mvp2004/source/...`, `EAGL::` names.
Likely an SN ProDG C++ build on the MVP 2004 codebase; the code itself is not checked yet.

**First dtk run (2026-09-29, dtk v1.8.3, local copy of the DOL):** analysis stops. It warns "Failed
to locate _rom_copy_info" (CodeWarrior's runtime init table, which a ProDG-linked DOL would not
have), then fails on "Overlapping functions 1:0x804055F0-1:0x8041A5F8 -> 1:0x80405B2C" after control
flow from 0x804055F0 hits the known function 0x80404BDC. Getting dtk through analysis (config hints
or symbols) is discovery step 2's first job.

**Next:** discovery (`docs/discovery.md`), then port tw2004's tools the phase needs (below), then the
pilot.

## Tools to port from tw2004 (in the order the phases need them)

- Discovery: compiler-ID method, `tools/research` string surveys, `tools/prodg/prodgcc.py` if ProDG.
- Matching: `tools/match` (trial, permute, mwccdbg if CodeWarrior, graduate, mkunit, datamap,
  constcheck, doldiff), `tools/agents` (new_agent, merge.py gates, asmgate, status, remain,
  triedledger from `60f149c2`).
- Naming in the same pass: `name.py`, `rename.py`, `lint.py`, `check_batches.py`, `replay_lane.sh`,
  `lanediff.py` (tw2004 latest).
- To write new: `tools/agents/done.py` (the DONE check), the loop 2 reviewer and reconciler.
- Later: the progress page (`tools/dashboard`), the PC runner job.

## Parked decisions (owner)

- Carried from tw2004, confirm for this project: no Co-Authored-By or AI footer in commits and PRs;
  agents never delete files.
- Loop 2 thresholds (proposed: names 3%, comments 5%) and the sample after the pilot (proposed 10%).
- Whether loop 2 reviewers use a different model from the lanes.
