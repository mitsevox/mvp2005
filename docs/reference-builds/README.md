# Reference builds (discovery step 6)

Status 2026-09-29: surveyed and measured; the owner accepted the list.
Updated 2026-09-30: the owner's GameCube disc is now checked and its retained
rendering debug metadata exported (`../disc-inspection.md`). Other disc checks
remain open. The owner asked to gather every available resource
before going further (existing decomps, DWARF, ELF, STABS, debugging.games, related titles). This
page ranks what exists, says what each item gives MVP, and lists the discs worth dumping from the
owner's own copies.

The public survey found no full-game MVP map or debug build. The owner's MVP
2005 GameCube disc retains symbols and DWARF1 in `libmatd.a`, covering 25
rendering objects and their shared declarations, not the whole executable.
MVP's EA library
block is well covered: 15 GameCube builds from EA studios with symbols were compared against MVP
code, and together they name 960 of the 1,210 functions in the EA graphics, audio and video
libraries, 283 of 398 in EA's system libraries, and most of the SDK and C library. MVP's own
baseball code (16,031 functions) gets essentially nothing from them. For the game code, the best
remaining hope is map files on MVP's own PS2 discs, since EA's PS2 discs of the same years often
shipped them (list below).

Nothing from another game is in this repo. The reference files were read in a scratch folder of a
cloud session. debugging.games asks researchers to delete, within 24 hours, files for games they
do not own (its LEGAL.txt); that applies to the scratch copies, not to anything committed.

## What we want from one

MVP's main executable is stripped, but its disc's rendering archives and
runtime model objects retain symbols (`../disc-inspection.md`). A related
build helps when it shares code with us and
carries names: a symbol table (function names), DWARF (names, types, struct layouts, file order,
inlines) or a link map (names, object files and link order).

## How overlap was measured

`tools/research/refmatch.py` reduces every function to a fingerprint that ignores linked
addresses (branch targets and the 16-bit immediates of loads, stores, `addi`, `addis` and `lis` are
masked), then looks up each reference function among MVP's functions from
`config/GV4E69/symbols.txt`. A match counts only when the fingerprint is unique on both sides and
the function has at least 12 instructions. The same instructions with only addresses changed is
the same compiled code, so the reference's name applies to MVP's function.

Checks on the method:
- FIFA 2005 and UEFA Champions League (two maps from the same studio) name 1,082 of the same MVP
  functions and never disagree.
- The seven builds with mangled names agree on 1,686 of 1,825 shared addresses. Most of the rest
  are SPCH functions named once as C and once as C++; a few are chance collisions in game code.
- So hits inside MVP's game code (about 100 across all builds) are mostly look-alikes and are not
  counted as coverage. Hits in the library block are reliable.

Region bounds are from `docs/sdk.md`. "EA libs" is EAGL, SND, SPCH and the VP6, MAD and RCMP
codecs (0x8038C000..0x803EC000); "EA sys" is file, memory card and system (0x803EC000..0x80404000).
Each MVP count is functions of 12 instructions or more.

| Build (GameCube) | EA libs /1,210 | EA sys /398 | SN, libc /186 | SDK /606 |
|---|---|---|---|---|
| GoldenEye: Rogue Agent | 651 | 191 | 114 | 519 |
| Medal of Honor: European Assault | 636 | 246 | 114 | 550 |
| NFS Most Wanted | 595 | 88 | 104 | 537 |
| UEFA Champions League 2004-2005 | 571 | 151 | 102 | 388 |
| Medal of Honor: Rising Sun | 456 | 157 | 103 | 471 |
| NFS Underground | 416 | 92 | 91 | 456 |
| FIFA Soccer 2005 | 415 | 160 | 109 | 387 |
| Harry Potter and the Goblet of Fire | 387 | 97 | 113 | 534 |
| NASCAR 2005: Chase for the Cup | 374 | 9 | 68 | 452 |
| Freedom Fighters | 6 | 0 | 76 | 375 |
| The Sims 2 | 2 | 1 | 102 | 548 |
| FIFA Soccer 2004, FIFA 2003, MoH Frontline, 007 Agent Under Fire | 0 | 0 | 0 to 1 | 248 to 342 |
| **All builds together** | **960** | **283** | **127** | **562** |

