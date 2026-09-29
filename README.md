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

**The match has not started.** All 24,158 functions are still assembly and no unit links from C
yet; the build already reproduces the retail `main.dol` exactly from that assembly.

The project is in its **scaffold** phase: discovery of the compiler, libraries and file layout
([`docs/discovery.md`](docs/discovery.md)), then a small pilot section before matching scales up
([`agents/pass.md`](agents/pass.md)). Here a function counts as exact only once it is also named
and commented, in the same commit. As of 2026-09-29, of the 24,158 functions:

- 0 are byte-exact;
- 0 are named in the pass (the evidence for names found so far is in [`docs/names.md`](docs/names.md));
- 0 source files are through it.

Live numbers: the [progress page](https://mitsevox.github.io/mvp2005/) and
[decomp.dev](https://decomp.dev/mitsevox/mvp2005).

What's here
===========

- `src/`, `include/`: the game's C++ source and headers. Not started.
- `extern/`: the Nintendo SDK, C library and SN runtime, built from public GameCube
  decompilations. Not started.
- `config/GV4E69/`: decomp-toolkit configuration (symbols, splits) and
  [`filemap.tsv`](config/GV4E69/filemap.tsv), the evidence map of where source files begin and
  end. `name_sources.tsv`, the evidence behind every name, starts with the first match.
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
