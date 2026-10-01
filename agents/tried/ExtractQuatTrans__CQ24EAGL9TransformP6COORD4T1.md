# ExtractQuatTrans__CQ24EAGL9TransformP6COORD4T1

2026-09-30, Codex transform-recovery; shared EAGL `-O2 -G0`, one original transform.o.

Latest combined objdiff: 68.15607%. Full unit includes31 functions and220 rodata bytes, remains NonMatching.

- Standard named doubled quaternion products and row-major matrix stores; preserves exact arithmetic grouping and handedness.
- BuildQuatTrans requires a MATRIX3 temporary and copies the full translation row including w; direct builder first attempt incorrectly forced w1, corrected after direct target inspection before review.
- ExtractQuatTrans uses trace/largest-diagonal branches, zero-root guard, and full translation; source matrix temporary is natural, target retains a persistent pointer to it with different register allocation.
- Actual RTL/combine/regmove/sched/greg/sched2 dumps generated for entire current unit; unresolved inlining/temp addressing remains.

## Independent quaternion follow-up

2026-09-30, independent quaternion lane. Baseline167/173 instructions,24.1% instruction
similarity. Aggregate MATRIX3 initializer plus cyclic Y diagonal sum emits195 instructions,
16.8%, and is rejected. Direct-member construction plus cyclic Y diagonal sum retains
167 instructions,24.1%; that one operand correction is proposed because target803DE6B0
computes Z+X, matching the cyclic sums X:(Y+Z),Y:(Z+X),Z:(X+Y). sqrtf relocations remain
sqrtf, and constant relocations preserve0/1/half. Natural source has three saved integer
registers; target has four, retaining MATRIX3's address in r31 across sqrtf calls. Actual
six-stage RTL diagnostics confirm direct-member accesses lose that persistent pointer.
No speculative helper, pointer pun, register variable or compiler flag is proposed.

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

## Final combined checkpoint

2026-09-30, root measured the repaired full candidate after original definition order, shared EAGL O2/G0/finline-functions, and reviewed source corrections. This function's final combined objdiff: 68.184975%. Supersedes earlier candidate scores above; diagnostic trial results remain historical.

Transform unit:25/31 exact,4760/7960 code bytes; remains NonMatching. Viewport:15/17 exact,5092 exact code bytes. Whole-build baseline1139 exact functions, candidate1165, zero previously exact target addresses lost. Explicit retail DOL verification: main.dol OK.