The last group were built with CodeWarrior (they carry `.mwcats` sections), so only the SDK lines
up. MVP's `gamelib` block (393 functions, animlib and friends) gets 17 at most; no reference
build carries gamelib.

## Ranked list

"Has" is what the file carries, checked by reading its sections. Sizes are the debugging.games
archives.

### Tier 1: use these for the EA library block

1. **UEFA Champions League 2004-2005 (GUCP69) and FIFA Soccer 2005 (GF5E69), GameCube, EA Canada,
   2004.** Has: stripped `fifa_z.elf` plus an SN linker map `fifa_z.map` (object file, address,
   size and demangled name for every function; built as `gc-sn-release`, so SN ProDG like MVP).
   Same studio, same year, same toolchain. The map gives the library objects in link order, which
   is exactly what step 7 (the file map) needs for the library block: `libsndgc` (180 MVP
   functions named from UEFA), `libeaglSN` (171), `libvp6decode` (127), `librealfile` (52),
   `librealmemcard` (39), `librealsystem` (26), `librcmp*` (53), `libspch` (21), `librealshape`
   (18), `librealmath` (14), `librealfont` (10), `libcsisgc`, `librealcodec`, `librealstd`. Package
   versions in the paths: eaglcore 5.03.04, eaglanim 5.03.06, spch 3.16.00, realmemcard
   2.08.06/2.10.02, realmath 0.5.2. UEFA is the later build and covers the video codecs better, so
   read it first; FIFA 2005 adds little on top. No types (no DWARF).
2. **GoldenEye: Rogue Agent (GOYE69) and Medal of Honor: European Assault (GONE69), GameCube, EA
   Los Angeles, 2004-2005.** Has: full DWARF 1 plus symbol table (`GE2RDVD.ELF`, `MOH4RDVD.ELF`).
   The two highest overlaps with MVP, and they bring types and struct layouts for EAGL, SND, SPCH
   and the codecs, which the FIFA maps cannot. MoH EA is also the best source for EA's system
   libraries (246 of 398).
3. **NFS Most Wanted (GOWE69), GameCube, EA Black Box, 2005.** Has: full DWARF plus symbol table
   (`NFSMWRELEASE.ELF`, 105 MB). Its public decomp (github.com/dbalatoni13/nfsmw) has already
   rebuilt EA's `snd/9` and `spch` source trees plus `realcore`, `realmemcard`, `rcmp`, `csis` and
   `LibSN` under `src/Speed/Indep/Libs/`, and uses ProDG 3.9.3 like MVP. That is matched C for
   libraries MVP also links (versions may differ; check per file, and check the repo's licence
   before copying anything).

   **What the nfsmw decomp has for us (checked 2026-09-29 against its repo, commit of that day).**
   Of the 1,360 MVP functions its build names, the EA-library ones with C in its `src/` are:
   | nfsmw state | MVP functions | bytes |
   |---|---|---|
   | SND units marked matching for GOWE69 (29 files: saems, sbplay, smemman...) | 60 | 12,804 |
   | C written, unit not yet matching (SND 22, realmemcard 7, rcmp 5, realcore 4, VP6 2, other SND 4) | 44 | 11,832 |
   | Named only, no C yet (SND ~196, VP6 129, SPCH and others ~231, realmemcard 32, realcore 29, rcmp 41) | ~660 | ~190,000 |
   The rest of the overlap is Dolphin SDK code, which RE4 and dolsdk2004 cover. So nfsmw gives about
   24 KB of EA library C to try, 13 KB of it already byte-matched in nfsmw, all of that in SND. Its versions may differ from MVP's (its SND is `snd/9`, MVP's SND is V9.02.04). Licence:
   CC0. Other decomps checked the same way: nfsug has no matched units (5 source files); Sims2DECOMP
   shares almost no EA library code with MVP; the SSX decomps are PS2, so no byte reuse. No decomp
   has EAGL, VP6, gamelib or animlib C.

