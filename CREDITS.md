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

The SDK code is a reverse-engineered reconstruction of Nintendo's libraries, kept here for
research and preservation, as in those repositories. Its names are Nintendo's own symbol names.
No official SDK files, headers or documentation are in this repository.
