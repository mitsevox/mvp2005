# ViewPort::SetOrthographicScreenSpace (0x803E1DB0)

2026-09-30, viewport-screen lane, whole viewport.cpp, shared `-O2 -G0`.
The target is 216 bytes / 54 instructions. No flags, split ranges or link mode changed.

## Types and name evidence

Disc `libmatd.a` DWARF, queried with `dwarf_lookup.py --dir` against the private full export:
VPGeometry (InstanceCrowd.o .debug 0xF463), ViewPortPrivate (0xEFCF), ViewPort (0xE87F),
VPFrustum (0xF580), MATRIX4 (0xE4A3), ProjectionType (0xF419).
The existing canonical header declares their known members; no layout additions were needed.

The owner relayed Claude's reference-map excerpt: FIFA 2005 / UEFA CL 04-05
libeaglSNz.a(viewport.o), `SetOrthographicScreenSpace__Q24EAGL8ViewPortff`, 0x803E1DB0,
size 0xD8, matching GoldenEye and MoH4 name/size. The lane did not inspect the raw map TSVs;
their project-share location was not locally accessible. Non-const member with two float
arguments is map-supported; `nearPlane` and `farPlane` are T3 from stores into the corresponding
VPFrustum fields and the C_MTXOrtho near/far arguments. Void return is T3 from no produced return
value after GXSetProjection (return types are absent from this mangling).

## Measured attempts

1. Scratch provisional C function, using a local `ViewPortPrivate& state` to shorten the accesses:
   55 versus 54 instructions, 53.2% alike. GCC materialised the reference base at this+12,
   changed member displacements/registers, and emitted one additional instruction.
2. Natural direct member access, consistent with SetPerspective: 54 instructions, 100.0%
   normalized instruction match. No casts, fake helpers or forced statement ordering.
3. Actual map-named ViewPort member in the existing whole viewport.cpp: 54 instructions,
   100.0% normalized instruction match; objdiff reports 100.0%. Existing SetPerspective and
   IsSphereInView both remain 100.0%. Viewport matched code rises 776 -> 992 bytes, functions
   2 -> 3. Whole-build matched code rises 253740 -> 253956, functions 1127 -> 1128.

`ninja` ends with `main.dol: OK`. Viewport remains NonMatching, so this verifies the assembly-
linked build; it does not establish source-linked viewport bytes or complete data ownership.
No MATCH or fake match notes introduced. Literal relocation values checked against target:
0.0f (0x00000000), 0.75f (0x3F400000), 1.0f (0x3F800000).

## Behavior

Orthographic bounds are top=0, bottom=viewport height, left=0, right=viewport width: x right,
y down. It stores FOV=0 and aspect=0.75, and the supplied near/far distances, transposes the
projection's affine entries into EA's row-vector matrix, selects ORTHOGRAPHIC and uploads GX.
It does not refresh perspective side-plane cull data.

## Friction

The `python` executable is absent on this host; `python3` works. Initial ninja refreshed the
shared dtk tooling due its generated prerequisite state; no source or build configuration fix
was required. A failed read guessed the SDK matrix header path; the actual C_MTXOrtho definition
was found in src/dolphin/mtx/mtx44.c. No processes remain running.

Root integration: main f1e1763 published the refnames, and root read fifa05.tsv:367,
uefa.tsv:525, ge.tsv:595 and moh4.tsv:586 directly. The names, non-const two-float signature
and 0xD8-byte size agree. All five recovered functions remain 100.0% in the combined unit,
which has 1,256 matched bytes and 5/17 exact functions; no existing exact address was lost.
The whole build has 254,220 matched bytes and 1,130 exact functions (+480 bytes / +3).
