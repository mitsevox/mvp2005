# ball.cpp discovery

2026-09-30. Research only: no new configured unit, source-link claim or counted exact
function. Scratch code is not an accepted reconstruction of EA's source.

EA's path string at 0x805CDCD4 is exactly
`C:/mvp2004/source/common/ai/physics/ball.cpp`. Functions 0x8018B9D8
(0xAF8 bytes) and 0x8018E0CC (0x390 bytes) reference it. The contiguous
interior 0x8018B9D8..0x8018E45C therefore belongs to this file: 28 functions,
10,884 bytes. Both original object edges remain open in `filemap.tsv`.

The candidate extent 0x80187190..0x80191AD8 has 114 functions, 43,336 bytes.
It starts at the large physics object's constructor and ends after a reflected
tunables allocator. That grouping, neighboring constructor forms and ascending
constant pools do not prove either original edge. No split has been made from it;
data and BSS ownership are also unresolved. See `docs/filemap.md` for the measured
limitations of these clues.

The reflected `cBall` configuration object is a different receiver. Its constructor
at 0x80191720 passes type ID 0x0F245603 to the reflection base. Registration at
0x80191764 names `Fatigue` at +4, `MinSpinRPM` at +0xC and `MaxSpinRPM` at +8.
These fields must not be used as the layout of the much larger physics object.
The retained disc DWARF has no complete definition of cBall, Ball or BallPlayer.
The physical object's original class name and inheritance declarations remain open.

## Stored direction and speed

The getter at 0x8018CA5C (28 bytes) copies three floats at +0x3FC, +0x400
and +0x404 to its three output addresses. Writer 0x8018B738 establishes their
meaning from the supplied velocity vector:

| Field | Calculation | Writer addresses |
|---|---|---|
| +0x3FC | Horizontal azimuth in radians, atan2(x, z) | 0x8018B888..0x8018B894 |
| +0x400 | Elevation in radians, atan2(y, sqrt(x*x + z*z)) | 0x8018B898..0x8018B8BC |
| +0x404 | Speed, sqrt(x*x + y*y + z*z) | 0x8018B8C0..0x8018B8DC |

The square-root wrapper at 0x804028E4 calls sqrt at 0x804101AC and rounds
to single precision. Caller 0x801DAECC supplies a vector formed from the scalar
at its argument's +0x48 and the direction at +0x4C, with position at +0x58.
UI callers scale the getter's third output by approximately 1/17.6 before integer
conversion (for example 0x800323A4..0x800323B4). This supports a display-speed
conversion; its display label has not been established, so physical units are
not assigned here.

A fresh blind reader independently recovered the two angles and vector magnitude
from anonymous getter/writer assembly and the DOL square-root implementation.
Launch-velocity interpretation additionally uses the caller evidence above.
The assembly does not settle pointer versus reference parameters, const qualification,
the declared return type or EA's original method spelling. `Ball` and
`GetLaunchParameters` in scratch are proposed names, not recovered symbols.

## Position setters and the receiver

0x8018D3E8 (40 bytes) clears the receiver's first word and copies a COORD3
to +0x60. The scalar overload candidate at 0x8018D410 (80 bytes) clears the same
word and stores x, y and z there. These are inherited position operations;
the cleared word must not be described as the ball's flight state.

The constructor at 0x80187190 stores the primary vtable at +0x98. That does
not mean the setters receive this+0x98: caller 0x801DAECC loads the ball pointer
from game+0x6CC at 0x801DAEF0, reads its vtable at 0x801DAEF4, obtains the
reference setter and zero this adjustment at 0x801DAEF8..0x801DAEFC, then adds
the adjustment and calls at 0x801DAF04..0x801DAF08. Both setter and getter use
the same allocation pointer. The secondary tables have adjustments -0xA0 and
-0x360; this still does not recover their base class names.

Base position operation 0x8035A6F4 has the same clear-and-copy instruction form
as 0x8018D3E8. Base constructor 0x8035A618 initializes position, rotation and
scale storage; its destructor installs the base vtable at +0x98. Point-transform
operations 0x8037D824 and 0x8037D8DC test the first word and rebuild the cached
transform at +0x20 through 0x8037D768 when it is zero. The rebuild uses position,
rotation and scale. Transform accessor 0x80256D40 additionally sets the word to
one after rebuilding (0x80256D60..0x80256D6C). This establishes transform-cache
validity as its behavioral meaning: the position setters invalidate that cache.
The point-transform operations rebuild without marking it valid; not every rebuild
sets the flag. The word's original declared type/name remain unresolved.

## Scratch measurements

All comparisons use existing ProDG 3.9.3 and target instruction bytes from the
original DOL. A single flag set is applied to the entire three-body scratch file.

| Candidate | Generic game O2 flags | Existing geomlib Os flags |
|---|---|---|
| Reference position setter | 10/10 instructions, 40 bytes identical | 10/10, 40 bytes identical |
| Scalar position setter | 20/20 instructions, 80 bytes identical | 20/20, 80 bytes identical |
| Direction/speed getter | 5/7 instructions; different FP register allocation | 7/7, 28 bytes identical |

Generic game flags are `-O2 -G0 -ffloat-store -fno-strength-reduce`;
geomlib flags are `-Os -G0 -ffloat-store`. These leaf results do not establish
the whole ball object's original flags. No flag or build configuration was changed.

The reference setter uses ordinary struct assignment. The scalar candidate uses a
local COORD3 followed by component copies: direct assignment does not reproduce
the target's two spill/reload layers, and aggregate initialization emits memset.
Its byte equality is recorded, but this source shape has not passed fidelity review;
no helper or redundant temporary is accepted on the strength of bytes alone.

Local inventories, source candidates and 21 leaf comparisons are in the ignored
`scratch/ball-boundaries`, `scratch/ball-types` and `scratch/ball-leaves` folders.
The coordinator's getter-only flag comparisons are in `scratch/ball-discovery`.
No game payload is included in this research note. Before any source is integrated,
resolve the original object extent and declarations, then run the configured combined
build, blind naming review and fresh hostile review. Branch exact counts remain unchanged.
