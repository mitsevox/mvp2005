# Independent EAGL compiler-policy audit

Verdict: a provisional shared `-O2 -G0 -finline-functions` policy is supported by measured behavior, subject to the combined checks below. The evidence does not distinguish that policy from `-O3 -G0`, prove EA's historical command line, or establish a complete source-linked transform object.

I inspected `scratch/diagnostics/source-order-flags.json`, the diagnostic source, the target object/assembly, `docs/compiler.md`, and the shared EaglLib configuration. The worktree contains two EAGL source translation units, viewport.cpp and transform.cpp; the remaining EAGL files are headers. All 30 diagnostic transform function bodies are identical to the current candidate after removing whitespace and comments. Their definition order follows the target function sequence, with the still-omitted Invert occupying its original assembly range.

I independently recompiled the full diagnostic transform source and full current viewport source with the repository's ProDG 3.9.3 driver, one flag policy per complete translation unit, and compared every emitted function with the original target object through the reviewed trial.py normalization:

| Shared candidate flags | Transform normalized-exact bodies | Viewport normalized-exact bodies |
| --- | ---: | ---: |
| `-O2 -G0` | 19/30 | 15/15 |
| `-O3 -G0` | 24/30 | 15/15 |
| `-O2 -G0 -finline-functions` | 24/30 | 15/15 |

The five transform gains are AppendScale, AppendRotate, AppendTranslate, AppendMatrix and PrependScale. No previously exact body is lost. This is concrete mechanism evidence: the target expands the small builder/copy and PostMult operations into the append methods, but retains a real PreMult call in the prepend methods; the target definition order places PreMult after those callers. Ordinary GCC automatic inlining with earlier visible definitions reproduces this pattern without per-function flags, attributes, source slices, or added match helpers.

The two automatic-inlining transform objects are byte-identical to each other (SHA-256 e35b06fb2f7b49da3f62993a850cfaccef6176b9ad9638db4d638182d91ccfeb). All three viewport objects are byte-identical (0b6c2cf6a9b7b2ee92fb6983287d41a3fa9f64a21e61aab9ca58343d3a3ec4ab). Therefore the extra inlining flag has direct evidence in a recovered unit and no observed effect on the other existing unit. Keeping O2 and adding the specifically measured automatic-inlining flag is the narrower explanation; O3 remains experimentally indistinguishable on these units.

Limits: normalized-exact instructions are not full object equivalence. trial.py normalizes literal/data names, and target relocation destinations must still be checked against their actual data. The automatic-inlining compiler also emits BuildQuatTrans after BuildRotate, despite its first position in the diagnostic source; the emitted function order therefore does not equal the original object order. Invert remains assembly, six written bodies remain partial, and viewport's constructed-global/data ownership remains unresolved. Neither the 24 score nor a normal NonMatching `main.dol: OK` overcomes those limits.

Required checks before retaining the policy:

1. Repair the source review findings, adopt one measured shared policy through cflags_eagl, and build both complete EAGL translation units together under the same configuration. Verify the actual commands contain no unit/function override. Repeat per-function and relocation comparison using the final source order and repaired bodies, rather than carrying forward this scratch diagnostic's scores.
2. Inspect the five gained call sites against original assembly, including retained PreMult calls, MultMatrix argument order, MEM_copy size/destination and literal bindings. Verify source symbols and omitted assembly ranges coexist without duplicate definitions, unresolved symbols, or altered cross-unit caller contracts.
3. Run the normal configured combined build and DOL verification, while explicitly reporting that NonMatching links original assembly. Any separate diagnostic source-linked build must verify the available complete objects/data it actually replaces; it cannot be described as full binary equivalence while partial functions and constructed-data placement remain unresolved. Preserve that distinction in progress and review claims.
4. Update docs/compiler.md with the complete-unit comparisons, five inlining gains, zero losses, indistinguishable O3/O2inline outputs, original-object-order limitation and exact chosen shared flags. The current sentence claiming EAGL was built "at -O2" is stronger than its previous viewport measurements support: those measurements did not test O3 or automatic inlining. Record the new policy as measured reconstruction evidence, not a proven historical flag string.

Recompile objects, .i/.s outputs and per-function results are in `scratch/transform-review/policy-audit/`; audit.json records the independently measured counts. This policy audit is separate from the pending source FIX recheck.
