# Transform::Invert matching trials

Target 0x803DE7D0, 1392 bytes / 348 instructions. All trials used the unit's shared
ProDG 3.9.3 `-O2 -G0`; no production flags or tracked files were changed.
Trials are isolated under scratch/transform-inverse and use the main lane's canonical
Transform / MATRIX4 declarations.

The target computes a full 4x4 determinant, returns it unchanged, and performs no output
stores when `-1.0e-5f < determinant < 1.0e-5f`. At either boundary it proceeds.
Output math is the adjugate divided by the determinant. Its determinant expression
expands along a row; its adjugate uses column-expanded 3x3 minors. Algebraic equivalence
alone does not establish matching floating-point grouping, FMA or rounding.

| Source trial | Instructions (target 348) | Literal instruction similarity |
|---|---:|---:|
| column-cyclic-direct | 350 | 6.5902579% |
| column-cyclic | 354 | 3.1339031% |
| column-direct | 269 | 3.5656402% |
| column-standard | 271 | 3.2310178% |
| column | 393 | 5.6680162% |
| cyclic-column-first-column | 347 | 5.1798561% |
| cyclic-column-first-row | 344 | 6.0693642% |
| cyclic-column-last-column | 354 | 16.8091168% |
| cyclic-column-last-row | 346 | 6.3400576% |
| cyclic-row-first-column | 356 | 5.3977273% |
| cyclic-row-first-row | 344 | 5.2023121% |
| cyclic-row-last-column | 346 | 4.8991354% |
| cyclic-row-last-row | 354 | 3.1339031% |
| inverse | 267 | 4.5528455% |
| row-direct | 264 | 4.5751634% |

`inverse.cpp`: row-expanded cofactors, subtractive middle term, all cofactor values
formed before stores. `column.cpp`: cyclic positive expressions with negative cofactor
signs distributed by reversing inner subtractions. `column-standard.cpp`: column
expansion with subtractive middle terms and outer negative sign on odd cofactors.
`column-direct.cpp` / `row-direct.cpp`: explicit source scalar snapshots followed by
direct output stores. `column-cyclic.cpp`: column expansion with cyclic positive terms
and outer negative odd cofactors. `column-cyclic-direct.cpp`: scalar source snapshot and
direct output stores. `cyclic-*`: measured row/column cofactor declaration order,
last diagonal cofactor at first/last, and row/column output store order. These remain
scratch diagnostics, not proposals to disguise a low-fidelity replacement as EA code.

Best literal similarity was 16.8091168%, 354 instructions. It remains far from faithful
instruction/FMA ordering. Recommendation: keep the complex Invert implementation in
assembly rather than commit an algebraically equivalent replacement.

Actual compiler RTL diagnostics were emitted for the best trial using `-dr -dc -dN
-dS -dg -dR -fverbose-asm`: initial RTL, combine, regmove, both scheduler stages and
global allocation. Files are inverse-rtl.i.{rtl,combine,regmove,sched,greg,sched2} and
inverse-rtl.s. No scheduler or compiler flag changes were adopted.

## Inverse wrapper, 0x803DFAB4

`Transform source = *this; return Invert(source, *this);` produced the target's exact
37-instruction snapshot/call wrapper. Raw trial similarity was94.5945946% because
target and candidate local branch and callee symbols were not yet reconciled. The
wrappers-only trial (no Invert source definition) was compared after normalizing the
target branch to Inverse__Q24EAGL9Transform and callee to the map-proven Invert symbol:
37/37 instructions and call relocation identical. No invented helper or forced shape.
Return type float is a separate inference: the callee leaves determinant in f1 and the
wrapper forwards it, but existing callers ignoring f1 cannot distinguish void source.
No own-name evidence changes were made here; the main lane owns those rows.

0x803DFA94 is an8-instruction direct-call wrapper, but the reference maps supplied no
name there. This lane did not invent a two-argument method or modify canonical headers.


### Additional direct wrapper trial, 0x803DFA94

