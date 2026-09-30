# Fidelity: writing it the way EA wrote it

Owner decision, 2026-09-30 (green-lit as proposed; calibration tweaks green-lit the same day).
Applies to every game unit from now on. Library imports (SDK, SN runtime, nfsmw SND) are exempt:
that code is upstream's, and keeps upstream's form with a provenance note.

**The one-line version:** write it the way an EA Canada dev in 2004 would have, and make every
deviation from that visible. The byte match is the floor, not the goal. A unit is judged by a
hostile reader who assumes it is AI slop until the code proves otherwise (`docs/review-checklist.md`).

**The reference file** is `src/common/geomlib/geomgroup.cpp` with `geomgroup.h`, `geomlib.h` and
`src/realcore/realmath.h`. It was matched in the pilot (PR #47, "Bad" below) and redone to these
rules (PR #49, "Good" below; hostile review REDO before, SHIP after). When in doubt, do what it does.

## 1. Evidence decides

The ranking, strongest first:

| Tier | Source | Examples |
|---|---|---|
| T1 | EA's own text in the binary naming the thing itself | assert and error strings, djb2 type IDs, reflection member names (`docs/names.md`) |
| T2 | EA's name from a related build, confirmed by the code; or a name the compiler fixes | `COORD4`, `MATRIX4` (mangled names in the FIFA/UEFA maps); DWARF from GoldenEye, MoH EA, nfsmw (`docs/reference-builds/`) |
| T3 | Read from the code, a file name, or a convention learned from units already matched | `UpdateBounds`; `GeomGroup` (from the file name `geomgroup.cpp`) |
| T4 | Judgment: the code does not settle it | `keepPrevious`, the second argument of `Transform` |

A file name alone (an assert's `__FILE__`) places a function in a unit; it does not name a class
or function. A class named only from its file name is **T3**, not T2.

Every name **and every type** gets a row in `config/GV4E69/name_sources.tsv` with its tier and
evidence (types and fields: the address column is the vtable, or `type` for a plain struct). A T4
row's evidence starts with `guess:`; the comment still states only what the code shows.

- Good: `keepPrevious` with a T4 row ("guess: GeomCone copies one 4-float block aside when set"),
  and a comment that says only that.
- Bad: the same name with a T3 row and a comment that states "keeps the previous position" as fact.

Quote EA's strings exactly as the binary spells them (`C:/mvp2004/...` and `/mvp2004/...` are
different strings). A `#line` path is proven by the build; any other quoted path is copied from the
binary, never from a summary doc.

## 2. EA's vocabulary, not ours

Use EA's real types (math, containers, allocators), EA's macros (asserts, MIN/MAX, whatever the
references show) and EA's naming style, taken from the DWARF builds and the FIFA/UEFA maps. C++ as
GCC 2.95 takes it: no `nullptr`, `auto`, `static_cast` habits, templates EA did not have, or
`std::`. Use `0`/`NULL` the way EA's headers do.

- Bad (#47): `virtual void Transform(const float* matrix, bool keepPrevious);` and
  `Clone(const float* scale)`. Nobody at EA passed a 4x4 matrix as a bare `float*`.
- Good (#49): `Transform(const MATRIX4* matrix, bool keepPrevious)`, `Clone(const COORD4* scale)`,
  with EA's realmath type names from the maps (`src/realcore/realmath.h`).

## 3. Types before volume

Build the shared type layer before mass decomp: EA's math types, the `Geom` class family, the
allocator and assert hosts, from the reference DWARF and the maps. A unit that needs a type that
does not exist yet adds it to the shared header first (with its evidence row), never a local
stand-in. A header type says where its name and layout come from in one line.

When no build with debug info gives a type's layout, the type still ships under EA's name, with
the layout marked unknown: declare only the members matched code reads, say so in the header
(`realmath.h`: "only what matched units read is declared, and the member names are ours"), and tag
the guessed member names T4. Leave a type incomplete (`struct MATRIX4;`) until a matched unit
reads it. The layout is replaced when a DWARF build turns up.

Why: every file written against placeholder types gets rewritten when the real type arrives.

## 4. Match-forcing is a smell, not a crime

A source shape chosen because the codegen needs it is allowed only when a dev plausibly wrote it,
and it carries a note giving the codegen reason:

```
// MATCH: <what the natural form emits instead, and what this form fixes>
```

- `// MATCH:` = a plausible EA form picked from several because only it matches. It may well be
  what EA wrote. The note names the natural form that was tried and what it emitted.
- `// fake match:` (CLAUDE.md fidelity order 2) = a form we believe EA did **not** write, used only
  after EA's form could not be found. It leaves the logic unchanged.

Counting: an **unexplained** forced shape (no note, or a note that only says "needed to match")
means REDO. Explained notes are a signal, not a cap: the reviewer reports the count per file
(`grep -cE '// (MATCH|fake match):'`), and a high count only triggers a second look at whether a
more natural form exists.

**Banned outright:** meaningless temporaries (`int tmp = x; use(tmp);` with no meaning), raw
offsets (`*(float*)((char*)this + 0x30)`), casts to fake types, inline asm, register variables or
`register` hacks, `goto` as a match trick, dead code kept for its bytes.

- Bad (#47): `GeomBox::Enclose` as six `if (!(mMin[0] <= box.mMin[0]))` with a paragraph on
  `cror`/`bso`, and no sign the natural form was tried.
- Good (#49): the same six ifs on `COORD4` members under one note: "only `!(a <= b)` gives the
  cror/bso branch around each store; `a < b` and `a > b` branch with ble/bge, and
  `x = MIN(x, y)` stores unconditionally". The macro was tried first; the note says so.

## 5. Consistency

Once a pattern exists, it is used the same way everywhere, or the exception is explained.

- Bad (#47): `Child(i)` in `CopyFrom` and `SetScaled`, `mChildren[i]` elsewhere, with no reason given.
- Good (#49): one `// MATCH:` note on `Child(i)` in `geomgroup.h` says which functions need which
  operand order, so the split is explained once where a reader meets it.

## 6. Honest unknowns

Pads and offset-named fields (`mPad10[0x20]`, `mUnk34`) are allowed while a class is in progress.
The class says "In progress" in its comment. A class is **not done** until they are gone; a unit
that only touches known fields can still be DONE.

- Allowed (#49): `char mPad10[0x20];` in `Geom`, because no matched unit touches 0x10..0x2F yet.
- Not allowed: naming those bytes from a guess to make the class look finished.

## 7. Comments explain why, never narrate

A short intent line per class and function: what it is for in the game, units, what 0/NULL means,
side effects. Never "this function does X by doing X". Never a claim the code does not show, and
no hedging ("probably", "seems"): the evidence row carries how sure we are.

- Bad: `// Loops over the children and calls Transform on each, then calls UpdateBounds.`
- Good: `// Moves every child to world space; the group's bounds follow its children.`

## 8. A hostile review gate on every PR

Before a game unit merges, a reviewer agent plays the hostile decomp-server mod with the fixed
checklist in `docs/review-checklist.md`, on top of the blind naming review (`agents/pass.md` loop 2).

The loop: a **fresh** reviewer (one that has not seen the lane's work) does the first full pass.
The lane fixes each FAIL or answers it in the PR with evidence. The **same** reviewer then
re-checks: only its earlier FAILs and anything the fixes changed, not a new full pass. A fresh
reviewer per round invents new nits every time (the calibration took 7 rounds that way).

## 9. `#line`

Allowed, as a documented convention: EA's asserts pass `__FILE__` and `__LINE__`, and rebuilding
EA's blank-line layout by hand says nothing about intent. Rules for it:

- The first `#line` in a file sets EA's path exactly as the binary spells it:
  `#line 75 "/mvp2004/source/common/geomlib/geomgroup.cpp"`.
- Later ones give only the number, directly above the assert that needs it.
- The file header says once that `__LINE__` values are EA's, set with `#line`.
- No `#line` anywhere else (not for layout, not for anything but a value the binary holds).
