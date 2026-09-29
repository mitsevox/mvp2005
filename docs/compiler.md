# Compiler and language (discovery step 3)

Status 2026-09-29: the compiler family and the linker are settled from the binary; the exact ProDG
version is not yet. Every line below says what was measured.

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

dtk's signatures find `GXInit`, `OSRegisterVersion`, `PPCHalt` and others in 0x80403F08..0x8043E728
with CodeWarrior prologues. They come from the Dolphin SDK's prebuilt libraries (discovery step 4).

## ProDG version: open

The compilers package has ProDG 3.5 (gcc 2.95.2, SN BUILD v1.37), 3.5b140 (v1.40), 3.7 (v1.46),
3.8.1 (v1.54/1.55) and 3.9.3 (gcc 2.95.3, v1.76). A small test (a float dot product and a getter)
compiles to identical code on all of them, so the version has to come from matching real game
functions, looking for one that only some versions reproduce. Each version's build date also has to
be checked against Dec 2004. The package includes each version's `ngcld.exe`, which may answer the
linker question below.

## What this means for the build

- tw2004's CodeWarrior rulebook (`docs/decomp-notes.md` there) mostly does not apply. tw2004's
  ProDG path (`tools/prodg/prodgcc.py`: cpp, cc1, NgcAs run directly) is the starting point,
  with `cc1plus.exe` for C++.
- **Parked (linker):** the rebuild links with CodeWarrior's `mwldeppc`, which encodes `.sdata2`
  against r2. The asm-only rebuild is exact because `config/GV4E69/config.yml` leaves those
  references as raw bytes, but compiled C++ that touches `.sdata2` will not link the same way.
  Options: link with SN's `ngcld`, a post-link fixup, or a section layout mwld treats as r13.
  Decide before the pilot.
