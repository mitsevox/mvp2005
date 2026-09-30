# COORD4 as EA's plain struct (2026-09-30)

The disc's libmatd.a DWARF shows COORD4 as `typedef struct { float x, y, z, w; } COORD4;`
(InstanceCrowd.o .debug typedef 0x219ED, unnamed struct 0x1E3C; RQUAT, typedef 0x23BBA, names the
same struct), so EA's COORD4 had no constructors or operators. That DWARF also records realmath's
inline globals (DegToRad, RadToDeg) but no COORD4 operator or vector inline, so GeomLib's vector
maths were not in realmath's header: they are GeomLib's own, and their names are ours (T4).

Until this date `realmath.h` gave COORD4 constructors and operators, labelled a fake match. The
committed form now keeps COORD4 plain (`realmath.h`) and does the maths in inlines in `geomlib.h`.

## What the target shows

Each vector result in Transform, Precompute and PointOnAxis goes through three stages: the four
floats are stored to the stack (float-store copies of an inline's float parameters), copied into a
16-byte temporary, then copied component by component (lfs/stfs) to the destination, read through a
register holding the temporary's address. CopyFrom and SetScaled scale x, y, z through an inline
with a float parameter into a 12-byte temporary, then add w.

## Forms measured

objdiff percentages (report.json) unless marked "trial" (trial.py's difflib ratio, a different
scale). Functions not listed stayed at 100; geomgroup was 10/10 whenever measured.

| # | Form | CopyFrom | SetScaled | Transform | Precompute | PointOnAxis |
|---|---|---|---|---|---|---|
| 0 | Old fake match: COORD4 constructors + component-wise `operator=` + operators | 78.7 | 78.2 | 100 | 97.6 | 100 |
| a | Plain struct; operators build `COORD4 r; r.x = ...; return r;` | 66.5 | 72.1 | 47.7 | 60.7 | 35.4 |
| b | Plain struct; operators return `MakeCOORD4(float x, y, z, w)` | 48.6 | 56.5 | 49.4 | 63.1 | 41.3 |
| 1 | C-style out-pointer inlines (`v4set(r, x, y, z, w)`, `v4scale(r, v, s)`...), v4mult with an inner temporary | 58.9 | 77.0 | 91.5 | 76.2 | 99.6 |
| 2 | #1 with a temporary and copy inside every op | 58.9 | 77.0 | 90.0 | 72.7 | 64.7 |
| 3 | Value return `COORD4 r; return r;` plus struct assignment | | | 49.4 | | |
| 4 | Caller temporary, pointer v4mult without inner temporary, then v4copy | | | 88.4 | | |
| 5 | Pointer-returning helpers, `v4copy(&dst, v4mult(&t, ...))` | | | trial 63.8 | | |
| 6 | NRV makers (below) plus `v4copy(COORD4*, const COORD4&)` | 58.9 | 77.0 | 100 | 97.6 | 100 |
| 7 | Compound literal `return (COORD4){...}` | | | trial: worse, calls memset | | |
| 8 | `COORD4 r; ...; return r;` maker plus reference copy | | | trial 33.9 | | |
| 9 | #6 plus `v4copy(&mLocalBase, v4make(x*s, y*s, z*s, w))` | 78.8 | 78.2 | 100 | 97.6 | 100 |
| 10 | Named-return COORD3 scale, then a named-return COORD4 from COORD3 | 82.9 | 85.0 | 100 | 97.6 | 100 |
| 11 | COORD3 scale, then out-pointer `v4set3` into a local t | 95.8 | 95.7 | 100 | 97.6 | 100 |
| 12 | #11 with t in a block | 95.9 | 95.7 | 100 | 97.6 | 100 |
| 14 | #12 copied with `mLocalBase.x = t.x` ... | 96.8 | 97.9 | 100 | 97.6 | 100 |
| 15 | #12 copied through `COORD4& dst = mLocalBase` (NRV makers, not standard C++) | 100 | 100 | 100 | 97.6 | 100 |
| 16 | #15 without the block in SetScaled | 100 | 99.9 | 100 | 97.6 | 100 |
| 18 | Standard C++: reference out-parameters, one block per statement | | | trial 69.8 | | trial 86.1 |
| 19 | Standard C++: reference out-parameters returning `r&`, chained | | | trial 67.3 | | trial 64.4 |
| 21 | #15 with the ops returning a class derived from COORD4 (float constructor) through a maker | 88.8 | 90.6 | 78.2 | 81.3 | 64.6 |
| 22 | **#21 with each op constructing that class directly** | 100 | 100 | 100 | 97.6 | 100 |
| 23 | #22 with CopyFrom's block moved into an inline `ScalePoint(COORD4& dst, const COORD4& v, float s)` | 87.4 | 86.4 | 100 | 97.6 | 100 |
| 24 | #22 with CopyFrom/SetScaled as plain `v4set3(&mLocalBase, v4scale3(base, scale->x), base.w);` (no dst, no block) | 79.1 | 81.8 | 100 | 97.6 | 100 |
| 25 | #22 with a `GeomVec4 v4from3(const COORD3&, float w)` helper assigned to mLocalBase (coordinator's review) | 77.2 | 80.9 | 100 | 97.6 | 100 |

Committed: #22 (geomcone 7/8 exact; Precompute's 97.6 is its own open item,
`Precompute__8GeomCone.md`). Removing `GeomBox() {}`, which only COORD4's constructors needed, is
neutral.

