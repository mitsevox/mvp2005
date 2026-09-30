# ViewPortPrivate::EnactFogSettings

2026-09-30, ProDG 3.9.3, unchanged original-object `-O2 -G0` flags.
Map name at 0x803E1A38, size 0x11C: FIFA05:363, UEFA:521, GE:591, MoH4:582.

Types first: disc InstanceCrowd.o RenderContextExtensionBase .debug 0x6101, all
seven data members and eleven static members, plus compiler-managed vptr at 0x1C.
Its EAGL namespace is confirmed by original ELF static symbols. Five associated enums
are retained at 0x67EA (FilterModeOverride), 0x685D (AlphaWritesOverride), 0x68D5
(MipMapModeOverride), 0x6944 (AnisotropyOverride), 0x699E (FogTableMode). Enum namespace
placement beside the owning EAGL class is inferred rather than retained by DWARF.
Colour .debug 0x2C93 remains its genuine four-byte packed representation.

Virtual destructor identity independently established: map-proven extension-base
constructor 0x803D9B6C writes vptr 0x806867E8 at +0x1C. That table's function slot
0x806867F4 points to 0x803D9BAC, which reinstalls this vptr at +0x1C, tests the GCC
deleting-destructor flag r4&1 and calls the same deletion path 0x80377408. This is
T3 identity evidence, not an invented method for object layout; no body is recovered.

Attempt 1: natural null-guard, SDK GXColor populated by memcpy from EAGL Colour,
enabled-fog upload, optional SDK GXFogAdjTable and nonnegative viewport centre,
disabled-fog upload otherwise. memcpy is the ordinary representation copy needed
to pass EA's packed colour to GX; it optimises into the exact four-byte load/store
and avoids unrelated pointer casting. Trial 71/71 instructions, 100.0% identical.
The float-to-int centre conversion initially implicit raised ProDG's warning.

Attempt 2: explicit `(int)` for the semantic viewport-centre conversion, eliminating
the warning; trial remains 71/71 instructions, 100.0% identical. The `(GXFogType)`
cast converts compatible enum values to the SDK API enum; the `(unsigned short)`
width conversion matches the SDK u16 argument. No MATCH/fake note or forced helper.

Whole build `main.dol: OK`. With ReBegin included, report viewport 7/17 functions,
1636/5324 exact code bytes; all existing five plus ReBegin remain 100%. The unit is
still NonMatching and assembly-linked. Generated external calls have the same targets
as the original: GXSetFog twice, GXInitFogAdjTable once and GXSetFogRangeAdj twice.
