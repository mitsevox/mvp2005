# BuildQuatTrans__Q24EAGL9TransformPC6COORD4T1

2026-09-30, Codex transform-recovery; shared EAGL `-O2 -G0`, one original transform.o.

Latest combined objdiff: 61.090908%. Full unit includes31 functions and220 rodata bytes, remains NonMatching.

- Standard named doubled quaternion products and row-major matrix stores; preserves exact arithmetic grouping and handedness.
- BuildQuatTrans requires a MATRIX3 temporary and copies the full translation row including w; direct builder first attempt incorrectly forced w1, corrected after direct target inspection before review.
- ExtractQuatTrans uses trace/largest-diagonal branches, zero-root guard, and full translation; source matrix temporary is natural, target retains a persistent pointer to it with different register allocation.
- Actual RTL/combine/regmove/sched/greg/sched2 dumps generated for entire current unit; unresolved inlining/temp addressing remains.

## Independent quaternion follow-up

2026-09-30, independent quaternion lane. GE/MoH map signature retained with COORD4,
despite a separate Quaternion type also existing in the disc DWARF. The target genuinely
builds a36-byte MATRIX3 stack temporary, then embeds its nine elements. Baseline has
64/66 instructions,15.4% instruction similarity; target retains local matrix address
in r9, while direct-member source emits frame-relative stores. RTL dumps confirm the
natural local uses virtual stack register78 without a distinct persistent matrix pointer.
No invented pointer-taking inline helper or redundant local is added to manufacture it.

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
| complete COORD4 snapshot | 73 | 17.3% | wrong64-byte frame |
| typed COORD3 doubled vector | 67 | 19.5% | wrong64-byte frame |
| DWARF-native m33 view | 64 | 15.4% | byte-identical |

All local raw disc exports and maps searched again: no retained conversion helper
API establishes the persistent MATRIX3 pointer boundary. Real six-stage RTL dumps
emitted for each new representation. No helper or pointer invented to force it.
