# SetMatrix__Q24EAGL9TransformRC7MATRIX4

2026-09-30, Codex transform-recovery; shared EAGL `-O2 -G0`, one original transform.o.

Latest combined objdiff: 100.0%. Full unit includes31 functions and220 rodata bytes, remains NonMatching.

- Prior matrix-constructor hypothesis compiled27 instructions vs target26 and retained original this via mr r9,r3; target advances destination r3 and does not restore it.
- Ordinary void SetMatrix(const MATRIX4&) with m=matrix matches26/26; canonical setter supersedes guessed constructor.

- Ordinary const MATRIX4* setter also matches26/26 unchanged instructions. Pointer vs reference remains genuinely unsettled; canonical reference is retained as an explicit signature guess.
