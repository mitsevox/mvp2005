# GeomCone::CopyFrom (0x802E22EC), and GeomCone::SetScaled (0x802E247C)

Both have the same miss, so this entry covers both.

**Committed now** (2026-09-30, after the COORD4 layout check): `mLocalBase = COORD4(base.x *
scale->x, base.y * scale->x, base.z * scale->x, base.w);`, 78.7% (CopyFrom) and 78.2% (SetScaled),
objdiff. It is one stage short of the target (no COORD3 temporary, no home for scale->x), and the
source says so.

**Why not 95.9%.** Both 95.9% / 95.7% forms read COORD4's x, y, z as a COORD3 in place:
- `(const COORD3&)base`: a cast to a type the value is not, banned by `docs/fidelity.md`.
- COORD4 derived from COORD3 plus `const COORD3& point = base; COORD4(point * s, base.w)`: the
  same code with no cast (committed in #53), undone after the check: the nfsmw decomp
  (dbalatoni13/nfsmw @ 9ca26bc) declares COORD4 as a typedef of UMath::Vector4, a standalone
  x, y, z, w struct with no base (`UVectorMath.h`, `UTypes.h`). No EA build shows a COORD4 built
  on COORD3. That is NFS's math layer rather than realmath, so it is support, not proof; the
  derivation had no evidence of its own beyond the codegen.
A match now needs a form that fits a standalone COORD4 and still gives the COORD3-shaped stage.

**Other cast-free forms scored** (objdiff, CopyFrom / SetScaled):
- The four components straight into `COORD4(x, y, z, w)` through the `base` reference: 78.7 / 78.2
  (committed). Without the reference, `src->mLocalBase.x` etc.: 79.4 / 79.5.
- The same with `float s = scale->x;` first: 83.8 / 84.8 (s homes like the operator's float
  parameter); 83.1 / 82.2 when mLength uses s too. Not committed: a local that is there only to
  get the home back is an unexplained forced shape (checklist item 6).
- `COORD4(COORD3(base.x * s, base.y * s, base.z * s), base.w)`: 78.8 / 81.9 (a COORD3 built only
  to feed the constructor).
- `COORD4(COORD3(base.x, base.y, base.z) * s, base.w)`: 71.6 / 73.5 (an extra copy stage).
- `mLocalBase = src->mLocalBase * s; mLocalBase.w = src->mLocalBase.w;`: 87.9 / 88.5, but it
  multiplies w too, which the target never does: not the game's operations, so not committed.
- Component-wise `mLocalBase.x *= s` after a copy: trial.py 40.4% (CopyFrom). Four separate
  assignments `mLocalBase.x = src->mLocalBase.x * s` ...: trial.py 48.0%.

**Before the fix.** Best was 95.9% (CopyFrom), 95.7% (SetScaled), objdiff; 6 and 7 instructions
differ, all in one copy.

**What is left.** `mLocalBase = <scaled COORD4 temp>` copies the temp at sp+8 into this+0x378. The
target loads all four floats first (y, x, w, z) and then stores x, w, y, z; ours stores x and y
before loading z and w. Everything before and after is identical, including the stack slots.

**Source shape that got this far** (geomcone lane, 2026-09-30):
`const COORD4& base = src->mLocalBase; mLocalBase = COORD4((const COORD3&)base * scale->x, base.w);`
with `COORD3 operator*(const COORD3&, float)` and `COORD4(const COORD3&, float)`. The slot order
(COORD3 temp 0x18, the float parameter's home 0x28, the product homes 0x30..0x38, w's home 0x40)
proves the float parameter belongs to a COORD3 operator, and w is read through the same pointer
as x, y, z (hence the reference). The cast is the weak part; a COORD4 that derives from COORD3
gives the same code.

**Tried, no better:**
- COORD4(x*s, y*s, z*s, w) directly (one stage too few).
- A ScalePoint(const COORD4&, float) inline (float home lands before the COORD3 temp).
- COORD4 derived from COORD3, with COORD3 copy constructor; COORD3 operator= only (the implicit
  COORD4 operator= is then called out of line).
- COORD4 operator= taking its argument by value; returning void; all 24 statement orders
  (xyzw is best; the others also break Transform and PointOnAxis).
- A named local COORD4 then `mLocalBase = local` (slots move).
- A SetBase(const COORD4&) inline; an inline helper writing through a COORD4& out parameter.
- `cone` declared before the assert; no `base` reference (w then loads from cone+0x384).
- Implicit (no user) operator=: gives exactly the target's load/store order but with lwz/stw.
  So the target's copy behaves like a block copy done in float registers; the next idea is
  whatever makes GCC 2.95 treat the temp and the member as unrelated memory (alias sets).
- -O2 / -O1 variants of the flags: worse everywhere.
