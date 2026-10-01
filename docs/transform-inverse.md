# Original Transform::Invert denominator discrepancy

Confirmed during the three-lane retry of the six remaining transform functions.
The implementation at 0x803DE7D0 remains assembly; the faithful decomp must preserve
its observed arithmetic, including this discrepancy.

The cofactor contributing the first-row m[2] term uses:

```
m[4] * (m[9] * m[15] - m[11] * m[13])
+ m[5] * (m[11] * m[13] - m[8] * m[15])
+ m[7] * (m[8] * m[13] - m[9] * m[12])
```

The second line needs m[11] * m[12] for the mathematical cofactor. The original
instead uses m[11] * m[13]. Target load/multiply at 0x803DE844 establishes that
product; the difference at 0x803DE8B8 and multiply at 0x803DE8CC feed it into the
returned denominator. Its contribution differs by
m[2] * m[5] * m[11] * (m[13] - m[12]).

A concrete row-major matrix distinguishes the original from a correct determinant:

```
1 0 1 0
0 1 0 0
0 0 1 1
0 1 0 1
```

Its mathematical determinant is 1; decoding and evaluating the original arithmetic
produces 2. Every intermediate in this witness is a small exactly representable
integer, so single-precision versus fused rounding cannot explain the difference.
Identity alone produces 1 in both calculations. The inverse lane and coordinator
independently traced this discrepancy; the hostile scoped review checks it again.
This is a bounded arithmetic check, not a Dolphin gameplay test.

Affine matrices normally have m[11] = 0, which makes this particular error term zero.
No claim is made about gameplay reachability or other errors. A near-zero test is
applied to the computed denominator, not necessarily the mathematical determinant;
the result matrix is left untouched when that computed value is strictly between
-1e-5 and +1e-5. Equality at either boundary proceeds with the routine.

Earlier blind-review and tried-ledger descriptions called the returned value a
mathematical determinant. Those are historical observations, corrected here and in
the current signature evidence. Inverse wrappers call the original routine; their
comments must not promise an exact mathematical inverse for arbitrary matrices.
The original bug is documented, not fixed in the faithful decomp.
