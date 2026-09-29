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

SN's runtime (thread "Libc, libgcc and SN runtime", 2026-09-29) comes from the same repo and is
compiled with the ProDG rule (`docs/compiler.md`). Measured before importing, with every
ProDG-built runtime unit of emoose/re4 compiled by our ngccc 3.9.3 (v1.76) and searched for with
relocations masked: libgcc, most of newlib's libc and the libm (fdlibm) units MVP links match as
they are; SN's debug stub (`ppcdown`, `fileserver`) and `sndvd` match only in part (MVP has libsn
62, re4 60). Landed so far: libgcc's 64-bit shift, divide and remainder helpers and `_exit`
(`src/libgcc/`, 0x80413940..0x80414E54 and the four `__clz_tab` copies in `.sdata2`
0x806F0880..0x806F0C80), `__pure_virtual` (0x804144B8; `inhibit_libc` leaves only its call to
`__terminate`) and the crt's `__main`/`__do_global_ctors` (0x80413878, built with `-G 0` so its
`initialized` flag is plain `.bss` at 0x806C37F0). `_eh` (0x80414E54..0x80414F30, with
`__terminate_func` in `.data` 0x8062F914) is still asm: re4's object keeps 4 of its 13 functions
here, but its 0x28-byte `.bss` does not fit the 0x1C bytes MVP leaves before `ai.c`'s.

SN's libsn itself (`src/libsn/`): `FSasync` (the debugger host file server's asynchronous reads
over EXI channel 2, 0x80406DCC..0x80407604, 13 functions, with its `.data` and `.bss`) matches
as re4 has it, names from RE4's own symbol file. The functions it calls in `proview` are named in
`linked_names.tsv`. `proview`, `tealeaf`, `ppcdown`, `fileserver` and the startup code were
hand-written assembly in SN's library (re4 keeps them as whole-function `asm()` bodies), so they
stay as asm here, which is their original form. Still to check: `dummy` (its second `.data` word
is unproven), `sndvd` (5 of 11 functions match, libsn 62 differs) and `builtin-delete`.

