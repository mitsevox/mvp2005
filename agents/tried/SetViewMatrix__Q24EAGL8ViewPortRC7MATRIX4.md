# ViewPort::SetViewMatrix

Target: 0x803E1C44, 0x98 bytes (38 instructions), viewport.o.

## Evidence and natural form — 2026-09-30

The GoldenEye map (`config/GV4E69/refnames/ge.tsv:594`), MoH3 (`moh3.tsv:411`)
and MoH4 (`moh4.tsv:585`) give `SetViewMatrix__Q24EAGL8ViewPortRC7MATRIX4` at
the target address and size, including the const-reference signature. FIFA 2005
(`fifa05.tsv:365`) and UEFA (`uefa.tsv:523`) put it in libeaglSNz.a(viewport.o),
but their displayed demangled signatures omit const; the mangled maps settle it.

The disc DWARF lookup confirms MATRIX4 is a 0x40-byte union with m and m44 views
(InstanceCrowd.o .debug 0xE4A3). ViewPortPrivate's mViewMatrix is at 0x4C
(.debug 0xF0FB), mAmActive at 0x18C (0xF305), and ViewPort's mPrivate at 0xC
(0xEADC). The target copies 64 bytes to ViewPort+0x58 and tests the four-byte
bool at +0x198 before calling ReBegin with ViewPort+0xC.

First and only candidate: ordinary union assignment
`mPrivate.mViewMatrix = matrix;` followed by
`if (mPrivate.mAmActive) mPrivate.ReBegin();`.

`tools/match/trial.py src/eagl/viewport.cpp
SetViewMatrix__Q24EAGL8ViewPortRC7MATRIX4`: 38/38 instructions identical,
100.0%, under the existing -O2 -G0 viewport flags. No new flags, stand-in
types, manual copy loop, helper, casts, MATCH notes or fake matches.

Relocation check: both target and candidate call
`ReBegin__Q212EAGLInternal15ViewPortPrivate` with R_PPC_REL24 at function+0x84.
The SN candidate additionally carries R_PPC_REL14 .text relocations on its
internal branches at +0x50 and +0x7C; they resolve to function+0x14 and +0x88,
the target's loop and return targets. No data relocation is used.

Whole-unit report: SetViewMatrix 100%; the previous five exact functions remain
100%; viewport 6/17 functions, 1408/5324 bytes, +152/+1 from baseline.
`ninja`: main.dol OK. Viewport remains NonMatching and assembly-linked: this is
not a source-linked whole-viewport validation. Data ownership remains open.

Naming uncertainty: the parameter's spelling `matrix` is a T4 descriptive guess;
the function name and const-reference type are map-proven T2. The mViewMatrix
and mAmActive fields already have T1 DWARF evidence rows.
