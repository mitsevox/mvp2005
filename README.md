# MVP Baseball 2005

A matching decompilation of **MVP Baseball 2005** (GameCube, EA, 2005): C++ source that compiles back to a byte-identical copy of the retail `main.dol`. The aim is EA's code as EA wrote it. A PC port and mods will start from that code later.

This repository contains no game assets, no game code binaries and no official SDK files. You need your own copy of the game to build it.

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
- 1 game unit is configured but not linked yet: `geomcone.cpp` (7 of its 8 functions exact; the
  last, Precompute, is in [`docs/tried/`](docs/tried/)).

**Verified numbers**, from CI's objdiff report on PR #59's head `226488a` (2026-09-30):

| | Exact | Total | |
|---|---:|---:|---:|
| Functions | 1,127 | 24,150 | 4.67% |
| Code (bytes) | 253,740 | 5,896,192 | 4.30% |
| Units complete | 226 | 305 | |

Of the exact functions, 17 are game code (geomgroup's 10, geomcone's 7), 2 EA's EAGL graphics
library (viewport), 1,011 the SDK, C library and SN runtime, and 97 EA SND. Everything else, nearly all of the game, is still assembly. (objdiff
counts 24,150 functions; dtk's split found 24,158.)

Live numbers: the [progress page](https://mitsevox.github.io/games/mvp2005/).

## Targets

| Id | Region | Revision | Status | Original SHA-1 |
| --- | --- | --- | --- | --- |
| `GV4E69-rev0` | USA | 0 | active | `da6becdbea614d03c4b5eae9f8a0fb08e0a184dd` |

`config/targets.json` is the registry; each target's inputs are in `config/<id>/`.

## Building

Needs Python 3 and [ninja](https://github.com/ninja-build/ninja). On Linux and macOS, [wibo](https://github.com/decompals/wibo) is downloaded automatically to run the compiler and linker.

1. Put your disc image (ISO/GCM, RVZ, WIA, WBFS, CISO, NFS, GCZ or TGC) in `orig/GV4E69-rev0/`, or the extracted `main.dol` at `orig/GV4E69-rev0/sys/main.dol`.
2. `python configure.py` then `ninja`. The build must end with `build/GV4E69-rev0/main.dol: OK`.
3. `ninja build/GV4E69-rev0/report.json` measures the target.

To check every active target: `for id in $(python3 -c 'from tools.targets import build_targets; print(*build_targets())'); do python3 configure.py --version "$id" && ninja; done`.

Pinned tool versions are in `configure.py`; the build structure is [dtk-template](https://github.com/encounter/dtk-template), whose documentation covers the other commands. The link uses SN Systems' ProDG linker (`ngcld`), as EA's build did ([docs/compiler.md](docs/compiler.md)). A cloud session sets itself up with `tools/cloud/setup.sh` ([tools/cloud/README.md](tools/cloud/README.md)).

## CI and the progress site

`.github/workflows/validate.yml` builds every affected target in the private build image from [mitsevox/mvp2005-build](https://github.com/mitsevox/mvp2005-build) and publishes each measurement to the [progress site](https://mitsevox.github.io/games/mvp2005/) on `main`. Pull requests publish nothing.

## Contributing

The project owner is **[mitsevox](https://github.com/mitsevox)**, the sole merge authority. See [CONTRIBUTING.md](CONTRIBUTING.md) for the tiers, the task loop and the review checklist; agents start with [AGENTS.md](AGENTS.md), whose Project section holds this repository's facts; [docs/fidelity.md](docs/fidelity.md) is the style guide. Open work is tracked in the issues.

## Layout

| Directory | Purpose |
| --- | --- |
| `src/`, `include/` | Game code under `src/common/` and `src/realcore/`; the imported SDK, C library, SN runtime and EA SND under `src/dolphin/`, `src/libc/`, `src/libm/`, `src/libgcc/`, `src/libsn/` and `src/snd/` |
| `config/<id>/` | One target's toolkit inputs, `build.sha1`, `filemap.tsv` and `name_sources.tsv`, the evidence behind every game name |
| `orig/<id>/` | Where the original goes locally; ignored by Git |
| `build/` | Generated; ignored |
| `tools/`, `tests/` | The kit tools, dtk-template's tools and the project's own: research (`tools/research/`), matching (`tools/match/`) and the cloud setup (`tools/cloud/`) |
| `docs/` | [compiler.md](docs/compiler.md) (SN ProDG / GCC 2.95 and the flags), [sdk.md](docs/sdk.md), [names.md](docs/names.md), [reference-builds/](docs/reference-builds/README.md), [filemap.md](docs/filemap.md), and the process docs in `docs/process/` |

## Credits and licenses

Imported source is credited in [CREDITS.md](CREDITS.md), and each imported file names its origin on its first line. The process and infrastructure come from the [Tiger Woods PGA Tour 2004 decompilation](https://github.com/mitsevox/tw2004). Built on [decomp-toolkit](https://github.com/encounter/decomp-toolkit) and [objdiff](https://github.com/encounter/objdiff).
