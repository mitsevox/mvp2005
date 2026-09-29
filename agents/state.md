# State (current facts only)

Updated 2026-09-29.

**Phase: scaffold.** The repo is dtk-template plus tw2004's CI and cloud setup and the process docs
(`agents/pass.md`, `agents/brief.md`, `docs/discovery.md`). Nothing builds yet: no `main.dol`, and the
game ID is still the template's `GAMEID`.

**Waiting on the owner:** the private build container `mitsevox/mvp2005-build` with MVP's
`main.dol`, Read access for this repo on its package, and the `MVP_BUILD_TOKEN` cloud secret
(`tools/cloud/README.md`).

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

- Game ID and region of the disc.
- Carried from tw2004, confirm for this project: no Co-Authored-By or AI footer in commits and PRs;
  agents never delete files.
- Loop 2 thresholds (proposed: names 3%, comments 5%) and the sample after the pilot (proposed 10%).
- Whether loop 2 reviewers use a different model from the lanes.
