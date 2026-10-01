# BuildSQT__Q24EAGL9Transformffffffffff

2026-09-30, Codex transform-recovery; shared EAGL `-O2 -G0`, one original transform.o.

Latest combined objdiff: 75.242424%. Full unit includes31 functions and220 rodata bytes, remains NonMatching.

- Standard named doubled quaternion products and row-major matrix stores; preserves exact arithmetic grouping and handedness.
- BuildQuatTrans requires a MATRIX3 temporary and copies the full translation row including w; direct builder first attempt incorrectly forced w1, corrected after direct target inspection before review.
- ExtractQuatTrans uses trace/largest-diagonal branches, zero-root guard, and full translation; source matrix temporary is natural, target retains a persistent pointer to it with different register allocation.
- Actual RTL/combine/regmove/sched/greg/sched2 dumps generated for entire current unit; unresolved inlining/temp addressing remains.

## Independent quaternion follow-up

2026-09-30, independent quaternion lane. Target signature and float argument order
confirmed from NFSU/MoH3 refnames; actual assembly inspected. Full-candidate baseline
has66/66 target instructions,42.4% instruction similarity. Scaling remains applied
to matrix rows, with scale as first fmuls operand. No scalar quaternion helper exists
in retained DWARF/refnames to justify introducing an inline conversion abstraction.
Actual rtl/combine/regmove/sched/greg/sched2 dumps emitted under existing `-O2 -G0`.

## Source-order diagnostic

2026-09-30, independent bounded follow-up to library-wide automatic inlining evidence.
Compiled the recovery lane's target-order `transform-source-order.cpp` under O2,
O3 and O2+finline-functions diagnostics. All four quaternion instruction streams
are identical across those three settings: BuildQuatTrans64/66, ExtractQuatTrans
167/173, BuildSQT66/66 and BuildQT49/49. Existing similarity scores are unchanged.
The O2+finline-functions compile emitted all six actual RTL stages. Persistent
MATRIX3 address registers remain absent; extraction still saves only r29..r31.
No quaternion conversion helper declaration was found in the available refnames
or libmatd.a debug export. Source definition order and automatic inlining explain
no additional quaternion bytes; this bounded avenue is exhausted without new source edits.
