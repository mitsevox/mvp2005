# ViewPort sphere/frustum test, 0x803E1850

2026-09-30, frustum-sphere lane. Provisional method symbol until shared headers are integrated.

| Attempt | Flags | Trial result | Finding |
| --- | --- | --- | --- |
| Natural near/far expressions, signed side distance local | -O2 -G0 -ffloat-store -fno-strength-reduce | 37.1%, 88 / 79 instructions | Named floats are homed to the stack; retail retains them in FPRs. |
| Same source, library-style flags | -O2 -G0 | 86.1%, 79 / 79 | Layout and flow match; expression results use f0 where retail uses f13. |
| One signed plane-distance local throughout, compound normalization assignments | -O2 -G0 | 97.5%, 79 / 79 | Only far-plane addition/negation register operands differ. |
| Save far-plane signed distance, then negate it | -O2 -G0 | 100.0%, 79 / 79, instructions identical | A MATCH note records the single-expression alternative's two register differences. |

Relocations and the complete linked DOL still require integration and verification.
Provisional header/compiler scaffolding is not final naming evidence.
