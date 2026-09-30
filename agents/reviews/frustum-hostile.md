# Frustum hostile review, 2026-09-30

Reviewer: full-disc-debug agent, first source review after the unnamed-instruction review.
No lane report or reasoning was supplied. Scope: both viewport source slices, shared viewport
and realmath headers, changed libc math declarations, naming evidence and original assembly.
The reviewer followed `docs/review-checklist.md`.

Round 1: items 1,2,3,4,4b,5,6,7,9,10,11,12,13,15,16 PASS. Verdict FIX.

- Item 8: missing grouped evidence rows for projection parameters/locals and Transform
  declaration parameters. Names were sensible; added meaning/evidence rows, retained T4
  constructor-signature uncertainty.
- Item 14: stale realmath comment said vector layouts/member names were unavailable. Full
  disc metadata proves COORD3 and COORD4 layouts and x/y/z/w; corrected comment and T1 rows.

Round 2: the same reviewer rechecked only its FAILs and changed evidence. Items 8 and 14 PASS.
Verdict SHIP. Source bodies unchanged between rounds.

Final counts: 2 MATCH notes, 0 fake-match notes, 0 banned tricks, 0 unexplained inconsistencies.
The reviewer found both functions natural engine code and accepted their explained notes.
Historical FIFA/UEFA catalogue claims are not freshly verified reference artifacts.

Round 3: exact recovery adds the disc-evidenced `DegToRad(float)` helper and changes the setup
call to `tanf(DegToRad(fov * 0.5f))`. The same reviewer checked the changed helper, call and
evidence only, without receiving lane diagnostic reasoning. Items 3,4b,5,8,14 PASS; SHIP.
Texture.o records 0x24C8 and 0x24E6 establish the float declaration and `deg` parameter.
The helper body and global placement remain T3 reconstruction; namespace is not claimed proven.
Counts remain two MATCH notes, zero fake matches, zero banned tricks, zero unexplained
inconsistencies. The inline helper is original EA vocabulary, not an invented expression wrapper.
