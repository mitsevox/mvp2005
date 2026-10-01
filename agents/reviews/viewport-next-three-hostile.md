# Viewport next three: hostile review

2026-09-30. Fresh reviewer with no conversation history. It received the complete current
viewport.cpp and its headers, name evidence, original assembly, referenced strings, split and
file-map entries, shared library flags, published refnames and full DWARF output for declared
types. It did not receive lane reports, tried-ledgers, the blind review or coordinator reasoning.
The prompt in docs/review-checklist.md was used verbatim, including items 17-19.

The reviewer independently compiled the whole unit with its DWARF-allowed anonymous COORD3,
COORD4 and MATRIX4 union forms at unchanged -O2 -G0. All five written functions scored 100.0%
instruction similarity. This is not a claim that the NonMatching unit links from C++.

## Round 1

1 PASS
2 PASS
3 PASS
4 PASS
4b PASS
5 PASS
6 PASS
7 PASS
8 FAIL src/eagl/viewport.h:17: RenderContextBase has no type-name evidence row -> record its T1 DWARF identity at 0x6C66 and the namespace evidence.
9 PASS
10 PASS
11 PASS
12 PASS
13 PASS
14 FAIL src/eagl/viewport.h:93: VPFrustum is described as the last SetPerspective inputs, but both orthographic setters overwrite it -> describe the current projection settings.
15 PASS
16 PASS
17 FAIL src/eagl/viewport.cpp:1: the top comment does not explain the open .text edge or account for functions through 0x803E1F98 -> cite the global initializer at 0x803E1F6C and the viewport_cmn.o boundary at 0x803E1F98.
18 PASS
19 PASS

MATCH notes: 0, fake match notes: 0, banned tricks: 0, inconsistencies: 0 unexplained

Verdict: FIX

SetPerspective reads like EA: explicit SDK projection setup and named frustum mathematics.
IsSphereInView reads like EA: ordinary plane-distance rejection with the recovered vector and transform types.
My independent compile of the DWARF-allowed type forms scored all five written functions at 100.0% instruction similarity; fix the evidence bookkeeping and stale comments.

## Round 2: same reviewer, only FAILs and changes

8 PASS
14 PASS
17 PASS

MATCH notes: 0, fake match notes: 0, banned tricks: 0, inconsistencies: 0 unexplained

Verdict: SHIP

The missing type evidence, stale projection comment and open-edge accounting are fixed.
The original DOL confirms the initializer registration, and both maps confirm the next object boundary.

Fixes: a dedicated RenderContextBase T1 row with map namespace corroboration; a current-
projection VPFrustum comment; an explicit ReBegin / registered initializer / viewport_cmn.o
account of the open .text edge. No function bodies, flags, type layouts or splits changed.
Claude's final review is a separate pending gate requested by the owner.
