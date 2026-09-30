# What the retail disc holds (GV4E69)

Checked 2026-09-30 from the owner's own USA disc (Game ID `GV4E69`, revision 0; `sys/main.dol`
SHA-1 `da6becdbea614d03c4b5eae9f8a0fb08e0a184dd`, the project's target; `files/version.txt`:
`TP GC Build Number 2004-12-24_1`). No game file goes in this repo.

## The main executable

`files/mvp.elf` is the game linked as an ELF, stripped: no symbols and no debug sections. Its
loaded sections are byte-identical to `main.dol`. It keeps section names the DOL loses
(`.frontend_codeoverlay`, `.database_codeoverlay`, separate `.ctors` and `.dtors`).

## EA's own debug data: libmatd.a

`files/data/libmatd.a` (SHA-1 `91b461b8382ab3309cbf5b6687f95622a02edaa2`) holds 25 of the
game's render-method objects (`InstanceCrowd.o`, `Texture.o` and so on, compiled from
`C:/mvp2004/source/GC/rendermethods/`) with symbols and full DWARF1 debug data from
`GNU C++ 2.95.3 SN BUILD v1.76`. `libmatz.a` has the same members with symbols only.

These objects are not part of `main.dol`'s own code map, but they include EA's shared headers, so
their DWARF gives EA's layouts and member names for every type they use: realmath (`COORD3`,
`COORD4`, `MATRIX4`), EAGL (`ViewPort`, `Transform`, `RenderContextBase`, `Colour`...) and
Dolphin SDK types. It is the strongest evidence the project has for a type (tier T1).

What DWARF1 from this compiler does and does not record:

- Records: every member's name, type and offset; sizes; enum values; typedefs; static members;
  inline member functions (EA's operator new/delete overloads show up on most classes); global
  inline functions used by the object (`DegToRad`, `RadToDeg`).
- Does not record: namespaces, `struct` versus `class`, access (public or private), member
  functions that are not inline, or which header declared a type (`.debug_sfnames` lists only
  the few headers that hold inline code with line numbers).
- Unnamed structs are real: `COORD3` and `COORD4` are typedefs of unnamed structs, so EA's
  versions have no constructors.

## Where the data lives

The full export (`disc_debug_full.py`: every record, symbol and relocation of the 25 objects,
plus symbols of 41 more ELF objects on the disc) can rebuild the original sections byte for byte
and includes SDK types, so it lives in the private `mitsevox/mvp2005-build` repo under
`disc-debug/GV4E69/`, with its own README. Clone that repo beside this one, then:

```
python3 tools/research/dwarf_lookup.py ViewPortPrivate COORD4   # EA's layout of a type
python3 tools/research/disc_debug_full.py --verify ../mvp2005-build/disc-debug/GV4E69
```

This repo keeps only facts that matched code uses: the evidence rows in
`config/GV4E69/name_sources.tsv` (each cites the object and `.debug` offset) and
`config/GV4E69/disc_types.tsv`, the viewport types' records from `InstanceCrowd.o`
(`tools/research/disc_debug.py`, which reads the archive itself). Never commit SDK types from
the export; SDK headers come from the public decomps.

To regenerate the export from an extracted disc (a directory with `files/` and `sys/`):

```
python3 tools/research/disc_debug_full.py <extracted-disc> --output ../mvp2005-build/disc-debug/GV4E69
```

## Other contents

405 files under `files/` and five under `sys/`; 38,659 entries in the standard BIG archives. None
is a map, PDB, symbol file or C/C++ source. 15 loose runtime model `.o` files carry symbols (no
debug data); they reference EAGL's interfaces. 243 animation `.ord` entries start with an ELF
signature but do not parse as ELF objects; 16 audio `.big` files use another format and were not
indexed; nested or compressed assets were not searched. `mvp.ini` lists development switches
(AI, simulation, camera, rendering); its own comment says shipping builds ignore the file.
