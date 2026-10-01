# BuildRotate__Q24EAGL9Transformffff

2026-09-30, Codex transform-recovery; shared EAGL `-O2 -G0`, one original transform.o.

Latest combined objdiff: 97.0102%. Full unit includes31 functions and220 rodata bytes, remains NonMatching.

- Natural Rodrigues matrix with degree conversion, real sinf/cosf/sqrtf calls, explicit identity zero-angle path; trial98/98instructions86.7% alike, objdiff97.0102%.
- Genuine RTL/combine/regmove/sched/greg/sched2 dumps generated in scratch/diagnostics/transform-rtl.i.*; divergence consists of identity scheduling and sine-axis product register allocation. No forcing adopted.

## Rotation-product follow-up

2026-09-30. Scratch-only variants; unchanged shared O2/G0. Each result below is normalized instruction similarity, distinct from objdiff. Target98 instructions.

- rotation-plain-weighted_scalar.cpp: 98 instructions, 86.73469%; rejected; no exact improvement beyond the scalar proposal.
- rotation-sin_vector-weighted_vector.cpp: 118 instructions, 19.44444%; rejected; no exact improvement beyond the scalar proposal.
- rotation-sin_scalar-weighted_vector.cpp: 108 instructions, 19.41748%; rejected; no exact improvement beyond the scalar proposal.
- rotation-sin_scalar-weighted_scalar.cpp: 98 instructions, 97.95918%; rejected; no exact improvement beyond the scalar proposal.
- rotation-sin_vector-weighted_scalar.cpp: 108 instructions, 19.41748%; rejected; no exact improvement beyond the scalar proposal.
- rotation-sin_vector-plain.cpp: 108 instructions, 19.41748%; rejected; no exact improvement beyond the scalar proposal.
- rotation-plain-weighted_vector.cpp: 108 instructions, 19.41748%; rejected; no exact improvement beyond the scalar proposal.
- rotation-sin_scalar-plain.cpp: 98 instructions, 97.95918%; natural three sine-axis scalar products proposed, remaining identity scheduling differs.

Natural identity branch alternatives measured individually on the sine-axis scalar proposal:

- rotation-identity-reverse.cpp: 98 instructions, 86.73469%; rejected.
- rotation-identity-zeros_first.cpp: 98 instructions, 94.89796%; rejected.
- rotation-identity-diagonal_first.cpp: 98 instructions, 95.91837%; rejected.
- rotation-identity-last_row_first.cpp: 98 instructions, 95.91837%; rejected.
- rotation-identity-w_first.cpp: 98 instructions, 96.93878%; rejected.
- rotation-chain_diagonal.cpp:98 instructions,94.89796%; rejected.
- rotation-chain_zero.cpp:98 instructions,88.77551%; rejected.
- rotation-early_return.cpp:98 instructions,97.95918%; remains partial, no improvement over ordinary if/else.

Raw objdiff for scalar-product proposal:97.418365%, compared with initial97.0102%. Meaningful proposed locals are sineAxisX/Y/Z. Existing actual six ProDG RTL dumps expose scheduler differences. No arbitrary store permutations, register coercion, helper or flags adopted.

## Final combined checkpoint

2026-09-30, root measured the repaired full candidate after original definition order, shared EAGL O2/G0/finline-functions, and reviewed source corrections. This function's final combined objdiff: 97.82653%. Supersedes earlier candidate scores above; diagnostic trial results remain historical.

Transform unit:25/31 exact,4760/7960 code bytes; remains NonMatching. Viewport:15/17 exact,5092 exact code bytes. Whole-build baseline1139 exact functions, candidate1165, zero previously exact target addresses lost. Explicit retail DOL verification: main.dol OK.

## Fresh three-lane retry

Whole original unit, shared O2/G0/finline-functions, reviewed be5011e baseline.
Scores are normalized instruction similarity, not objdiff; no new match.

| Natural trial | Instructions | Similarity | Rejected because |
| --- | ---: | ---: | --- |
| whole MATRIX4 identity value | 118 | 28.7% | memset and copy |
| existing BuildIdentity call | 81 | 52.5% | call retained rather than inline stores |

Target guard uses converted radians, not input degrees. Nonzero branch is exact;
two identity-branch scheduling differences remain. Actual RTL diagnostics emitted.
