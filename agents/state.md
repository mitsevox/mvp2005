# State (current facts only)

Updated 2026-09-29.

**Phase: scaffold.** The repo is dtk-template plus tw2004's CI and cloud setup and the process docs
(`agents/pass.md`, `agents/brief.md`, `docs/discovery.md`). Target: `GV4E69` (USA), `main.dol` SHA-1
`da6becdbea614d03c4b5eae9f8a0fb08e0a184dd`, 6,837,728 bytes.

**Build container:** `ghcr.io/mitsevox/mvp2005-build:main` (Dockerfile and publish workflow merged
in mvp2005-build PR #1; this repo has Read access). Cloud sessions fetch the DOL with
`bash tools/cloud/setup.sh`, which worked end to end on 2026-09-29.

**First strings survey (2026-09-29, strings only):** `<< libsn version %d >>`, "Please See the ProDG
manual", ProDG malloc hooks, 75 `.cpp` source paths under `C:/mvp2004/source/...`, `EAGL::` names.
Likely an SN ProDG C++ build on the MVP 2004 codebase; the code itself is not checked yet.

**Discovery step 2 done (2026-09-29, dtk v1.8.3):** `ninja` ends with `main.dol: OK` from a cloud
session (`tools/cloud/setup.sh` fetched the DOL with `MVP_BUILD_TOKEN`). 24,158 functions, 9
sections, all still one asm unit each. What it took, and what each fix says about the binary:
- **Overlap at 0x804055F0.** That function is SN Systems' debug stub (hand-written asm; strings
  "snPause() : Stopped.", "Fatal error: Can't patch exc vector"). It ends with a tail branch to the
  SDK's `PPCHalt` (0x8041A5E4), which dtk did not know, so it swallowed 85 KB as one function.
  Fixed by one hint in `symbols.txt`.
- **Unaligned symbol 0x8061EC25.** Code indexes a 3-byte-entry table at 0x8061EC28 from 1, so the
  compiler folded the -3 into the address. Fixed with `add_relocations` (table - 3).
- **Section 7 (0x805A2BC0, 0x1E0) is GCC-style `.ctors` + `.dtors`**: each list starts with
  0xFFFFFFFF and ends with 0, the GNU linker's format, not CodeWarrior's. dtk rejects that under the
  name `.ctors`, so it is split as `.ctordtor` (our name) for now.
- **All small data goes through r13**, `.sdata2` included (`_SDA_BASE_` 0x806F69C0). r2 is loaded
  with 0x807069C0 but no instruction ever uses it as a base. Even Nintendo's GX library (built by
  CodeWarrior, found by dtk's `GXInit` signature) reaches `__GXData` in `.sdata2` through r13, so
  the linker rewrote the register: that is SN's linker, not CodeWarrior's. The CodeWarrior linker
  we rebuild with always encodes `.sdata2` against r2, so `config.yml` blocks relocations into
  `.sdata2` and the r2 loads (raw bytes, still exact), and sets `symbols_known: true` so dtk's GXInit
  signature does not demand those relocations back. **Parked:** before C in `.sdata2` can link,
  the build needs a linker answer (a post-link fixup, a custom section name mwld treats as r13,
  or a GNU/SN-style link step).
- `_rom_copy_info` missing: expected, it is CodeWarrior's runtime table and this DOL was not
  linked by CodeWarrior.
- The entry point (0x80003100) is SN's startup code, not the SDK's `__start`; it is named
  `__start` only because the generated link script needs that entry name.

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
