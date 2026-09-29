# SDK, runtime and middleware (discovery step 4)

Status 2026-09-29: what the game links besides EA's own game code, where each piece sits in `.text`,
and which public decomps cover it. Addresses are approximate (to about 4 KB) unless given exactly;
exact unit boundaries are step 7's job. Every line says what was measured.

## Layout of `.text` (0x800034A0..0x805A2BC0)

Measured by prologue style (GCC `stwu; mflr` vs. CodeWarrior `mflr; stw; stwu`), r13 use (game code
is `-G0`, libraries use small data) and the strings each function references.

| Range (about) | What | Evidence |
|---|---|---|
| 0x800034A0..0x80364000 | EA game code (C++, ProDG, `-G0`) | 63 `.cpp` paths under `C:/mvp2004/source/...` (database, frontend, script, ai, animation, geomlib); no r13 use |
| 0x80364000..0x8038C000 | EA `gamelib` (animlib and friends) | `C:/mvp2004/libraries/gamelib/source/animlib/animation/pathlist.cpp` at 0x80384C88 |
| 0x8038C000..0x803A4000 | EA video: `AV::` stream buffers, VP6 and MAD codecs | "VP6_CODEC_INTERNAL::...", "MAD_CODEC_INTERNAL::...", "AV::AudioStreamBuffer"; uses r13 |
| 0x803A4000..0x803EC000 | EAGL, EA's graphics library (C++) | "EAGL::..." names, `C:/mvp2004/libraries/GC/eagl/`; includes an ELF dynamic loader ("dlopen", ".symtab", "DynamicLoader::GetAddr()") at about 0x803E8000 |
| 0x803EC000..0x80404000 | EA system libraries: memory reports, memory card, file system, async file I/O | "Memcard Work Area", "DefaultFILE_malloc", "ASYNCFILEBUF", "openfile - ILLEGAL OPEN MODE"; GCC prologues, r13 |
| 0x80404000..0x80407000 | SN Systems debug stub (hand-written asm) | "snPause() : Stopped.", "Comms Error", "File server function not available..." |
| 0x80407000..0x80414F30 | C library (SN's, newlib-style), GCC-built | newlib's assert format `assertion "%s" failed: file "%s", line %d`, locale names "C-SJIS"/"C-EUCJP", printf digit tables |
| 0x80414F30..0x8043EB2C | Nintendo Dolphin SDK (CodeWarrior-built) | CodeWarrior prologues; `GXInit`, `OSRegisterVersion`, `PPCHalt` by dtk signature; the version strings below. A few GCC functions with r13 sit inside at about 0x8043DC48..0x8043E344 (not yet identified) |
| 0x8043EB2C..0x80440000 | GCC runtime and small libraries | `__save_gpr`/`__restore_gpr` (0x8043EFC0, 0x8043F00C, by dtk); GCC prologues, r13 |
| 0x80440000..0x805A2BC0 | EA game code again (`-G0`) | Franchise and offseason screens ("urost.bin", "Stat Pumper (Franchise Only)"), `C:/mvp2004/source/common/tourneylogic/offseason/audionames.cpp` at 0x80541F40; no r13 use |

Why game code sits on both sides of the libraries is not known yet. A guess, labelled as one: the
second block may be the files new in MVP 2005 (owner mode, offseason), added later in the link order.

Not located yet: EA's audio libraries. Their version strings are in `.data` ("SNDAUTHOR: Tpbuild,
Thursday 12:06PM Dec 23, 2004, V9.02.04" at 0x806262B4; "SPCHAUTHOR: TLBuild, Wednesday 04:26PM
Oct 13, 2004, V3.18.01" at 0x80624454), but no code references them directly. Step 7 finds them.

Not present: MetroTRK (no TRK code or strings besides the OS's own "commandeered by TRK" message; SN's
debug stub takes its place), CodeWarrior's MSL (the C library is newlib-style), MusyX (EA's own
audio instead). No `.rel` modules found so far (step 1).

## Dolphin SDK: 2004 SDK, Patch 1 (May 21 2004)

