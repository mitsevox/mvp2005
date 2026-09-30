MVP Baseball 2005
=================

[![Code progress](https://decomp.dev/mitsevox/mvp2005.svg?mode=shield&measure=code&label=Code)](https://decomp.dev/mitsevox/mvp2005)
[![Functions](https://decomp.dev/mitsevox/mvp2005.svg?mode=shield&measure=functions&label=Functions)](https://decomp.dev/mitsevox/mvp2005)

A matching decompilation of MVP Baseball 2005 for the GameCube: C++ source that compiles back to
a byte-identical copy of the retail `main.dol`. The aim is EA's code as EA wrote it. A PC port and
mods will start from that code later.

This repository contains no game assets, no game code binaries and no official SDK files. You need
your own copy of the game to build it.

Supported version: `GV4E69` (USA). `main.dol` SHA-1 `da6becdbea614d03c4b5eae9f8a0fb08e0a184dd`.

Status
======

The build reproduces the retail `main.dol` exactly. Discovery is done
([`docs/discovery.md`](docs/discovery.md)); the imported libraries are in, and game code has just
started, one small geometry library (geomlib, the collision shapes) at a time. Here a game function
counts as exact only once it is also named and commented, in the same commit
([`docs/fidelity.md`](docs/fidelity.md)).

**Configured units** (`configure.py`, the source files that build from C): 227.
- 226 are marked matching and are linked in place of the assembly:
  - 209 library units (Nintendo SDK 96, C library 65, libm 33, libgcc 12, SN libsn 3), taken from
    public GameCube decomps (`CREDITS.md`);
  - 16 EA SND audio units, adapted from the NFS Most Wanted decomp;
  - 1 game unit, `geomgroup.cpp` (10 of 10 functions exact, named and commented).
- 1 game unit is configured but not linked yet: `geomcone.cpp` (5 of its 8 functions exact; the
  other three are in [`agents/tried/`](agents/tried/)).

**Verified numbers**, from CI's objdiff report on `main` at `66a863a` (2026-09-30):

| | Exact | Total | |
|---|---:|---:|---:|
| Functions | 1,123 | 24,150 | 4.65% |
| Code (bytes) | 252,172 | 5,896,192 | 4.28% |
| Units complete | 226 | 301 | |

Of the exact functions, 15 are game code (geomgroup's 10, geomcone's 5), 1,011 the SDK, C library
and SN runtime, and 97 EA SND. Everything else, nearly all of the game, is still assembly. (objdiff
counts 24,150 functions; dtk's split found 24,158.)

Live numbers: the [progress page](https://mitsevox.github.io/mvp2005/) and
[decomp.dev](https://decomp.dev/mitsevox/mvp2005).

What's here
===========

- `src/`, `include/`: the source and headers: game code under `src/common/` and
  `src/realcore/`, the imported SDK, C library, SN runtime and EA SND under `src/dolphin/`,
  `src/libc/`, `src/libm/`, `src/libgcc/`, `src/libsn/` and `src/snd/`.
- `config/GV4E69/`: decomp-toolkit configuration (symbols, splits) and
  [`filemap.tsv`](config/GV4E69/filemap.tsv), the evidence map of where source files begin and
  end. [`name_sources.tsv`](config/GV4E69/name_sources.tsv) holds the evidence behind every game
  name.
- `docs/`: highlights: [`docs/compiler.md`](docs/compiler.md) (SN ProDG / GCC 2.95 and the flags),
  [`docs/sdk.md`](docs/sdk.md) (the SDK and EA libraries in the binary),
  [`docs/names.md`](docs/names.md) (names leaked by the binary),
  [`docs/reference-builds/`](docs/reference-builds/README.md) (other EA builds with symbols),
  [`docs/filemap.md`](docs/filemap.md) (the source file layout).
- `tools/`: build and research scripts (`tools/research/`), and the cloud build setup
  (`tools/cloud/`).
- `agents/`: how the work is organised and where it stands ([`agents/state.md`](agents/state.md)).

Building
========

Needs Python 3 and [ninja](https://github.com/ninja-build/ninja). On Linux and macOS,
[wibo](https://github.com/decompals/wibo) is downloaded automatically to run the compiler and
linker.

1. Put your disc image (ISO/GCM, RVZ, WIA, WBFS, CISO, NFS, GCZ or TGC) in `orig/GV4E69/`, or the
   extracted `main.dol` at `orig/GV4E69/sys/main.dol`.
2. Run:

   ```sh
   python configure.py
   ninja
   ```

The build must end with `build/GV4E69/main.dol: OK`. More commands are in
[`docs/getting_started.md`](docs/getting_started.md).

Credits
=======

Built on [decomp-toolkit](https://github.com/encounter/decomp-toolkit) and
[objdiff](https://github.com/encounter/objdiff), and linked with SN Systems' ProDG linker
(`ngcld`), as EA's build was. The process and infrastructure come from the
[Tiger Woods PGA Tour 2004 decompilation](https://github.com/mitsevox/tw2004).
