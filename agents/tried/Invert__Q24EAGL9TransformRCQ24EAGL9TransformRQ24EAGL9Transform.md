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