### Tier 2: more of the same, useful as cross-checks

4. **Medal of Honor: Rising Sun (GR8E69)**: symbol table and a little DWARF; 456 EA-lib names.
5. **NFS Underground (GNDE69)**: DWARF plus symbols; 416. A public decomp exists
   (github.com/dbalatoni13/nfsug). NFS Underground 2 (GUYE69) has DWARF too; its archive would not
   unpack here.
6. **Harry Potter and the Goblet of Fire (GH4E69)**: DWARF (250 MB of it) plus symbols; 387.
7. **NASCAR 2005 (GN4E69), EA Tiburon**: DWARF plus symbols; 374.

### Tier 3: compiler know-how, not names

8. **The Sims 2 (G4ZE69), EA, 2005.** Has: release and debug SN maps plus the ELF. Shares
   little code with MVP, but its public decomp (github.com/natebag/Sims2DECOMP) matches C++ with
   SN ProDG GCC 2.95.3 at `-O2`, the same compiler family. Useful for GCC 2.95 matching patterns.
   Not checked for quality.

9. **Resident Evil 4 decomp (github.com/emoose/re4, GameCube, Capcom), 100% matched.** Found by
   the "Import SDK and library code" thread. Same toolchain as MVP (ProDG 3.9.3, SN `ngcld`,
   dolsdk2004 at revision 1), and its `GXInit.c` carries MVP's exact GX build string. Matched
   newlib 1.8.2 libc and libm, libgcc, SN's libsn (v60; MVP has v62) and the SN debug stub. The
   best source for MVP's runtime block; no EA code. Tools and docs CC0; the reconstructed source
   is marked as the owners' IP.

### Tier 4: baseball ancestry and other platforms (names only, no code overlap possible)

