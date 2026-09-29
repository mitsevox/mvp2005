# Credits

Code in this repository that was not written here comes from these public decompilations. Every
imported file says where it came from on its first line (`tools/import_upstream.py`), and
`config/GV4E69/imported_units.tsv` lists each imported unit with its upstream commit.

## Nintendo Dolphin SDK (`src/dolphin/`, `include/dolphin/`, `include/libc/`)

- [emoose/re4](https://github.com/emoose/re4), commit `feb6805b`: the Resident Evil 4 GameCube
  decompilation. It links the same SDK build as MVP (2004 SDK, Patch 1, including GX's
  `Apr 5 2004 04:14:28` build) with the same SN toolchain, so we take its SDK sources as they are.
  Its tools and docs are CC0-1.0; `tools/strip_unused.py` is adapted from its tool of that name.
- [doldecomp/dolsdk2004](https://github.com/doldecomp/dolsdk2004), commit `2328b416`: the
  decompilation of the 2004 Dolphin SDK libraries that re4's SDK sources are based on.
- [mariopartyrd/partyboard](https://github.com/mariopartyrd/partyboard): the `DebuggerDriver`
  (OdemuExi2) source that re4 took.

## GCC runtime (`src/libgcc/`)

- [emoose/re4](https://github.com/emoose/re4), commit `feb6805b`: `src/lib/libgcc2/` (GCC 2.95.3's
  `libgcc2.c` and its headers, as SN ProDG builds them, with re4's `tconfig.h` shim) and
  `src/lib/_exit.c`. `libgcc2.c` is GNU CC source under the GPL with its runtime exception (see the
  notice in the file). The one-line `L_*` wrappers are ours, in re4's form.

## C library (`src/libc/`, `include/prodg/`)

- [emoose/re4](https://github.com/emoose/re4), commit `feb6805b`: `src/game/*.c` (newlib 1.8.2 as
  built into SN ProDG's `libc.a`), its private headers `newlib_local.h`, `newlib_stdio.h` and
  `va_ppc.h`, and two of ProDG's GCC 2.95 headers (`include/prodg/stdarg.h`, `va-ppc.h`, GNU CC,
  GPL). newlib is under the permissive licences named in its sources. Comments that described how
  Resident Evil 4 uses a function were removed or made general.

The SDK code is a reverse-engineered reconstruction of Nintendo's libraries, kept here for
research and preservation, as in those repositories. Its names are Nintendo's own symbol names.
No official SDK files, headers or documentation are in this repository.

## EA SND audio library (`src/snd/`, `include/snd/`, `include/csis/`, `include/Allocator/`)

- [dbalatoni13/nfsmw](https://github.com/dbalatoni13/nfsmw), commit `9ca26bc1` (CC0-1.0): the Need
  for Speed: Most Wanted GameCube decompilation. Its EA SND sources (`snd/9`, rwaudiocore 2.09.00)
  and the Csis and allocator headers they use, with EA's names from NFS MW's debug information.
  MVP links an older build of the same library (SND 9.02.04, Dec 2004); where MVP's differs, the
  change and its evidence are noted in the file (`src/snd/cmn/sndcmn.h`: `SNDGLOBALSTATE`).
  `include/cstddef` and `include/cstring` are small wrappers written here.
