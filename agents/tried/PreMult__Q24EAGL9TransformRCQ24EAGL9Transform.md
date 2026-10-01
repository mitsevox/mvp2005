# PreMult__Q24EAGL9TransformRCQ24EAGL9Transform

2026-09-30, Codex transform-recovery; shared EAGL `-O2 -G0`, one original transform.o.

Latest combined objdiff: 100.0%. Full unit includes31 functions and220 rodata bytes, remains NonMatching.

- First natural typed implementation matches100% in combined report; target relocations/call contracts inspected.

## Original definition-order follow-up

2026-09-30. Whole-unit scratch restores original target definition order. This emitted body remains exact individually under O2/G0, O3/G0, and O2/G0 plus finline-functions. Original-order O2 yields19/30 written exact; both automatic-inlining diagnostics yield24/30 exact without losing an existing exact function. PreMult is defined last, so preceding methods retain its ordinary call. source-order-flags.json records all functions. No shared flag policy adopted; original unit remains NonMatching.