The C library (`src/libc/`) is newlib 1.8.2 with SN's changes. In MVP's copy its objects are not
all laid out as in re4's: some of re4's files have their functions spread over two places in MVP
(`fopen`'s `_sn_sinit` and `_cleanup_r`, `locale`'s `setlocale` and `localeconv`), and MVP links
C library functions re4 lacks between them. So only files whose kept functions sit together in MVP
become units; the others stay asm until MVP's own file layout is worked out. Landed: 36 units with
no data of their own (string and memory functions, stdio internals, the printf and scanf entry
points, `strtol`/`strtoul`, `qsort`, `exit`, `atof`/`atoi`, `isdigit`/`isspace`, `_close_r`,
`_fstat_r`), 0x80407D1C..0x8040FCA0 with gaps. Functions and data they reach by name (`_impure_ptr`,
`_ctype_`, `errno`, `vfprintf`, `strtod`, the `_r` system calls and others) are named in
`linked_names.tsv`. Then five with data, placed with `tools/research/datacheck.py` (all TRUSTED):
the scanf core `__svfscanf`/`__sccl` (`vfscanf`), `_mbtowc_r` with its JIS tables, SN's `strtod`
(Tcl's `strtod.c` with float tables, `strtod2`), `ungetc` and `tolower` (0x8043EFA4, linked
among SN's system calls). As with libm, objdiff counts GCC's unnamed literal pools as unmatched
data. Then SN's `vfprintf` (7 functions, 0x8040BAA0..0x8040D69C). datacheck placed its `.rodata`
from the two named tables only (at +0x40); the whole 0xD0-byte section equals the DOL at
0x8060EDA8 and all 83 relocations into it resolve there, so the unit owns 0x8060EDA8..0x8060EE78.
Then `vfiprintf` (the same file built with `INTEGER_ONLY`, 0x8040D69C..0x8040EAA0). MVP's SN libc
(libsn v62) has one function re4's (v60) lacks: newlib's `vfiprintf` wrapper, between `_vfwrite`
and `_vfiprintf_r`, added to `vfprintf.c` under `INTEGER_ONLY`. Its data are byte-identical to
vfprintf's, so datacheck anchored `.sdata` and `.bss` on vfprintf's copy; the addresses come from
the DOL's own references instead (`.sdata` 0x806EEB44, `.bss` 0x806C3770, `.rodata`
0x8060EE78..0x8060EEE4), and `main.dol: OK` proves them.
Then `math_support` (0x8040ECE8..0x8040F5FC): fdlibm's `floor`, `fmod`, `log` and `log10` under
`sn_` names, which vfprintf calls. The code folds every constant into `.rodata`, but GCC still
emits the `static const` doubles into `.sdata2`, and MVP keeps them (0x806EFC60..0x806EFCE0).
There log10 has only its own three constants and shares `two54` and `zero` with log, so SN's file
was one source: `log10` is written out in `math_support.c` instead of re4's include of
`e_log10.c`, which duplicated the two.
Then `locale` (`_localeconv_r` and `localeconv` at 0x8040ECB8; `.rodata` 0x8060EEE4..0x8060EF38,
`.sdata` 0x806EEB4C..0x806EEB60, compared with the DOL by hand since datacheck anchors only
`lconv`). As in re4, `_setlocale_r` and `setlocale` are not linked, but MVP keeps their two static
`lc_ctype` buffers in `.sdata`.
Still asm: `fopen` and the functions re4 has no source for. `fopen` is one file in MVP
(0x80407E10..0x804081A4): `snstd`, `_sn_sinit`, then SN's `__sfp` (0x144) and `_fopen_r` (0xEC),
which re4 has no source for, a real `fopen` wrapper (re4's is an error stub) and `_cleanup_r`.

The math library (`src/libm/`) is newlib 1.8.2's fdlibm, each file compiled as C++ through a
one-line wrapper with re4's flags (`configure.py` `cflags_libm`). 28 units, 0x8040FF1C..0x80413878
with gaps: `log`, `sqrt`, `cos`, `fabs`, `floor`, the float functions (`acosf`, `asinf`, `atan2f`,
`sqrtf`, `atanf`, `cosf`, `fabsf`, `floorf`, `sinf`, `tanf`), the kernels and pi/2 reductions, and
`scalbn`/`copysign` in both widths. Their literal pools (`.sdata`) and tables (`.sdata2`:
`two_over_pi`, `npio2_hw`, `PIo2` and others) were placed with `tools/research/datacheck.py`, all
TRUSTED. objdiff counts the `.sdata` literal pools as unmatched data because GCC gives them no
symbols to pair; the bytes are proven by `main.dol: OK`. Five functions in this range have no re4
source (0x8040FCA0, 0x804103C0, 0x80410790, 0x80410F08 and 0x80411490; probably other fdlibm
functions such as `sin` and the `ceil` pair, not checked) and stay asm with their data.

Measured before importing (all 123 SDK units compiled from emoose/re4 with GC/1.2.5n and compared
with relocations masked, `tools/research/libmatch.py`): walking the units in our link order, 166 KB
of the SDK's 169 KB match byte for byte as they are. The six stretches that did not were all
explained (checked with `tools/research/sdkcheck.py`):
- the two `GXFifo` gather-pipe functions, NONMATCHING in re4, match once `reg &= 0xFBFFFFFF` is
  written as `SET_REG_FIELD(line, reg, 1, 26, 0)`;
- the other five are whole members re4 leaves out of its link, which match as they are:
  `amcstubs` (`AmcExi2Stubs`, before `ar`), `CARDRename` (with `-char signed`, before `CARDNet`),
  `CARDStatEx` (before `db`) and `OSMessage` (before `OSMemory`), the last three from dolsdk2004.

Nintendo's VM library has no public source. `vm.a` (0x8043D960..0x8043E344, `src/dolphin/vm/`)
is decompiled here: it was built with a newer CodeWarrior than the rest of the SDK (its prologues
save LR after the stack update; GC/1.3 to 2.7 give identical code, the build uses 2.0), and its
declarations are in a reconstructed `src/dolphin/__vm.h`. The reference builds name 13 of its 21
functions; the rest are read from the code, all logged in `config/GV4E69/linked_names.tsv`.
`vmbase.a` (0x8043F058..0x8043FDB8, after libgcc, `src/dolphin/vmbase/VMBase.c`), the MMU layer
under it, is decompiled the same way with the same compiler: page table, lock and reverse tables,
and the patched DSI/ISI exception vectors that turn page faults into calls to `vm.a`. The
reference builds name 15 of its 31 functions; four are asm functions (TLB invalidate, the
real-mode SDR1 switch and the two exception entry stubs).

Two things the VM files showed about this compiler:
- `.sdata` statics come out in declaration order but `.sbss` ones in reverse, so a static's
  place in the DOL fixes its declaration order.
- The arena setup of the two lookup tables matches only as `arenaLo = ptr = OSGetArenaLo();`
  with a separate `u8*` for the new arena start, and a byte-offset clearing loop. Plainer forms
  give a 16x unroll or a different register choice.
- vmbase adds: variables declared in a block of their own get different callee-saved registers
  than the same variables at function scope; CodeWarrior has no `__icbi` intrinsic (inline asm
  `isync; icbi` does it); and an asm function cannot take `label@ha`, so labels other code
  patches in are `entry` symbols.

How the SDK sits in our build:
- **Link order** is library by library, alphabetically (ai, amcstubs, ar, ax, base, card, db, dsp, dvd, exi,
  gx, mtx, os, pad, si, vi, then the VM library and DebuggerDriver), each archive in its own member
  order. Not RE4's order.
- **Dead stripping.** SN's linker dropped every SDK function and global the game does not use.
  `tools/strip_unused.py` (adapted from RE4) removes the same symbols from our objects after each
  compile, keeping what `symbols.txt` names inside the unit's ranges.
- **Whole archives.** Members the game never calls are still linked, with every function stripped
  but their static data kept: the `.sdata2` block holds the `0.5`/`3.0` square-root constants of
  `mtxstack`, `psmtx`, `vec` and others, and `OSFatal`'s constants, with no code left. Those units
  get data-only splits.
- **Data layout.** Each unit's data sections are placed by chaining the units in link order,
  simulating the stripping of each, and are kept only when checked: every relocation from the
  unit's matched code must land on the right object, or, with no such relocation, the unit's own
  non-zero bytes must match the DOL. A section nothing refers to (unreferenced statics, often
  `.bss`) is accepted when it fills the space between two checked neighbours exactly; a data-only
  unit (`DSPCode`) when another unit's reference to it resolves there. Units that fail stay asm
  until their layout is proven. `tools/research/datacheck.py OBJ UNIT` runs the same checks on one
  object (anchors from its code and pointers, content, exact fits) and prints each section's
  range with TRUSTED or UNTRUSTED and the reason. Run over the built SDK objects it agrees with
  144 of the 145 ranges it places, and marks the one it gets wrong (`dsp_task` `.sbss`) UNTRUSTED.
- **Small objects the linker keeps.** Stripping removes whole 8-byte granules, so an unreferenced
  4-byte global is not removed. When its pointers are filled in the DOL it is kept outright
  (`dvdFatal`'s `Japanese` and `English`), and its relocations must stay in our object.
- **Shift-JIS.** `dvdFatal.c` holds a Japanese string; SDK units compile through `sjiswrap`, so
  the string's bytes match. A plain compile gives UTF-8 bytes and the wrong size.
- **Linker-defined symbols.** The SDK reads `_stack_addr`, `_stack_end`, `__ArenaLo` and
  `__ArenaHi`, which the link script defines (`config/GV4E69/ldscript.tpl`). With those defined,
  ngcld reported the other undefined symbols only as exit code 99 with no message (seen
  2026-09-29). Link with those lines removed to see the errors.
- **Names outside the imported units.** Library functions the SDK calls that are still asm (libc,
  the CodeWarrior helpers `__shr2i` and friends in SN's runtime, gap functions) are named from the
  SDK's own references, logged in `config/GV4E69/linked_names.tsv`.

## EA SND audio (from 2026-09-29)

Where it is: `.text` 0x803A4214 (after the VP6 codec) to about 0x803B9794, where the Csis library
(`libcsisgcz.a(csis.o)` in the FIFA 2005 and UEFA maps) begins; `sndgs`, the library's global state,
is at 0x8069C87C. The SND objects are in `config/GV4E69/filemap.tsv` (`libsndgcz.a`).

Source: dbalatoni13/nfsmw (`CREDITS.md`), compiled with ProDG 3.9.3 and nfsmw's SND flags (`-O2 -G0
-fno-strength-reduce -fno-strict-aliasing -ffast-math -mps-float`, as C++); they reproduce MVP's
code unchanged. Compared with relocated fields masked, about 110 of their functions match code in
MVP once the struct below is fixed; 97 of them (16 files) are linked as units so far.

- **MVP's SND is older.** `SNDGLOBALSTATE` lacks two hooks nfsmw has (`aemsstopmodulebanks`,
  `aemsstreampurge`), so every field from `chan` on sits 8 bytes lower. The evidence is in
  `src/snd/cmn/sndcmn.h`. MVP also has no `SNDAEMSI_stopmodulebanks` (removed from `saems.c`);
  with that and the struct fix, all 74 of MVP's `saems` functions and its tables match. MVP's
  `SNDCTRL_getprogvol` and `SNDSTRM_getprogvol` return the volume scaled to 0..127, where nfsmw's
  return the raw float (a `* 127.0f` added in `sgetpvol.c` and `sstgetpv.c`).
- **Look-alikes.** Masked byte matching alone is not proof for small wrappers: nfsmw's
  `SNDCTRL_lowpass`, `SNDmemlimits` and `SNDmemlargestunused` match functions in MVP whose callees
  are other functions (the last two are Csis's `Class::Release` and a neighbour). A unit is added
  only when the functions it calls and the functions calling it agree with the source, checked
  with `tools/research/relocnames.py` and the reference-build names.
- **Units.** Only whole files that match in place are linked; `config/GV4E69/imported_units.tsv`
  has one row per file. Next candidates: `saemsamb.c` and `sserver.c` (static initialisers in
  `.ctors`). Parked: `spktplay.c`, where 13 of 14 functions match but MVP's `SNDPKTPLAY_create` is
  0xF4 bytes to nfsmw's 0xE8 (the same stores, but a different block order and one fewer saved
  register; about 20 source shapes tried, none reproduce it). `SNDAEMSI_timerupdate`
  (`saemstimupdt.c`) looks hand-written in MVP (`mflr` inside the loop, `stmw r20`).
