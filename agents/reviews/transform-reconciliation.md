# Transform blind reconciliation

2026-09-30. Compared the independently written `blind.md` and F01..F31 mapping in
`reconciliation.json` with the current candidate at
`scratch/worktrees/transform-recovery/src/eagl/transform.cpp` and `transform.h`.
This is a meaning review; no compiler experiments or tracked edits were performed.
F03 (general inverse) has no C body in the candidate and is context only. The remaining
30 functions are the complete written-source review sample.

## Findings requiring local correction

1. **F24, AppendMatrix, transform.cpp:193:** the comment says it keeps the source
   intact even when it aliases this matrix. The code snapshots the source before
   multiplication, then overwrites this matrix with the result. If `matrix == &m`,
   the source object consequently changes on return. The actual alias guarantee is
   preservation of the source values *during composition*, not preservation of the
   aliased object afterward. Suggested intent comment:
   `// Snapshots the supplied matrix before applying it after this transformation.`
2. **F26, PrependMatrix, transform.cpp:200:** the same source-intact claim has the
   same alias overstatement. Suggested intent comment:
   `// Snapshots the supplied matrix before applying it before this transformation.`

Both claims were checked directly against the target assembly: AppendMatrix copies
the supplied 64 bytes to its stack snapshot, calls MultMatrix, then calls MEM_copy
with this as destination. PrependMatrix copies to its stack snapshot then calls
the current-matrix PreMult wrapper. The blind reviewer independently described both
as snapshots with self-composition support, without the source-preservation claim.

The previously accepted F02 Y-largest diagonal operand correction remains pending
in this candidate: target803DE6B0 evaluates Z+X, while source line412 evaluates X+Z.
That correction is documented separately in the quaternion lane's proposed patch.
It does not change the recovered mathematical operation or the blind naming agreement.

## Full sample reconciliation

| ID | Candidate name | Name/operation agrees | Comment agrees |
|---|---|---|---|
| F01 | BuildQuatTrans | Yes: quaternion matrix plus full final row | Yes |
| F02 | ExtractQuatTrans | Yes: trace/largest-diagonal conversion, full final row | Yes; operand correction noted above |
| F04 | TransformPoint(COORD3) | Yes: implicit w1, exact in-place guard | Yes |
| F05 | TransformPoint(COORD4) | Yes: all four components, no divide | Yes |
| F06 | TransformPoints | Yes: byte strides, zero means12, base-equality path | Yes |
| F07 | MultMatrix | Yes: result=left*right, separate output | Yes |
| F08 | BuildRotate | Yes: degree axis-angle, normalizes for nonzero angle | Yes |
| F09 | PostMult | Yes: current=current*argument | Yes |
| F10 | BuildScale | Yes: all four diagonal entries, including w | Yes |
| F11 | BuildTranslate | Yes: affine translation | Yes |
| F12 | BuildIdentity | Yes: 4x4 identity | Yes |
| F13 | mload44 | Yes: compact3x3 plus xyz to affine4x4 | Yes |
| F14 | BuildSRT | Yes: degree Euler rotation, scaled rows, independent translation | Yes |
| F15 | ExtractRotTrans | Yes: copies linear3x3 plus xyz; no scale decomposition claim | Yes |
| F16 | SetMatrix | Yes: full matrix copy | Yes |
| F17 | Inverse(result) | Yes: forwarding inverse wrapper | Yes |
| F18 | Inverse() | Yes: snapshot before inverse of current | Yes |
| F19 | Transpose() | Yes: six off-diagonal swaps | Yes |
| F20 | Transpose(source,result) | Yes: all16 elements, exact alias temporary | Yes |
| F21 | AppendScale | Yes: current*diagonal, scales columns | Yes |
| F22 | AppendRotate | Yes: current*axis-angle rotation | Yes |
| F23 | AppendTranslate | Yes: current*translation | Yes |
| F24 | AppendMatrix | Yes: snapshot then current*argument | **Overstates source preservation under alias** |
| F25 | PrependScale | Yes: diagonal*current, scales rows | Yes |
| F26 | PrependMatrix | Yes: snapshot then argument*current | **Overstates source preservation under alias** |
| F27 | TransformVector | Yes: implicit w0, exact in-place guard | Yes |
| F28 | BuildSQT | Yes: row-scaled quaternion matrix, xyz translation, w1 | Yes |
| F29 | BuildQT | Yes: quaternion matrix, xyz translation, w1 | Yes |
| F30 | PreMult(transform,source,result) | Yes: result=source*transform | Yes |
| F31 | PreMult(transform) | Yes: current=argument*current | Yes |

**At the inspected checkpoint:** semantic naming/operation agreement30/30;
comment agreement28/30, with the two local overstatements above. After those two
comment corrections, the independent sample would be30/30 for both. Do not record
that final score until the edited comments have been inspected.

## Confidence limits, not discrepancies

Blind semantic agreement does not prove original EA spellings or declared types.
The blind reviewer correctly withheld exact constness/reference qualification and
float-versus-void wrapper return certainty. The candidate header explicitly records
the inferred SetMatrix signature and guessed Inverse overload names/constness/returns.
Map-backed names may legitimately be more specific than blind descriptive proposals;
TransformPoint(COORD4), ExtractRotTrans and BuildSRT are semantically consistent.

Blind square-root/trig/memory-copy labels were algorithmic inferences except the
anonymous turn-based trig callees that were supplied. Current symbol declarations
and known target relocations separately supply those identities. No speculative
normal-transform, scale/shear-decomposition, quaternion-normalization, perspective-
divide or broad overlap guarantee was introduced into source comments.

## Final reinspection after local fixes

Both alias comments now say they snapshot the input before composing it after/before
the current transformation, allowing aliasing (current lines458 and472). Those statements
agree with the target and no longer claim the aliased object remains unchanged.
ExtractQuatTrans's Y-largest branch now uses Z+X (current line83), agreeing with the
target's cyclic diagonal sum. The former F02 arithmetic operand discrepancy is closed.

Reordering definitions to original target order changes no named operation. BuildRotate's
named sineAxisX/Y/Z values are respectively sine*x/y/z of the already normalized axis;
their six uses retain the original Rodrigues signs and products. The single saved scalar
in Transpose retains each off-diagonal value only until its corresponding pair has been
swapped; all six pairs and all four unchanged diagonal entries agree with F19. Its updated
comment correctly describes supplying the transpose without a separate output matrix.
SetMatrix's omitted comment is permitted NONE: its one-statement body and name fully
describe the copy, with no semantic claim removed that needed explanation.

**Final reconciled score: naming/operation30/30 right; comments30/30 right.** This is
semantic agreement against independent anonymous assembly, not proof of EA spellings,
not a claim of byte matching, and not a replacement for the hostile fidelity gate.
The earlier28/30 checkpoint and its two findings remain above as review history.
`accuracy-rows.tsv` contains exactly30 rows, in target address order, with the current
symbols resolved from the candidate symbols.txt. F03 remains excluded as assembly-only.
