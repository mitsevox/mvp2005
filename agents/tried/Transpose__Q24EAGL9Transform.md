# Transpose__Q24EAGL9Transform

2026-09-30, Codex transform-recovery; shared EAGL `-O2 -G0`, one original transform.o.

Latest combined objdiff: 56.2%. Full unit includes31 functions and220 rodata bytes, remains NonMatching.

- Six standard pairwise swaps and deferred lower-triangle copies both emit25 instructions but12% instruction similarity; natural pairwise form/deferred alternative tested without volatile/register tricks.
- Actual six RTL pass dumps show load hoisting and register allocation; target reuses f8 for each upper triangle value, keeps six lower values live and defers opposite stores. No faithful improvement yet.

- Final canonical form is six ordinary named pairwise swaps; deferred-copy trial did not improve exactness and was reverted before review.

## Reusable swap temporary follow-up

2026-09-30. Earlier56.2% combined score describes six distinct savedXY/XZ/etc temporaries, now superseded by a proposed single reusable float saved.

- transpose-reuse.cpp: six ordinary pairwise swaps reusing one float saved;25/25 instructions identical under unchanged O2/G0. Raw objdiff100.0%. Root trial.py exit0.
- transpose-deferupper.cpp: six original lower values saved separately, lower destinations copied immediately, upper destinations deferred;25 instructions,12.0% normalized similarity; rejected.
- transpose-arraylower.cpp: saved[6] instead of six scalar lower values;33 instructions,3.4% normalized similarity and stack spills; rejected.

Genuine six-stage ProDG diagnostic emitted as scratch/diagnostics/transpose-reuse-rtl.i.{rtl,combine,regmove,sched,greg,sched2}. Target register lifetime fits a single reused scratch value; no volatile/register/artificial helper added. Unit remains NonMatching. Root owns source integration.

## Final combined checkpoint

2026-09-30, root measured the repaired full candidate after original definition order, shared EAGL O2/G0/finline-functions, and reviewed source corrections. This function's final combined objdiff: 100%. Supersedes earlier candidate scores above; diagnostic trial results remain historical.

Transform unit:25/31 exact,4760/7960 code bytes; remains NonMatching. Viewport:15/17 exact,5092 exact code bytes. Whole-build baseline1139 exact functions, candidate1165, zero previously exact target addresses lost. Explicit retail DOL verification: main.dol OK.