## Literal sources of the key forms

**NRV makers** (rows 6 to 17): g++'s named return value extension, `T f(params) return r { body }`,
which names the return slot so the body writes the caller's temporary directly. GCC only, not
standard C++, so #6 and #15 are not standard C++ either:

```cpp
inline COORD4 v4make(float x, float y, float z, float w) return r { r.x = x; r.y = y; r.z = z; r.w = w; }
inline COORD4 v4scale(const COORD4& v, float s) { return v4make(v.x * s, v.y * s, v.z * s, v.w * s); }
inline void v4copy(COORD4* r, const COORD4& v) { r->x = v.x; r->y = v.y; r->z = v.z; r->w = v.w; }
// #6, PointOnAxis:  v4copy(out, v4sub(mBase, v4scale(mAxis, along)));
// #15, CopyFrom:    COORD4& dst = mLocalBase; { COORD4 t; v4set3(&t, v4scale3(base, scale->x), base.w); v4copy(&dst, t); }
//                   with v4scale3 returning COORD3 through an NRV v3make, v4set3(COORD4*, const COORD3&, float w)
```

**#1, out-pointer inlines** (PointOnAxis 99.6; measured twice, by the round-1 review and in-repo):

```cpp
inline void v4set(COORD4* r, float x, float y, float z, float w) { r->x = x; r->y = y; r->z = z; r->w = w; }
inline void v4sub(COORD4* r, const COORD4* a, const COORD4* b) { v4set(r, a->x - b->x, a->y - b->y, a->z - b->z, a->w - b->w); }
inline void v4scale(COORD4* r, const COORD4* v, float s) { v4set(r, v->x * s, v->y * s, v->z * s, v->w * s); }
// PointOnAxis, after `along = dist - mLength;`:
COORD4 axis, point;
v4scale(&axis, &mAxis, along);
v4sub(&point, &mBase, &axis);
out->x = point.x; out->y = point.y; out->z = point.z; out->w = point.w;
```

Copying the result with `*out = point;` instead turns the last step into an lwz/stw block copy
(91.4); the separate component stores are what give 99.6.

## Why #22

#15 needs a GCC-only extension; GeomLib is common code (`source/common`) that MVP also shipped on
Xbox, whose MSVC would reject it, so it is unlikely to be EA's. #22 gets the same scores in standard
C++: COORD4 and COORD3 stay EA's plain structs (as the DWARF shows) and GeomLib's maths returns
small classes built on them (`GeomVec4`, `GeomVec3`, names T4). Nothing shows EA deriving from
COORD3 or COORD4, so the classes are a labelled `// fake match:` in `geomlib.h`; small classes with
a 4-float constructor are an EA habit elsewhere (GeomPlane at 0x8035F4A4, and 0x80379394), which is
context, not proof.

Rule 3's 5-point reopen: #1 is within 5 points on PointOnAxis alone (99.6). It is not used there
because the unit keeps one vector idiom (rule 5): #1 needs a second, parallel set of invented
out-pointer helpers for the same operations, is itself a fake match of the same kind, and is still
not exact. On every other function the class form wins by more than 5 points.

The dst alias and block in CopyFrom and SetScaled are labelled `// fake match:` too: they only
order loads and stores. The natural forms lose: #24 (79.1 / 81.8), #25 (77.2 / 80.9), #23 (87.4 /
86.4), #12 (95.9 / 95.7).