10. **Triple Play Baseball (PS2, SLUS-20168), EA Canada, 2001.** MVP's direct predecessor. Has:
   unstripped ELF with `.mdebug` and a symbol table (8,765 functions). It shares source file names
   with MVP (`ball.cpp`, `bat.cpp`, `player.cpp`, `stadium.cpp`, `scene.cpp`, `rendercontext.cpp`,
   EAGL's `FnPoseBlender.h`), but none of MVP's 126 known class names appear in it, and its game
   code is C-style (`BALL_InitPhysics`, `PITCHER_SelectPitch`). Useful as background on how EA
   Canada's baseball code was organised, not for names. MIPS, so no code comparison.
11. **NCAA March Madness 2004 and 06 (PS2), EA Canada.** Has: map files on the disc (`NCAA.MAP`,
    `MM2006F.MAP`), and March Madness 06 a debug ELF (`.mdebug`, `.stab`). Heavy EAGL, SND and SPCH
    names; no MVP class names. Shows that EA Canada's PS2 discs of this era shipped map files.
12. **NBA Live 06 demo (Xbox 360), EA Canada, 2005.** Has: PDB plus map. PDB types for EAGL, SPCH,
    VP6 and realmemcard of the same year; a later platform, so layouts need checking.
13. **Tiger Woods PGA Tour 06 (PS2 map, Xbox beta PDB), FIFA 2003 (Xbox beta map, PS2 ELF), NBA
    Street (PS2 ELF).** EA library names on other platforms; low value for MVP.

### Not found

- Public full-game symbols, map or debug build of MVP 2003, 2004 or 2005 (any platform), MVP 06 or MVP 07 NCAA
  Baseball. Checked: debugging.games (all platforms), retroreversing.com's GameCube and PS2 lists,
  the mariomadproductions gist, the PSP symbol list at psp-re.github.io, Hidden Palace.
- Public decomps of any EA Canada title, or public EAGL source. SSX, SSX Tricky and SSX 3 have PS2
  decomps (github.com/ssxdecomp); none names a symbol source, and none was checked for shared code.
- MVP prototypes: Hidden Palace has two MVP Baseball 2003 prototypes (Xbox, Dec 15 2002, with a
  debug `.xbe`; PS2, same day, with a debug menu). No symbol files are mentioned. Not downloaded:
  they are full discs.

## Search log (what was covered, where it came up empty)

Add rows here as new sources are checked.

| Where | What was searched | Result |
|---|---|---|
| debugging.games | Full listings of GameCube, PS2, Xbox, Xbox 360, Wii, PSP, Windows, Other, Unmatched; CHANGELOG and WANTED lists for "MVP", "Triple Play", "baseball" | EA builds in the ranked list; no MVP title; only baseball entries are Triple Play (PS2) and non-EA games |
| retroreversing.com | GameCube debug symbols page, PS2 unstripped page, Xbox page | Same EA builds as above; no MVP |
| gist by mariomadproductions | "Games with debug symbols" list | No EA Sports or EA Canada title |
| psp-re.github.io | PSP symbol list | No MVP Baseball (PSP) |
| hiddenpalace.org | GameCube and Xbox prototype lists, MVP pages | Two MVP 2003 prototypes (Xbox, PS2), no symbol files mentioned; no MVP 2004/2005. The Xbox list may have been read only partly (up to about "F") |
| GitHub, web search | Decomps of EA titles 2002-2007 | nfsmw, nfsug, Sims2DECOMP, ssxdecomp (SSX, Tricky, SSX 3), Burnout Paradise, Fight Night Round 3 PSP; none for FIFA, NHL, NBA Live, NBA Street, Def Jam, MVP, NCAA Baseball; no public EAGL source |
| tcrf.net | MVP Baseball 2005 (GameCube) page | Page blocked our fetch (403); snippet quotes `version.txt` "TP GC Build Number 2004-12-24_1"; verified directly from the owner's disc on 2026-09-30 |
| mvpmods.com | Tools and editors | Modding tools (BIG extractor, roster and stadium editors); no symbols or source |

Gaps not searched: EA Sports demo discs (Official Xbox Magazine, GameCube interactive demo discs,
EA Sports bonus discs) that might hold MVP builds; Discord servers of the decomp and modding
scenes; archive.org beyond the prototype items; NHL, NBA Live and FIFA Street GameCube builds
(none on debugging.games, not searched elsewhere); the SSX decomps checked for shared code.

## Discs worth dumping (the owner's own copies)

Retail discs are never downloaded by us. These are the checks, most promising first. Each is a
look at the disc's file list first; copy out only symbol, map or executable files.

1. **MVP Baseball 2005, GameCube (checked 2026-09-30).** `mvp.elf` is stripped;
   `libmatd.a` has 25 objects with symbols and DWARF1, `libmatz.a` has the
   corresponding symbols without debug, and 15 runtime model objects retain
   symbols. Full retained-debug metadata is in `config/GV4E69/disc-debug/`;
   see `../disc-inspection.md` for coverage and asset-container limitations.
   No full-main-executable map found.
2. **MVP Baseball 2005, PS2 (USA).** Look for `*.MAP`, `MAPFILE.TXT` or an unstripped ELF at the
   disc root. EA Canada's March Madness 2004 and 06 and EA's Tiger Woods 06 shipped maps on PS2. A
   map here would name MVP's game code, which nothing else does.
3. **MVP Baseball 2004, PS2, and MVP 2003, PS2.** Same check, older versions of the same code.
4. **MVP 06 NCAA Baseball and MVP 07 NCAA Baseball, PS2.** Same check, later versions.
5. **MVP Baseball 2005, Xbox and PC.** Look for `.map` or `.pdb` next to the `.xbe` or `.exe`.
6. **MVP Baseball (PSP, 2005).** Look for unstripped `.prx` modules.
7. **MVP Baseball 2004, GameCube.** An older build of the same source (MVP 2005's own paths
   still read `C:/mvp2004/`) with the same toolchain. Worth a file list for the same reason as
   item 1; its code alone carries no names.

## Getting the reference files again

The GameCube builds above are on debugging.games under `GameCube/` (NFS titles under
`GameCube/Need for Speed/`). The per-build name lists that `refmatch.py --tsv` wrote are kept
outside the repo, in the project's shared folder, for the file-map work.