Root requested measuring the explicitly guessed overload:
`float Transform::Inverse(Transform& result) const { return Invert(*this, result); }`.
A scratch-only copy of the canonical header gained that declaration. This generated
8/8 exact instructions (32 bytes), including the map-proven Invert callee relocation;
the in-place sibling remained37/37 exact. Both signatures' float return is inferred,
not proven by the wrappers or callers which ignore f1. The overloaded name and const
qualifier at803DFA94 are T4 guesses; the operation/receiver/output argument ordering
is proven by the unchangedr3,r4 direct forwarding call. Header/source paths:
scratch/transform-inverse/wrapper-header.h and wrappers-both.cpp. No canonical header
was edited by this lane.

## Retry behavior correction

Original arithmetic contains an index discrepancy: m[11]*m[13] replaces
m[11]*m[12] in one determinant cofactor. docs/transform-inverse.md records
independent instruction traces and an exact-integer counterexample: true determinant1,
original computed denominator2. Earlier mathematically correct adjugate trials cannot
reproduce this behavior. The singular interval applies to the computed denominator.
Current retry uses shared O2/G0/finline-functions, original function order and the
preserved discrepancy; final new attempts are logged below when the lane finishes.
## 2026-09-30 retry: original unit order, measured shared inlining, original index discrepancy

All 33 measured attempts are scratch-only full canonical translation-unit variants, with Invert inserted at its original position. They use the production shared `-O2 -G0 -finline-functions`; no flags, canonical source, headers, build configuration or split ownership were changed.

### New verified semantic evidence

The earlier summary that this computes the mathematical determinant was incomplete. The target denominator differs algebraically from the true determinant by `m[2] * m[5] * m[11] * (m[13] - m[12])`. Target `0x803DE844` computes `m[11] * m[13]`; `0x803DE8B8` reuses it in the minor multiplied by `m[5]`, where the mathematical formula needs `m[11] * m[12]`. This is preserved as an EA indexing bug in every new denominator trial.

Exact-integer witness: identity with `m[2] = m[11] = m[13] = 1` and `m[12] = 0` has determinant 1; the target denominator is 2. The root independently interpreted the original determinant PPC sequence and confirmed both values. Ordinary affine matrices have `m[11] = 0`, masking the discrepancy.

The target returns its computed denominator in f1, checks the same strict near-zero interval, and divides a mathematically correct adjugate by that denominator. `analyze.py` symbolically follows every original arithmetic/load/store instruction and proves all 16 numerator polynomials equal the adjugate entries, with exactly the denominator discrepancy above. This polynomial audit does not erase FP grouping, FMA or rounding differences. Its expression trees retain the original arithmetic grouping; source trials still need literal instruction equivalence.

### Measurements

