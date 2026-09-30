# ViewPort::ClearViewPort

2026-09-30. ProDG 3.9.3, original viewport.cpp `-O2 -G0`, no flag or split edits.
Map-proven signature `ClearViewPort(EAGL::ClearFlags)` at 0x803E1578, 0x2D8 bytes.
ClearFlags disc .debug 0x1A246 is CLEAR_CURRENT=1, CLEAR_Z=2, CLEAR_STENCIL=4.

Types first: genuine GeoPrimStateExtension (.debug 0x96C4), nested State (.debug
0x9723 with containing_type attribute), all known instance/static fields, and all
GCAttr, GCCompCnt, GCCompType, GCCullDir, GCZWrites, GCVertexFormat and GCVertexDataType
enumerators. Canonical declarations are in eagl/state.h, with common Colour and
VerbosityControl in eagl/base.h and context types in eagl/rendercontext.h. SDK Mtx44 is appropriate for
C_MTXOrtho/GXSetProjection; standard SDK GX position/colour inlines draw the quad.

Attempt 1: natural full-screen/cache conditional, packed GX colour via memcpy,
SDK setup, clear quad and projection restoration. 184 instructions vs 182, 81.4%.
Two initial arguments were corrected from actual asm: channel diffuse mode is
GX_DF_CLAMP=2, not GX_DF_NONE=0, and the copied colour is the newly updated cached
gScreenColour rather than reloading mBackgroundColour. The pointer equality order
is global-first; this-first reverses cmpw operands. An honest MATCH note records it.

Attempt 2: those source corrections, genuine EA vertex enum names instead of numeric
masks. 183 vs 182, 87.7%. Remaining real mismatch is imported GXVert.h's modern-GCC
union/pointer macro: it materialises FIFO as lis CC00 + ori 8000 and writes offset0,
where the retail uses lis CC01 with offset -8000. No raw FIFO offsets were added.

Types/provenance breakthrough: disc DWARF InstanceCrowd.o .debug 0x21E4F records
GXWGFifo as a volatile PPCWGPipe at absolute address CC008000. Imported types.h:27
also records the historical address attribute. ProDG retains this attribute.
Attempt 3: `extern volatile PPCWGPipe ... __attribute__((address(...)))` rejects with
"address attribute cannot be specified for external variables". No object produced.
Attempt 4: genuine absolute variable definition with the address attribute matches
all FIFO operations. 182/182; 99.5% only because target had an old query symbol name.
After target regeneration, 100% instructions. This SDK declaration has a __SN__
branch; CodeWarrior and modern GCC declarations remain their existing upstream forms.
This is a hardware variable declaration, not inline assembly or a fabricated helper.

Attempt 5: replace an exact but unwieldy literal spelling with binary expression
1.0f - 1.0f/8388608.0f, reproducing retail 0x3F7FFFFE. Still 182/182, 100% identical.
Expression spelling is reconstructed, not asserted as retained source text.

Whole build main.dol: OK. Report viewport 8/17, 2364/5324 exact bytes, including every
previously exact body in this worktree. Unit stays NonMatching and assembly-linked.
One MATCH note, no fake notes, no banned tricks. Remaining provenance reconciliation:
gpFirstViewPort at 8062C2B4 was reconciled by root/init lane against its scoped
original ELF name, first-null store and context reset in BeginView. gStateInitialized
at 80627A78 is independently confirmed by map-proven GeoPrimStateExtension::Use at
803DB5A0: it reads that flag first; if false, copies the complete 60-byte mState into
the current-state cache at 80627AA8, invalidates its cached values and stores true at
803DB668. ClearViewPort restores false after its special GX draw, invalidating that
same genuine state cache. The name is retained in DWARF; address confirmation is code.
The external query at 803D9E3C tests byte80627308 ==1; IsScreenClearEnabled is T3,
EAGL namespace is inference. SetAttributeFormat name/signature is genuine DWARF at
0xA64D; its body simply calls GXSetVtxAttrFmt. No callee body is recovered here.
