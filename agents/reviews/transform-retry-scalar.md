# Scalar quaternion / axis rotation retry

2026-09-30. Scratch-only whole-original-unit variants from reviewed be5011e.
Shared EAGL flags unchanged: -O2 -G0 -finline-functions. No canonical file edits.
Read every previous tried-ledger, quaternion findings/source-order diagnostics, and
rotation/composition diagnostic before selecting new forms. Reviewed map signatures
(BuildSQT in nfsu/moh3; BuildQT in ge/moh3/moh4) and own-disc DWARF MATRIX4/COORD4/Transform.
No quaternion conversion or identity helper invented.

## New measured attempts

Scores below are trial.py normalized instruction similarity, not objdiff.

| Variant | Function | Instructions target/actual | Similarity | Decision |
|---|---|---|---|---|
| retry-scalar-diaglocals.cpp | BuildQT | 49/49 | 71.4% | diagonal-value locals byte-identical to baseline; reject |
| retry-scalar-allcomponents.cpp | BuildQT | 49/49 | 71.4% | all nine meaningful rotation-component locals byte-identical; reject |
| retry-scalar-buildqt-matrixvalue.cpp | BuildQT | 49/75 | 24.2% | local complete MATRIX4 value stages nine outputs and copies integer words; reject |
| retry-scalar-buildsqt-matrixvalue.cpp | BuildSQT | 66/92 | 7.6% | local complete MATRIX4 value adds stack stores/integer copy; reject |
| retry-scalar-sqt-unscaledcomponents.cpp | BuildSQT | 66/66 | 42.4% | nine unscaled rotation component locals byte-identical; reject |
| retry-scalar-rotate-matrixvalue.cpp | BuildRotate | 98/118 | 28.7% | local MATRIX4 identity adds memset and copy; reject |
| retry-scalar-rotate-identityapi.cpp | BuildRotate | 98/81 | 52.5% | existing EA BuildIdentity API remains a real call, unlike target; reject |

The baseline BuildRotate still matches96/98 normalized instructions. All nonzero-angle
instructions are exact; only zero-angle identity scheduling differs. No arbitrary stores
were permuted, no definition moved outside original order, and no inline annotation added.
QT target chooses upper off-diagonal results before lower ones whereas compiler schedules
lower before upper from the current natural source. Whole-component meaningful locals do
not change this mechanism; source semantic grouping is eliminated before final scheduling.
No source patch is justified from these trials. Existing partial C remains clearer and closer.

## Actual compiler diagnostics

Saved dump.py compiles full variants with the configured compile_command and six genuine
ProDG passes: rtl/combine/regmove/sched/greg/sched2. Outputs named
retry-scalar-allcomponents-rtl.i.*, retry-scalar-sqt-unscaledcomponents-rtl.i.*,
and retry-scalar-rotate-identityapi-rtl.i.* plus verbose .s/.o. The unchanged scalar
local instruction streams and retained real BuildIdentity call agree with those dumps.
No download/tool friction occurred. All subprocesses finished; no background job remains.

## Independent operation-order audit and two additional source trials

A symbolic register readback of target objdump confirms the exact nine quaternion
coefficient expressions (operation grouping is retained, not simplified):

```
r00 = 1 - (qy*(qy+qy) + qz*(qz+qz))
r11 = 1 - (qx*(qx+qx) + qz*(qz+qz))
r22 = 1 - (qx*(qx+qx) + qy*(qy+qy))
r01 = qx*(qy+qy) + qw*(qz+qz)
r02 = qx*(qz+qz) - qw*(qy+qy)
r10 = qx*(qy+qy) - qw*(qz+qz)
r12 = qy*(qz+qz) + qw*(qx+qx)
r20 = qx*(qz+qz) + qw*(qy+qy)
r21 = qy*(qz+qz) - qw*(qx+qx)
```

Every QT and SQT target arithmetic instruction in this derivation is fadds/fsubs/fmuls;
there are **zero FMA contractions**. SQT multiplies each coefficient by its row scale
with the scale as the first multiplier. The canonical source arithmetic therefore
agrees, independently of its claimed comments or previous ledger.

- retry-scalar-buildqt-directproducts.cpp: removes nine named product locals and writes
  the conventional coefficient products directly, retaining the three doubled component
  locals;49/49instructions,34.7% similarity, rejected.
- retry-scalar-buildsqt-directproducts.cpp: same direct product form with row scaling;
 64/66instructions,24.6% similarity, rejected. Target needs four saved FP registers;
 direct form saves only three. This is not a source proposal.

BuildRotate target first executes fmuls f30,f1,f0 where f1 is input degrees and f0
loads pool0x8060C714 (word0x3c8efa35, float PI/180). It compares that result against
f29 from pool0x8060C718 (word0x00000000). Thus the guard is converted-radians zero,
not original-degrees zero; no guard correction is needed. Nonzero path operation
contraction already matches exactly in current source, including sqrt input and
Rodrigues coefficients.
