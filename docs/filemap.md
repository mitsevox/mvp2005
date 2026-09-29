# The file map (discovery step 7)

Status 2026-09-29: the evidence map is built. `config/GV4E69/filemap.tsv` places functions in EA's
source files only where the binary or a related EA build proves it. The rest stays unplaced, and
matching places it later: when a file is compiled, its functions and its constant pool have to line
up with the original, which proves the file's edges. Nothing is split in `splits.txt` yet. The
library block (0x80403F08..0x8043F058) is left out because the SDK and runtime come from public
decomps (`docs/sdk.md`).

Regenerate with (the map name lists live in the project's shared folder, not in the repo):

```
python tools/research/filemap.py --maps <refnames>/uefa.tsv <refnames>/fifa05.tsv --tsv config/GV4E69/filemap.tsv
```

## What proves a file edge or a file's name

| Evidence | What it proves | Count |
|---|---|---|
| Static-init pair | GCC 2.95 ends every file that has global objects with `_GLOBAL_$I` (and `_GLOBAL_$D` if it has destructors), both listed in `.ctors`/`.dtors`. The next function starts a new file | 87 exact file ends (87 ctors, 15 dtors), all in link order |
| Source path | A function that references a `.cpp` `__FILE__` string is in that file. Files run contiguously in `.text`, so everything between a file's first and last such function is in it too | 267 functions, 64 game files and 1 library file (`pathlist.cpp`) |
| SN link map | FIFA 2005 and UEFA CL 2004-05 (EA Canada, same toolchain) name the object file of library functions that match ours byte for byte (docs/reference-builds) | 740 functions in 215 library objects |

Checks: no source path shows up in two separate runs, and no static-init end falls inside a path
file. The maps disagree with our layout once: EAGL's `state.o` has functions at 0x80364A90 and at
0x803DA4EC, with other objects between. That's probably a different EAGL version (MVP's EAGL isn't
the FIFA one). Both are listed and neither is resolved.

## Coverage

| Block | Functions | Named files | Functions placed | Exact file ends |
|---|---|---|---|---|
| Game code 0x800034A0..0x80364000 | 15,282 | 63 | 1,320 (8.6%) | 31 |
| EA libraries 0x80364000..0x80403F08 | 2,572 | 216 | 1,136 (44.2%) | 54 |
| Game code 0x8043F058..0x805A2BC0 | 5,223 | 1 | 1 (0.0%) | 2 |

The 0x80364000 line between game code and EA libraries is approximate (`docs/sdk.md`). EAGL code
starts by 0x80364A90.

In game code, the 33 exact ends and the block edges cut 20,505 functions into 35 stretches. 21 name no file,
3 name exactly one (`ddtrap.cpp`, `assetmanager.cpp`, `audionames.cpp`), and one names 17. So
static-init ends are far sparser than files, and most files end without one.

## What did not work (measured, so nobody repeats it)

Measured against the 206 object changes the FIFA/UEFA maps show in the EA library block, with 519
same-object neighbours as the control:

- **Constant pools.** Starting a new file whenever a function's own constants lie past everything
  the file has used so far found 72 of 206 real edges and made 84 false splits. A file's constants
  are not in function order, but they are not cleanly separated from the next file's either.
- **Shared data and calls.** Counting data and call links that cross each gap, and cutting at
  local minima, found at most 37 of 206 edges (12 false). Neighbouring files call each other and
  share externs too often.
- **Class evidence** (docs/names.md). A class's vtable is also stored by its constructor inlined
  into other files: `cBall`'s vtable is stored at 0x8014AFA8, 0x80191720 and 0x801C1784. Its
  inline getters are emitted away from its constructor: `cActorScriptConditional` has its
  constructor in `actorscriptconditional.cpp` (0x80151A48) and its type-ID getter at 0x8016F3F4.
  So classes name vtables, not files.

## What this means for matching

- Bulk matching can't start from a full map, and doesn't need to. A file is placed when it matches:
  its functions compile in order and its constant pool lines up. The map gives the proven start
  points: 65 named source files, 215 library objects, and 87 exact file ends.
- The pilot (step 8) should be a file whose edges the evidence pins as tightly as possible.
- More evidence can come later from the owner's discs (map files on MVP's PS2 discs,
  docs/reference-builds) and from DWARF builds that carry compile units for the library block.