| Scratch trial | Literal instructions / target348 and similarity |
|---|---|
| retry-inverse-bug-cyclic-column-first-column.cpp | 347 instructions (target 348), 15.8% alike |
| retry-inverse-bug-cyclic-column-first-row.cpp | 347 instructions (target 348), 14.7% alike |
| retry-inverse-bug-cyclic-column-last-column.cpp | 352 instructions (target 348), 25.4% alike |
| retry-inverse-bug-cyclic-column-last-row.cpp | 343 instructions (target 348), 16.5% alike |
| retry-inverse-bug-cyclic-row-first-column.cpp | 350 instructions (target 348), 14.0% alike |
| retry-inverse-bug-cyclic-row-first-row.cpp | 360 instructions (target 348), 11.6% alike |
| retry-inverse-bug-cyclic-row-last-column.cpp | 337 instructions (target 348), 24.2% alike |
| retry-inverse-bug-cyclic-row-last-row.cpp | 341 instructions (target 348), 13.1% alike |
| retry-inverse-adjugate-row.cpp | 372 instructions (target 348), 11.7% alike |
| retry-inverse-transform-row.cpp | 372 instructions (target 348), 11.7% alike |
| retry-inverse-snapshots-row.cpp | 316 instructions (target 348), 1.8% alike |
| retry-inverse-adjugate-column.cpp | 363 instructions (target 348), 15.2% alike |
| retry-inverse-transform-column.cpp | 363 instructions (target 348), 15.2% alike |
| retry-inverse-snapshots-column.cpp | 316 instructions (target 348), 1.8% alike |
| retry-inverse-minor-locals.cpp | 353 instructions (target 348), 18.0% alike |
| retry-inverse-expansion-locals.cpp | 353 instructions (target 348), 22.3% alike |
| retry-inverse-scaled-scalar-column.cpp | 343 instructions (target 348), 16.2% alike |
| retry-inverse-scaled-matrix-column.cpp | 370 instructions (target 348), 15.6% alike |
| retry-inverse-scaled-direct-column.cpp | 407 instructions (target 348), 10.9% alike |
| retry-inverse-scaled-scalar-row.cpp | 337 instructions (target 348), 24.2% alike |
| retry-inverse-scaled-matrix-row.cpp | 362 instructions (target 348), 11.5% alike |
| retry-inverse-scaled-direct-row.cpp | 407 instructions (target 348), 10.9% alike |
| retry-inverse-form-column-standard.cpp | 279 instructions (target 348), 15.3% alike |
| retry-inverse-form-column.cpp | 398 instructions (target 348), 14.5% alike |
| retry-inverse-form-column-direct.cpp | 274 instructions (target 348), 15.1% alike |
| retry-inverse-form-column-cyclic.cpp | 341 instructions (target 348), 13.1% alike |
| retry-inverse-form-column-cyclic-direct.cpp | 336 instructions (target 348), 13.5% alike |
| retry-inverse-form-row-direct.cpp | 271 instructions (target 348), 16.8% alike |
| retry-inverse-form-inverse.cpp | 277 instructions (target 348), 17.3% alike |
| retry-inverse-post-snapshot-scalars-column.cpp | 355 instructions (target 348), 15.1% alike |
| retry-inverse-post-snapshot-matrix-column.cpp | 361 instructions (target 348), 4.8% alike |
| retry-inverse-post-snapshot-scalars-row.cpp | 336 instructions (target 348), 13.5% alike |
| retry-inverse-post-snapshot-matrix-row.cpp | 352 instructions (target 348), 18.0% alike |

These combine the new denominator evidence and current shared compiler policy with previously recorded cyclic formulas, conventional row/column traversal, meaningful minor/expansion locals, scalar inverse values, MATRIX4/Transform adjugate storage, and input snapshots. The earlier diagonal-first diagnostic shapes and traversal alternatives remain measurements, not proposed store-order tuning. Direct-output variants do not retain the target’s full input/output alias behavior and are rejected regardless of their scores. Pre-branch row/column snapshot variants are text-identical diagnostics; both measurements are listed transparently.

Best remains the ordinary scalar cyclic-cofactor form at 352 instructions / 25.4% literal similarity. Real ProDG RTL initial, combine, regmove, first scheduling, global allocation and second scheduling dumps were regenerated for this trial: `retry-inverse-rtl.i.{rtl,combine,regmove,sched,greg,sched2}`. They show global register allocation and spill scheduling remain far from target after the correct denominator graph is restored; neither arbitrary statement-order tricks nor register/compiler switches were adopted.

No candidate is proposed for canonical source. Keep Invert omitted and assembly-linked; retain the verified indexing-bug evidence for future recovery and correct prior review prose claiming an unqualified mathematical determinant. No new exact functions, no tracked shared-file edits, no spawned processes left running.

Saved C-generation scripts: `generate.py`, `structured.py`, `detlocals.py`, `scaled.py`, `forms.py`, `post-snapshots.py`. Each emitted variant has a saved source diff and individual trial diff. Symbolic analysis and ledger generation are non-C scripts. No tool/download/deletion friction occurred in this retry.
