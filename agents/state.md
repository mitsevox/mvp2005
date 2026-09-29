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
  the linker rewrote the register: that is SN's linker, not CodeWarrior's. **Resolved
  2026-09-29:** the build now links with SN's `ngcld` (owner: use what EA used), which keeps every
  relocation and still gives the exact DOL. The earlier relocation blocks for mwld are gone.
- `_rom_copy_info` missing: expected, it is CodeWarrior's runtime table and this DOL was not
  linked by CodeWarrior.
- The entry point (0x80003100) is SN's startup code, not the SDK's `__start`; it is named
  `__start` only because the link script's ENTRY needs a name.

**Discovery step 3 (compiler), 2026-09-29:** settled from the binary: game code is C++ from SN
ProDG (GCC 2.95), linked by SN's linker, with Nintendo's CodeWarrior-built SDK libraries.
The build links with SN's `ngcld`. Game code flags, from two exact matches: `-O2 -G0 -ffloat-store
-fno-strength-reduce`. ProDG 3.5 to 3.9.3 compile identically on everything tried, so 3.9.3 is the
default. Evidence: `docs/compiler.md`.

**Discovery step 4 (SDK and middleware), 2026-09-29:** the Dolphin SDK is the 2004 SDK with Patch 1
(OS May 21 2004); 12 of 13 version strings are identical to the public `doldecomp/dolsdk2004`, GX's
build time differs by 30 seconds. The C library is SN's newlib-style one; SN's debug stub replaces
MetroTRK; no MSL, no MusyX. EA's own libraries (EAGL, gamelib/animlib, AV/VP6/MAD video, file and
memory card, SND/SPCH audio) have no public source. Game code sits on both sides of the libraries.
Map and evidence: `docs/sdk.md`.

**Discovery step 5 (leaked names), 2026-09-29:** no RTTI or symbols, but three strong T1 sources.
89 EA source paths (asserts). EA's own type system: a class's type ID is the djb2 hash of its name,
so 123 classes get their vtable, constructor and getters named from one table
(`tools/research/typeids.py`). A reflection system registers about 1,800 members by name, with
offsets. Evidence: `docs/names.md`.

**Discovery step 6 (reference builds), 2026-09-29:** the owner asked to gather every resource
first, which settled the NFS MW question. 15 EA GameCube builds with symbols were measured against
MVP (`tools/research/refmatch.py`): together they name 960 of 1,210 EA library functions (EAGL,
SND, SPCH, codecs) and 283 of 398 EA system functions; MVP's game code gets nothing. The UEFA and
FIFA 2005 SN maps give the library objects in link order for step 7. No MVP symbols exist in
public. Ranked list and discs to check: `docs/reference-builds/README.md`.

**Discovery step 7 (file map), 2026-09-29:** evidence map only (`docs/filemap.md`,
`config/GV4E69/filemap.tsv`). 87 exact file ends (GCC static-init pairs), 65 files named by
`__FILE__` paths, 215 library objects from the FIFA/UEFA SN maps; 8.6% of game code and 44% of the
EA library block placed. Soft signals (constant pools, call and data locality, classes) were
measured against the maps and are too weak to place files, so matching places the rest.

**Discovery step 8 (pilot pick), 2026-09-29:** the owner picked `geomgroup.cpp` + `geomlib.cpp`
(geometry library; window 0x802E2C50..0x802E4DFC between `geomcone.cpp` and `geommesh.cpp`, at most
23 functions, 0x1DE0 bytes). Discovery is done.

**Library import (from 2026-09-29, thread "Import SDK and library code"):** the owner approved
bringing in the Dolphin SDK and SN runtime from emoose/re4 and doldecomp/dolsdk2004 (`CREDITS.md`,
`docs/sdk.md` "Importing"). This work owns the splits in `.text` 0x80403F08..0x8043F058 and the data
of the units it adds; the file map (step 7) leaves those to it. Units landed so far, with every
range they own:
- `dolphin/base/PPCArch.c`: `.text` 0x8041A5A4..0x8041A6C4 (no data).
- 91 more SDK units (ai, amcstubs, ar, ax, card, db, dsp, dvd, exi, gx, mtx, os, pad, si, vi, odemustubs): every
  `dolphin/*` entry in `config/GV4E69/splits.txt`, in `.text` 0x80414F30..0x8043D960 plus
  DebuggerDriver, and the data ranges listed there. Listed with evidence in `imported_units.tsv`.
  Library functions they call that are still asm (libc, the CodeWarrior helpers in SN's runtime,
  gap functions) are named in `linked_names.tsv`.
- Nintendo's VM library `vm.a` (`dolphin/vm/`, `.text` 0x8043D960..0x8043E344): no public
  source, decompiled here and built with CodeWarrior GC/2.0 (`configure.py`). Names: 13 from the
  reference builds, the rest read from the code, each logged in `linked_names.tsv`.
- Nintendo's `vmbase.a` (`dolphin/vmbase/VMBase.c`, `.text` 0x8043F058..0x8043FDB8, `.sbss`
  0x806EF970..0x806EF98C): the MMU layer under `vm.a`, decompiled the same way (GC/2.0). Names: 15
  of 31 functions from the reference builds, the rest and the 7 statics read from the code.
- Still asm: the 8 zero bytes after `vmbase.a` (0x8043FDB8), and the two empty functions at 0x8043E344/0x8043E348 with their pointer pair at 0x80649290.

**Next:** port tw2004's tools the pilot needs (below) and add a ProDG compile rule to
`tools/project.py`, then the pilot.

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

- When game code starts (owner, 2026-09-29): check the owner's discs for symbol or map files, MVP
  2005 PS2 first. `docs/reference-builds/README.md` "Discs worth dumping".
- Carried from tw2004, confirm for this project: no Co-Authored-By or AI footer in commits and PRs;
  agents never delete files.
- Loop 2 thresholds (proposed: names 3%, comments 5%) and the sample after the pilot (proposed 10%).
- Whether loop 2 reviewers use a different model from the lanes.