The DOL carries 13 version strings, all `(0x2301)`:

| Library | Build string in the DOL | In `doldecomp/dolsdk2004` |
|---|---|---|
| AI, AR, ARQ, AX, CARD, DSP, DVD, EXI, PAD, SI | Apr 5 2004, 04:14..04:15 | identical (`src/*/`) |
| VI | Apr 7 2004 04:13:59 | identical (`src/vi/vi.c`) |
| OS | May 21 2004 09:28:09 | identical at `SDK_REVISION` 1 ("Patch 1", `src/os/OS.c`) |
| GX | Apr 5 2004 04:14:28 | **differs**: the decomp has 04:13:58 and (rev 2) 06:27:12 |

So the SDK is the 2004 SDK with Patch 1, which the public decomp
[doldecomp/dolsdk2004](https://github.com/doldecomp/dolsdk2004) targets (its `Makefile`: "May 21 2004
- 1 (Patch 1)"). Its libraries are built with CodeWarrior, like ours. GX's build time is off by 30
seconds from the decomp's: probably a GX library rebuilt in a patch the decomp did not have. GX code
may still match; checking is the SDK matching work, not discovery.

Plan (per this step): match the SDK from dolsdk2004 first, with its CodeWarrior compiler and flags,
credited in a CREDITS/README as the repo's rules require. Those units are not part of the naming pass.
Nothing has been copied yet.

## SN runtime (libsn, C library, debug stub)

- The entry code at 0x80003100 is SN's startup and prints "<< libsn version %d >>" with version 62.
- The C library is newlib-style (see the table), GCC-built with small data.
- Public source: [emoose/re4](https://github.com/emoose/re4) (Resident Evil 4 GC, finished and byte
  exact) is built with ProDG 3.9.3 and reconstructs parts of libsn (exception handlers, crt0) and
  keeps some SN units as asm. Whether its libsn is version 62 is not checked. Nothing downloaded.

## EA middleware

EAGL, gamelib/animlib, the AV/VP6/MAD video code, the file and memory card libraries and the audio
libraries (SND 9.02.04, SPCH 3.18.01) are EA's own. A GitHub code search for "EAGL::TAR",
"SNDAUTHOR" and "VP6_CODEC_INTERNAL" finds no public source. They get matched and named like the
game code, as EA code. Other EA GameCube decomps that may share them are step 6.

## Importing the libraries (from 2026-09-29)

Owner-approved plan: bring in the SDK and SN runtime from public decomps, in small PRs. Sources:
`CREDITS.md`. Each imported file carries a one-line provenance note; each unit has a row in
`config/GV4E69/imported_units.tsv`. Names are the upstream (Nintendo, SN) names.

Measured before importing (all 123 SDK units compiled from emoose/re4 with GC/1.2.5n and compared
with relocations masked, `tools/research/libmatch.py`): walking the units in our link order, 166 KB
of the SDK's 169 KB match byte for byte as they are. What does not match yet: six stretches, 5.2 KB
in all (the start of `ar`, two functions each of `CARDNet`, `GXAttr` and `OSMemory`, two before
`db`), and Nintendo's VM library (0x8043D960..0x8043E344), which has no public source.

How the SDK sits in our build:
- **Link order** is library by library, alphabetically (ai, ar, ax, base, card, db, dsp, dvd, exi,
  gx, mtx, os, pad, si, vi, then the VM library and DebuggerDriver), each archive in its own member
  order. Not RE4's order.
- **Dead stripping.** SN's linker dropped every SDK function and global the game does not use.
  `tools/strip_unused.py` (adapted from RE4) removes the same symbols from our objects after each
  compile, keeping what `symbols.txt` names inside the unit's ranges.
- **Whole archives.** Members the game never calls are still linked, with every function stripped
  but their static data kept: the `.sdata2` block holds the `0.5`/`3.0` square-root constants of
  `mtxstack`, `psmtx`, `vec` and others, and `OSFatal`'s constants, with no code left. Those units
  get data-only splits.
