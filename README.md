MVP Baseball 2005
=================

A work-in-progress matching decompilation of MVP Baseball 2005 (GameCube).

This repository does **not** contain any game assets or assembly whatsoever. An existing copy of the
game is required.

Status
======

Scaffold only (2026-09-29): the build setup and the working process are in place; discovery starts
once the game's `main.dol` is available to the build. Agents and contributors start at
[`CLAUDE.md`](CLAUDE.md).

Building
========

- Install Python and [ninja](https://github.com/ninja-build/ninja/releases). On Linux and macOS,
  [wibo](https://github.com/decompals/wibo) is downloaded automatically.
- Copy your disc image to `orig/<GAMEID>`.
- `python configure.py`, then `ninja`. The build must end with `main.dol: OK`.

Once the build succeeds, an `objdiff.json` exists in the project root for
[objdiff](https://github.com/encounter/objdiff).

References
==========

- [decomp-toolkit](https://github.com/encounter/decomp-toolkit) /
  [dtk-template](https://github.com/encounter/dtk-template) (this project's scaffold)
- [objdiff](https://github.com/encounter/objdiff), [decomp.me](https://decomp.me),
  [decomp.dev](https://decomp.dev)
