# Compiler and language (discovery step 3)

Status 2026-09-29: the compiler family, the linker and the game code's flags are settled from the
binary. The ProDG versions on hand compile identically, so 3.9.3 is the default. Every line below
says what was measured.

## Game code: SN ProDG (GCC 2.95), C++

- **Prologues.** Of 24,158 functions, 17,736 open with `stwu r1,-N(r1); mflr r0` (GCC's order).
  287 open with CodeWarrior's `mflr r0; stw r0,4(r1); stwu r1,-N(r1)`; 283 of those sit in
  0x80403F08..0x8043E728 (the Dolphin SDK), the other 4 are to be looked at. The rest are leaves.
- **C++ with GCC 2.95 vtables.** 19,597 of the 22,167 `blrl` calls load a 16-bit `this` delta with
  `lha` from the vtable and add it before the call. That is GCC 2.95's default vtable layout
  (8-byte entries: delta, index, function; no thunks). CodeWarrior and later GCC do not do this.
- **No RTTI strings** (no GCC 2.95 type names like `21cFEBEASTMomentumLogic`), so probably built
  with `-fno-rtti`. Exceptions still to check.
- **Source paths** name `.cpp` files under `C:/mvp2004/source/...` and `C:/mvp2004/libraries/GC/eagl/`
  (EA's EAGL graphics library). The code base is MVP 2004's.
- **Newest build date in the strings:** "SNDAUTHOR: Tpbuild, Thursday 12:06PM Dec 23, 2004" (audio
  library); the game shipped in early 2005. Any compiler build later than that is ruled out.

## Linker: SN's (ngcld), not CodeWarrior's

- `.ctors`/`.dtors` (DOL section 7) use the GNU format: each list starts with 0xFFFFFFFF and ends
  with 0.
- All small data, `.sdata2` included, is reached through r13. r2 is loaded (0x807069C0) but never
  used as a base. Nintendo's GX library, compiled by CodeWarrior, reaches `__GXData` in `.sdata2`
  through r13 as well, so the linker rewrote its r2 relocations: SN's linker does that, CodeWarrior's
  does not.
- No `_rom_copy_info` (CodeWarrior's startup table). The entry code at 0x80003100 is SN's startup
  (it prints "<< libsn version %d >>" with version 62 and "Waiting for SN Debugger...").
- The SN debug stub (hand-written asm, "snPause() : Stopped.") is linked in at about 0x80404000.

## SDK: Nintendo's CodeWarrior-built libraries

dtk's signatures find `GXInit`, `OSRegisterVersion`, `PPCHalt` and others with CodeWarrior
prologues. They come from the Dolphin SDK's prebuilt libraries: the 2004 SDK with Patch 1, at about
0x80414F30..0x8043EB2C (the CodeWarrior-style prologues before that are SN's debug stub). Details in
`docs/sdk.md` (discovery step 4).

## ProDG version and flags (2026-09-29)

**Flags, from two exact matches:** `cc1plus -O2 -G0 -ffloat-store -fno-strength-reduce`.
- `fn_80044D90` (0x90 bytes, a ratio bucketed at 0.34 and 0.67) matches exactly. `-ffloat-store`
  shows in the float result being stored to the stack and read back, with the 0x18 frame.
- `fn_803B3908` (0x9C bytes, a loop scaling bytes by 1/255 into a float array) matches exactly.
  `-fno-strength-reduce` shows in the index being recomputed with `slwi` on each pass.
- `-G0`: game code never touches r13. The 638 r13 accesses below 0x80403F08 all sit at 0x8036xxxx
  and later, which is libraries (audio, middleware), not EA's game code.

```cpp
int ratio(unsigned total, unsigned part) {           // fn_80044D90
    int r = 0;
    if (total) {
        float f = (float)part / (float)total;
        if (!(f > 0.34f)) r = 1;
        else if (!(f > 0.67f)) r = 2;
        else r = 4;
    }
    return r;
}
void Fill(unsigned int key, float* out) {            // fn_803B3908
    unsigned int idx = (key >> 8) & 0xff;
    for (int i = 0; i < gInfo.count; i++)
        out[i] = (float)gTables[i][idx] * (1.0f / 255.0f);
    if (gMode == 3)
        out[5] = 0.0f;
}
```
(Test code only: the names are placeholders, not yet run through the naming pass.)

**Version: can't be told apart, so 3.9.3 for now.** The package has ProDG 3.5 (gcc 2.95.2, SN BUILD
v1.37), 3.5b140 (v1.40), 3.7 (v1.46), 3.8.1 (v1.55) and 3.9.3 (gcc 2.95.3, v1.76). The two matches
above, a 25-function C++ test set (virtual calls, constructors, switches, float and 64-bit maths,
struct copies) at -O2, -O3 and -Os, and four smaller game functions all compile to identical code
on every version. Their `cc1plus.exe` build dates run from 2001-08 (3.5) to 2003-03 (3.9.3), and the
game's newest library is from Dec 2004, so EA may have used a later ProDG that the package lacks.
For the code that matters that makes no difference: what counts is a compiler that reproduces the
bytes, and all five do. The default is 3.9.3, the newest and closest in date. Revisit only if a
function ever matches on one version and not another.

Outside support (secondhand, not measured by us): the owner of the NFS Most Wanted GameCube decomp
(EA Canada, 2005) told Lucas on 2026-09-29 that it builds with ProDG 3.9.3. A sister EA title from
the same year on 3.9.3 makes 3.9.3 the likely real pick, not just the default.

**Correction from the first game unit (2026-09-30, `common/geomlib/geomgroup.cpp`):** that file
matches only at `-Os -G0 -ffloat-store`. At `-O2` the register choices and one store order differ,
and its loops are strength-reduced (a `ctr` loop, pointer steps), so no `-fno-strength-reduce`.
The evidence above does not contradict this: `fn_803B3908` sits in the SND library
(0x803A4214..0x803B9794), not game code, and `fn_80044D90` compiles identically at `-O2` and `-Os`.
`cflags_game` is left as it was until more game units say which flags the whole game uses;
geomlib uses `cflags_game_os`.

Two build rules came with it (`GameObject` in `configure.py`):
- **Vtables.** GCC 2.95 emits each vtable in a `.gnu.linkonce.d._vt.<class>` section, and SN's
  linker placed them all after every object's `.data` (0x806492A8..0x80686800). dtk cannot give a
  game unit that range without a link-order cycle, so `tools/linkonce_data.py` turns the object's
  vtable into a reference to the copy in dtk's `.data` asm (named `_vt.<class>` in `symbols.txt`).
- **Unused inline members.** GCC 2.95 emits every inline member of a class in the file holding its
  vtable; ngcld dropped the unused ones, as in SN's libraries, so `strip_unused.py --gcc` runs too.

## What this means for the build

- tw2004's CodeWarrior rulebook (`docs/decomp-notes.md` there) mostly does not apply.
- **The ProDG compile rule** (from 2026-09-29): an object whose `mw_version` is `ProDG/<version>`
  is built by `tools/prodg_cc.py`, which runs that version's `CPP.exe`, `cc1.exe`/`cc1plus.exe`
  and `NgcAs.exe` (through wibo on Linux) with the arguments SN's driver `ngccc.exe` gives them
  (read from `ngccc -v`; the objects are byte-identical to ngccc's). ngccc itself is not used: it
  needs `SN_NGC_PATH` and writes its temporary files into the current directory under random
  short names, which parallel compiles can share. The language comes from the file extension
  (`.c` or `.cpp`); no `-lang` flag is added. cpp writes the dependency file with CRLF line ends,
  which `prodg_cc.py` turns into LF: the CI image's `ninja` is samurai 1.2, which reports "bad
  depfile" on a multi-line CRLF one and loops forever on a one-line one (that was the CI hang of
  2026-09-29).
- **Stuck stages under wibo** (2026-09-29, a stopgap): once in CI, `NgcAs.exe` under wibo 1.0.3
  never returned on an unchanged libc file, while the other run of the same commit passed. It did
  not reproduce locally in about 10,000 parallel runs, with io_uring or with the epoll backend
  wibo falls back to when Docker's seccomp blocks io_uring (as in CI). The suspect is a thread
  race in wibo 1.0.3: 1.2.0's notes list a fixed module TLS initialization race and reworked
  critical sections, but 1.2.0 cannot run the SDK's compiler wrapper (sjiswrap stops on a missing
  `RtlCaptureContext`), so the pin stays at 1.0.3. Until wibo can be moved up, `prodg_cc.py` kills
  a stage that runs 30 s (each takes well under a second) and runs it again, up to three tries,
  printing `WIBO HANG` with the stage and the try to the build log so the rate can be counted.
  The stages are deterministic, so a rerun gives the same object. In `configure.py`, `PRODG_VERSION` is `ProDG/3.9.3`, `cflags_game` holds
  the game flags above and `SnLib(...)` declares a ProDG library. The package has no ProDG system
  headers; code that includes `<stdio.h>` and friends needs them in the repo first (they come with
  the C library import). First users: libgcc's 64-bit helpers (`src/libgcc/`), byte exact.
- **The build links with SN's `ngcld`** (owner's call, 2026-09-29: use what EA used), through
  `config.sn_linker` in `configure.py` and the GNU-style script `config/GV4E69/ldscript.tpl`.
  With every relocation kept (3,334 small-data references, `.sdata2` included), it links the split
  objects to the exact DOL, where CodeWarrior's `mwldeppc` could only match by leaving the `.sdata2`
  references as raw bytes. The `ngcld` from each ProDG version in the package (3.5, 3.7, 3.8.1,
  3.9.3) gives the same exact DOL. 3.9.3's is used because it is the only one that reads response
  files. The two small-data bases in the script are the values the entry code loads (r13
  0x806F69C0, r2 0x807069C0).
