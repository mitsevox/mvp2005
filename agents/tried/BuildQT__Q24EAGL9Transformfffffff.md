# BuildQT__Q24EAGL9Transformfffffff

2026-09-30, Codex transform-recovery; shared EAGL `-O2 -G0`, one original transform.o.

Latest combined objdiff: 80.55102%. Full unit includes31 functions and220 rodata bytes, remains NonMatching.

- Standard named doubled quaternion products and row-major matrix stores; preserves exact arithmetic grouping and handedness.
- BuildQuatTrans requires a MATRIX3 temporary and copies the full translation row including w; direct builder first attempt incorrectly forced w1, corrected after direct target inspection before review.
- ExtractQuatTrans uses trace/largest-diagonal branches, zero-root guard, and full translation; source matrix temporary is natural, target retains a persistent pointer to it with different register allocation.
- Actual RTL/combine/regmove/sched/greg/sched2 dumps generated for entire current unit; unresolved inlining/temp addressing remains.

## Independent quaternion follow-up

2026-09-30, independent quaternion lane, whole-unit `-O2 -G0` trials.
Natural baseline is49/49 target instructions,71.4% instruction similarity (a different
metric from objdiff's existing80.55102%). Meaningful diagonal/upper/lower store grouping
and diagonal-product-first declarations each produce the identical baseline object.
A MATRIX3 rotation followed by explicit embedding produces58 instructions,15.0%
similarity, with nine unwanted stack stores. All three alternatives are rejected.
Actual rtl/combine/regmove/sched/greg/sched2 dumps emitted; no flags or forcing helpers adopted.

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

## Fresh three-lane retry

Whole original unit, shared O2/G0/finline-functions, reviewed be5011e baseline.
Scores are normalized instruction similarity, not objdiff; no new match.

| Natural trial | Instructions | Similarity | Rejected because |
| --- | ---: | ---: | --- |
| diagonal locals | 49 | 71.4% | byte-identical |
| nine component locals | 49 | 71.4% | byte-identical |
| whole MATRIX4 value | 75 | 24.2% | stack stores and integer copy |
| direct product expressions | 49 | 34.7% | worse scheduling |

Independent target readback confirms all nine quaternion arithmetic expressions and
row-scale operand order; neither target contains fused multiply-add contractions.
Real six-stage ProDG dumps verify the new source-lifetime experiments.
