# AppendMatrix__Q24EAGL9TransformPC7MATRIX4

2026-09-30, Codex transform-recovery; shared EAGL `-O2 -G0`, one original transform.o.

Latest combined objdiff: 28.043478%. Full unit includes31 functions and220 rodata bytes, remains NonMatching.

- Natural builder/copy plus PostMult/PreMult calls are retained as best faithful declaration form; shared -O2 does not inline them.
- Explicit inline declarations experimentally reproduced embedded instructions but suppressed required out-of-line definitions; rejected and reverted; no declaration-only inline remains.
- Explicit duplicate local matrix construction/direct multiplication measured worse or unchanged registers/frames; reverted to meaningful ordinary builder/copy calls.
- Whole-unit -O3 / -O2 -finline-functions retain out-of-line definitions and improve appends, but inline PreMult and lose previously exact PrependMatrix/PrependScale; neither flag adopted. All15 viewport functions remain instruction-exact in that diagnostic.

## Original definition-order follow-up

2026-09-30. Previous O3/finline trial lost prepend matches because the recovery source placed PreMult before its callers; it did not use original .text definition order. Scratch transform-source-order.cpp restores the observed original order; source-order-flags.json records the entire unit.

- Original-order O2/G0: this body remains partial;19/30 written functions exact.
- Original-order O3/G0 diagnostic: this body becomes instruction-exact;24/30 written functions exact, no prior exact match lost.
- Original-order O2/G0 plus finline-functions diagnostic: this body becomes instruction-exact;24/30 written functions exact, no prior exact match lost.

Earlier builders/PostMult/SetMatrix inline naturally while retaining their required standalone definitions. Final-defined PreMult remains an ordinary call. All15 viewport bodies were exact in preceding flag diagnostics. This is shared EAGL policy evidence; no per-function or per-object flags adopted, and unit remains NonMatching. Source integration and broader shared-policy verification belong to root.

## Final combined checkpoint

2026-09-30, root measured the repaired full candidate after original definition order, shared EAGL O2/G0/finline-functions, and reviewed source corrections. This function's final combined objdiff: 100%. Supersedes earlier candidate scores above; diagnostic trial results remain historical.

Transform unit:25/31 exact,4760/7960 code bytes; remains NonMatching. Viewport:15/17 exact,5092 exact code bytes. Whole-build baseline1139 exact functions, candidate1165, zero previously exact target addresses lost. Explicit retail DOL verification: main.dol OK.
