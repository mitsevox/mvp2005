# Scoped inverse documentation review

Verdict: **SHIP**. Reviewed the root canonical files, not the historical candidate worktree. No source body or signature change is present in this scope. Previous source, tooling and shared compiler-policy verdicts stand.

Scope: `src/eagl/transform.cpp:379,384`, `src/eagl/transform.h:50–51`, `config/GV4E69/name_sources.tsv:647–651`, and all of `docs/transform-inverse.md`. No new items were raised against unchanged code. General `Invert` remains omitted and supplied by the original assembly.

## Independent evidence

Read original target instructions in `build/GV4E69/asm/eagl/transform.s`, including their encoded bytes. At 0x803DE824, f0 receives m[11]; at 0x803DE830, f6 receives m[13]. The multiply at 0x803DE844 computes m[11]*m[13]. At 0x803DE834, f27 holds m[8]*m[15]; subtraction at 0x803DE8B8 and multiplication at 0x803DE8CC form m[5]*(m[11]*m[13]-m[8]*m[15]). This term reaches f30 through 0x803DE8DC, 0x803DE8E8 and 0x803DE8EC.

Independently interpreted the load and arithmetic instructions from 0x803DE81C through 0x803DE8F4 as exact multivariate polynomials. Computed the mathematical determinant separately from the 24 signed permutations, without consulting another lane's implementation or proof script. The exact symbolic difference is:

```
target denominator - determinant = m[2]*m[5]*m[11]*(m[13]-m[12])
```

For the documented row-major witness `[1,0,1,0; 0,1,0,0; 0,0,1,1; 0,1,0,1]`, independent evaluation gives target f30=2 and mathematical determinant=1. The witness arithmetic uses small exactly representable integers, so fused or single-precision rounding does not explain the discrepancy. This proves the original denominator defect, without claiming gameplay reachability or complete correctness of the rest of the routine.

The branch sequence at 0x803DE8F8–0x803DE914 returns the computed denominator without touching the output for values strictly inside the two thresholds; `bge`/`ble` proceed with writes at equality. The write path divides by f30 at 0x803DE954. Thus the documented threshold applies to the computed denominator, not necessarily the true determinant.

## Changed wording and evidence

- PASS: output-wrapper comment at transform.cpp:379 accurately identifies the original routine and its computed-denominator early exit.
- PASS: in-place-wrapper comment at transform.cpp:384 explains the snapshot's purpose without promising a mathematical inverse.
- PASS: transform.h:50–51 identifies the observed index error and links the bounded evidence; the error polynomial vanishes when m[11]=0 as in ordinary affine layouts.
- PASS: name_sources.tsv:647–651 preserves the existing name/signature evidence tiers and correctly calls f1 the computed denominator. Guessed float return declarations remain explicitly guesses; no tier inflation.
- PASS: transform-inverse.md:7–41 accurately describes the arithmetic, witness and strict threshold boundaries. Lines 43–47 clearly correct the earlier mathematical-determinant description and preserve the original behavior.

Counts for this scoped change: FAIL=0; MATCH/fake notes=0; banned tricks=0; unexplained inconsistencies=0. Three changed comment blocks, five corrected evidence rows, one new bug document. No implementation proposal was accepted; the 30 written transform bodies and omitted general `Invert` remain unchanged. Exact scores did not determine this verdict.
