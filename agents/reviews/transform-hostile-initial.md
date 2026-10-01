1 PASS
2 PASS
3 PASS
4 PASS
4b PASS
5 PASS
6 PASS
7 FAIL src/eagl/transform.cpp:196: AppendMatrix calls SetMatrix while the otherwise parallel PrependMatrix at line 203 assigns m directly, with no explanation; the original AppendMatrix also contains an inline aggregate copy, not a SetMatrix call -> use appended.m = *matrix consistently with prepended.m = *matrix, or document evidence for retaining the differing source forms.
8 FAIL src/eagl/transform.cpp:180: parameter spelling transform, also at lines 187 and 434 and in transform.h, has no parameter/local tier-and-evidence row in name_sources.tsv; the mangled function-name rows establish the declaration, not the argument spelling -> keep the readable name but record its spelling as a T4 guess tied to the input matrix contract.
9 PASS
10 PASS
11 PASS
12 PASS
13 FAIL src/eagl/transform.cpp:51: "Copies a supplied homogeneous matrix without changing its convention" and line 228 "Exchanges rows and columns in place" restate SetMatrix and Transpose rather than explain a constraint or purpose -> omit these redundant comments; retain the meaningful alias, stride, angle-unit and singularity contracts elsewhere.
14 PASS
15 PASS
16 PASS
17 PASS
18 PASS
19 PASS
MATCH notes: 0, fake match notes: 0, banned tricks: 0, inconsistencies: 1 unexplained.
Verdict: FIX
MultMatrix is the ugliest body, but a fully expanded four-by-four product with the retained MATRIX4 signature is ordinary period graphics code, not an AI tell. ExtractQuatTrans is the other worst body; its trace/largest-diagonal branches and saved MATRIX3 follow the original algorithm cleanly. All 30 written bodies, the omitted Invert declaration, shared headers and changed viewport callers were reviewed against the assembly, reference maps and disc DWARF; fix the three local issues and leave the honest partial bodies alone.
