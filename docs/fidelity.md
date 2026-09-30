# Fidelity: writing it the way EA wrote it

Owner decision, 2026-09-30 (green-lit as proposed). Applies to every game unit from now on.
Library imports (SDK, SN runtime, nfsmw SND) are exempt: that code is upstream's, and keeps
upstream's form with a provenance note.

**The one-line version:** write it the way an EA Canada dev in 2004 would have, and make every
deviation from that visible. The byte match is the floor, not the goal. A unit is judged by a
hostile reader who assumes it is AI slop until the code proves otherwise (`docs/review-checklist.md`).

The examples below come from the pilot, `src/common/geomlib/geomgroup.cpp` (PR #47), which is
byte-exact but does not yet meet these rules. It is the calibration file: it is redone to this
standard before anything scales.

## 1. Evidence decides

The ranking, strongest first:

| Tier | Source | Examples |
|---|---|---|
| T1 | EA's own text in the binary | `__FILE__` paths, assert and error strings, djb2 type IDs, reflection member names (`docs/names.md`) |
| T2 | EA's name from a related build, confirmed by the code; or a name the compiler fixes | FIFA/UEFA SN maps, DWARF from GoldenEye, MoH EA, nfsmw (`docs/reference-builds/`); `_vt.9GeomGroup` |
| T3 | Read from the code, or a convention learned from units already matched | `UpdateBounds`, the shape of `Child(i)` once EA's own use shows it |
| T4 | Judgment: the code does not settle it | the second argument of `Transform` |

Every name **and every type** gets a row in `config/GV4E69/name_sources.tsv` with its tier and
evidence (types and fields: the address column is the vtable, or `type` for a plain struct). A T4
name is a guess and its row says `guess`; the comment still states only what the code shows.

- Good: `keepPrevious` with a T4 row ("guess: GeomCone copies one 4-float block aside when set"),
  and a comment that says only that: "when set, a cone first copies one block of its data aside".
- Bad: the same name with a T3 row and a comment that states "keeps the previous position" as fact.

## 2. EA's vocabulary, not ours

Use EA's real types (math, containers, allocators), EA's macros (asserts, MIN/MAX, whatever the
references show) and EA's naming style, taken from the DWARF builds and the FIFA/UEFA maps. C++ as
GCC 2.95 takes it: no `nullptr`, `auto`, `static_cast` habits, templates EA did not have, or
`std::`. Use `0`/`NULL` the way EA's headers do.

- Bad (pilot): `virtual void Transform(const float* matrix, bool keepPrevious);` and
  `Clone(const float* scale)`. Nobody at EA passed a 4x4 matrix as a bare `float*`: the FIFA map
  shows EA's `realmath` library (`rmv3arit`, `mat4bld`), and nfsmw's DWARF carries its types.
- Good: the same signature written with EA's matrix and vector types, named exactly as the DWARF
  names them. Until the type layer (rule 3) has them, the unit is not DONE.

## 3. Types before volume

Build the shared type layer before mass decomp: EA's math types, the `Geom` class family, the
allocator and assert hosts, from the reference DWARF and the maps. A header type that came from
DWARF says so in one line (`// Layout: <build>'s DWARF`). A unit that needs a type that does not
exist yet adds it to the shared header first (with its evidence row), never a local stand-in.

Why: every file written against placeholder types gets rewritten when the real type arrives.

## 4. Match-forcing is a smell, not a crime

A source shape chosen because the codegen needs it is allowed only when a dev plausibly wrote it,
and it carries a note giving the codegen reason:

```
// MATCH: <what the natural form emits instead, and what this form fixes>
```

- `// MATCH:` = a plausible EA form picked from several because only it matches. It may well be
  what EA wrote.
- `// fake match:` (CLAUDE.md fidelity order 2) = a form we believe EA did **not** write, used only
  after EA's form could not be found. It leaves the logic unchanged.

Both are counted per file (`grep -c`). More than a few in one unit sends it back for another look;
the reviewer reports the count.

**Banned outright:** meaningless temporaries (`int tmp = x; use(tmp);` with no meaning), raw
offsets (`*(float*)((char*)this + 0x30)`), casts to fake types, inline asm, register variables or
`register` hacks, `goto` as a match trick, dead code kept for its bytes.

- Bad (pilot): `GeomBox::Enclose` as six hand-written `if (!(mMin[0] <= box.mMin[0])) ...` with a
  paragraph on `cror`/`bso`. That reads as a match-forcer. A dev wrote a MIN/MAX macro (or EA's
  math helper), and GCC expanded it to exactly this compare.
- Good: the macro or helper EA used (from the references), with no note needed, because it is the
  natural form. If a `!(a <= b)` truly is EA's form, one `// MATCH:` line says why.

## 5. Consistency

Once a pattern exists, it is used the same way everywhere, or the exception is explained.

- Bad (pilot): `Child(i)` in `CopyFrom` and `SetScaled`, `mChildren[i]` in `Release`,
  `Transform` and `UpdateBounds`. Real code is not that inconsistent; this is the codegen deciding.
- Good: one accessor used throughout, if the other three functions still match with it; otherwise
  the header says, once, why the loops that need the other operand order write `mChildren[i]`
  (`// MATCH:`), and the reviewer checks it.

## 6. Honest unknowns

Pads and offset-named fields (`mPad10[0x20]`, `mUnk34`) are allowed while a class is in progress.
A class is **not done** until they are gone, and a unit that only touches known fields can still
be DONE. `docs/` never pretends a layout is known when it is not.

- Allowed now (pilot): `char mPad10[0x20];` in `Geom`, because no matched unit touches 0x10..0x2F yet.
- Not allowed: naming those bytes from a guess to make the class look finished.

## 7. Comments explain why, never narrate

A short intent line per class and function: what it is for in the game, units, what 0/NULL means,
side effects. Never "this function does X by doing X". Never a claim the code does not show.

- Bad: `// Loops over the children and calls Transform on each, then calls UpdateBounds.`
- Good: `// Moves every child to world space; the group's bounds follow its children.`

## 8. A hostile review gate on every PR

Before a game unit merges, a separate reviewer agent plays the hostile decomp-server mod with the
fixed checklist in `docs/review-checklist.md`. It runs on top of the blind naming review
(`agents/pass.md` loop 2). Every finding is fixed, or answered in the PR with evidence, before merge.

## 9. `#line`

Allowed, as a documented convention: EA's asserts pass `__FILE__` and `__LINE__`, and rebuilding
EA's blank-line layout by hand says nothing about intent. Rules for it:

- The first `#line` in a file sets EA's path exactly as the binary spells it:
  `#line 75 "/mvp2004/source/common/geomlib/geomgroup.cpp"`.
- Later ones give only the number, directly above the assert that needs it.
- The file header says once that `__LINE__` values are EA's, set with `#line`.
- No `#line` anywhere else (not for layout, not for anything but a value the binary holds).
