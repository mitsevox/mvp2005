# ViewPort::BeginView

Target 0x803E0F9C, 0x5DC / 375 instructions, viewport.o; unchanged -O2 -G0.
GE ge.tsv:587 and MoH4 moh4.tsv:578 supply the mangled method name; FIFA
fifa05.tsv:359 and UEFA uefa.tsv:517 place the method in libeaglSNz.a(viewport.o).
This is an honest partial candidate, not an exact result.

## Types and declarations established first

Canonical base.h/rendercontext.h/state.h were read from the sibling lane's
reviewed header proposal and installed through apply_patch, not copied through
shell writers. RenderContext additions are in rendercontext.h only.
All retained fields and statics of RenderContextExtension (0x60D6),
RenderContextPrivate (0x747E), and RenderContext (0x701E) were declared, including
their retained inheritance: records 0x6525 -> extension base, 0x74A7 -> private
base, 0x7040 -> context base. InstanceCrowd.o supplies those record offsets.
SDK GXRenderModeObj/GXFifoObj/OSMessageQueue come from existing imported headers.
RenderContextPrivate's message array has a nonconstant bound in DWARF; its element
is a pointer to void. It is declared static void* gMessages[].

RenderContextPrivate::GPBreakCallback (0x7F53) and GPBreak (0x7F80) carry
AT_member0x747E, proving they are nested. The callback's subroutine0x84F2 has
unsigned token parameter0x84FE; map SetGPBreakPoint (ge.tsv:505/fifa05.tsv:288)
proves void(unsigned int), and nested GPBreak methods (ge.tsv:507..509 /
fifa05.tsv:290..292) independently confirm the namespace/nesting.
RenderContextPrivate's namespace comes from its constructor and methods;
RenderContextExtension's namespace from constructor fifa05.tsv:299.

No complete disc definitions exist for TextureRenderContext,
TextureRenderContextExtension, or TextureRenderContextPrivate. The texture
context constructor at 0x803E09B4 calls the common base constructor with owned
extension at +0x10 and private at +0x3C. Extension constructor0x803E081C calls
the extension base constructor; private constructor0x803E08B8 calls the private
base constructor. Their names/signatures are map-proven. These classes are
marked in progress; extension's unknown derived names/types occupy the explicit
0x20..0x2B pad. The texture private class declares only its base and the mapped
GetPhysicalXOffset method; its full size and unaccessed derived members remain
unknown. No whole texture-object layout completeness is claimed.

AppendMatrix(const MATRIX4*) is map-proven at0x803DFE28 (GE572; FIFA346,
whose displayed demangle omits const). EndView and EnactFogSettings are also
map-proven. GetCurrentViewPort (0x803DA148) and SetCurrentViewPort (0x803DA154)
have no map/DWARF name found: descriptive names are T3, getter const T4.
Their bodies return the current pointer through the private reference, and
store its replacement, respectively. Existing Transform constructor signature
remains the canonical T4 const-reference guess.

The first-viewport static and model-view backing matrix addresses are inferred
from their uses and related static-pointer values; no data ownership boundary
was invented. The source references extern/static declarations only.

## Trials — 2026-09-30

1. Natural stack suspension, Transform construction/AppendMatrix, three union
   copies, typed screen/texture context branch, viewport jitter, scalar scissor
   clamps, projection and fog: 375 instructions, 94.7%. Initially zero offset
   was initialized after GetSize; ctor arguments had one independent swap,
   model-view copy register assignment differed. Static symbol spelling was
   corrected to GCC's actual _Q24EAGL17ViewPortExtension.gpFirstViewPort.
2. Initialize physicalXOffset=0 and screenContext=0 before the dimension query:
   375 instructions, 99.7%. All differences disappear except the ctor argument
   setup order. This keeps related viewport-query inputs together naturally.
3. Converting initialization `Transform viewProjection = mPrivate.mViewMatrix`:
   99.7%, same swap. Not retained.
4. Pointer instead of const-reference constructor (an evidence-ambiguous T4
   alternative): same 99.7 instruction shape; relocation name differs. Sphere
   body likewise unchanged except ctor relocation. No advantage, canonical
   signature restored immediately.
5. Meaningful local ViewPortPrivate reference used across the long body:
   375 instructions, 71.5%, private-relative loads and smaller frame. Restored.
6. Explicit temporary construction `Transform viewProjection = Transform(...)`:
   99.7%, same swap. Restored direct construction.
7. A const MATRIX4 reference shared by the constructor and the two global matrix
   copies: 376 instructions, 68.2%; changes allocation and shrinks the frame from
   176 to 160 bytes. This was a meaningful alias experiment, not a temporary
   introduced merely to constrain registers. Restored the direct member uses.
8. Diagnostic whole-unit -fno-strength-reduce, in addition to canonical -O2 -G0:
   object byte-identical to the canonical candidate. BeginView remains 375
   instructions / 99.733333% trial; SetShape, SetPerspective, IsSphereInView,
   GetShape, SetViewMatrix, SetOrthographic and SetOrthographicScreenSpace remain
   100%. No build configuration or retained library flags changed.
9. Diagnostic compilation against the root lane's current canonical full headers,
   selecting /Users/Lucas/Documents/mvp2005/src before this worktree's src include
   directory: object byte-identical. The shared declaration consolidation and
   additional prototypes do not change this scheduling result.
10. Expanded trial 8 to all fifteen written functions in the root lane's current
    whole viewport.cpp, using root include/prodg, include/libc, include and src
    directories. The canonical and no-strength-reduction objects are identical,
    SHA1 9c3b341bb2f50a193d4a02fa3f44af4f162e1c73. Fourteen functions remain
    100%: SetShape193, SetPerspective115, EndView21, EnactFogSettings71,
    ClearViewPort182, IsSphereInView79, ViewPortPrivate constructor43, GetShape13,
    SetViewMatrix38, ReBegin24, SetOrthographic53,
    SetOrthographicScreenSpace54, ViewPortExtension constructor2 and destructor10
    instructions. BeginView remains375 /99.733333%. Outputs are ignored under
    scratch/beginview-whole-root/{canonical,no-strength}.o.
    An initial mixed-header snapshot used this worktree's older GXVert.h and
    made ClearViewPort183/88.219178%; correcting all include roots restores182
    /100%. That mixed-header result is not a root source regression or a flag
    effect. All root files were read only throughout this experiment.

Best and retained: normal direct construction, 375 instructions / 99.7% trial;
whole-unit objdiff 99.46667%. The only difference is at +0xC0/+0xC4:
target computes stack address r3 then copies source matrix address into r4;
candidate copies r4 then computes r3. Both call the same constructor at +0xC8.
No forcing helper, statement permutation sweep, flag tuning or assembly used.

## Verification and limits

All remaining calls and code match: the three current-viewport queries,
EndView, setter, Transform ctor/AppendMatrix, physical offset query, VI field,
GX viewport/jitter/scissor/projection and fog. All internal destinations agree.
All referenced literals have identical values: zero, unsigned/signed integer
conversion biases and 2147483648 double. The matrix and first-pointer addresses
remain external references, not recovered data definitions.

Seven exact functions in this worktree remain100%; BeginView stays partial.
The game still links assembly for NonMatching viewport; main.dol OK is a
regression check, not source-linked verification of BeginView or owned data.
No invalid-dimension or stack behavior was repaired: pointer address1 is the
retail stack sentinel, explicitly documented as a port hazard.

Friction: initial new header trial needed mapped derived constructor declarations
because GCC rejects implicit default constructors for reference/Colour bases;
existing SDK names required GXManage.h and void* message element type. First
GXScissor include assumption was corrected to the existing GXCull.h declaration.
No replacement SDK declaration or substitute game type was invented.

## Executed compiler RTL diagnostics

Actual ProDG compilation was executed with all six documented dump flags:
`-dr -dc -dN -dS -dg -dR`. These request initial RTL, combine, register move,
first scheduling, global register allocation/reload and second scheduling.
The normal -O2 -G0 object and the diagnostic object are byte-identical, SHA1
783712708ce02cc566cd4b45d757a6b0e97ea65b. Thus observing these dumps did not
change the result being diagnosed.

Ignored raw files are under scratch/beginview-rtl/viewport.i.{rtl,combine,
regmove,sched,greg,sched2}; corresponding .o/.i/.s files are retained there.
The same six dumps were actually generated for trials 8 and 9 under
scratch/beginview-rtl-no-strength and scratch/beginview-rtl-canonical-headers.
Both objects have the same SHA1 as the canonical candidate.

Initial RTL (lines 608..635) emits UID116 for SetCurrentViewPort, UID120 for
the view-matrix address, UID122 for r3 = frame + 8, UID124 for r4 = matrix
address, then UID126 for the constructor. Combine and register-move preserve
122 before 124. The first scheduling dump's basic block 7 ready list at cycle7
contains `122 124`; its scheduling visualization issues UID124 followed by
UID122 on the two integer units in that same cycle. The scheduled RTL at
lines2188..2197 confirms this is where their emitted order first reverses.
Global allocation maps the matrix address to r30 and the frame to r1 without
changing that order; second scheduling also emits 124 then 122 in one cycle.

UID122 has an output dependency on prior r3 setup UID112 and an anti dependency
on the preceding setter call UID116. UID124 has an output dependency on prior
r4 setup UID114, an anti dependency on UID116 and a true dependency on the
matrix-address calculation UID120. There is no dependency between 122 and124.
The remaining discrepancy therefore is an ordering choice between independent
instructions issued in the same cycle, rather than a different matrix offset,
copy operation or constructor destination. These dumps establish the pass and
dependency graph; they do not establish why EA's original source/compiler
configuration selected the opposite ordering. No compiler-source priority
explanation or source-equivalence certainty is claimed.

The fully evidenced layout/type declarations and the diagnostic shared
strength-reduction flag do not alter it. Without additional source/signature
or original shared compiler-configuration evidence, retain the natural partial
candidate instead of manufacturing a dependency to constrain this pair.

## Processor model and retained signature audit

Executed the actual NGCCC driver with its required SN_NGC_PATH directory, no
arguments to obtain its usage, and -v -x c++ -S -O2 -G0 on the already processed
whole unit. The command it sends cc1plus is -version -O2 -G0 -quiet: it adds no
implicit -mcpu/-mtune preset. The usage documents the -m... machine-option route
but defers individual options to compiler documentation. cc1plus --help only
documents function alignment and explicitly notes additional undocumented
target options; its embedded preset table and successful acceptance establish
the presets tested here. -Q/-v are not supported by this cc1plus and were not
used for matching. -fverbose-asm reports the default enabled target switches
as -mpowerpc -mnew-mnemonics -meabi -mcall-eabi -msdata=eabi; it does not name
the internal processor enum. Therefore the internal default is not claimed as
proven from that option printout alone.

Both -mcpu and -mtune sweeps were actually compiled, using one fixed preprocessed
root whole unit. Every output function was compared against the named root
retail split object. Raw complete fifteen-function instruction counts and scores
are in scratch/beginview-{cpu,tune}/results.json, generated by the retained
scratch/beginview-cpu-diagnostics.py. Each preset's first/second scheduling dumps,
assembly, object and diagnostic log are saved separately. Processor choices are
diagnostic only: no build configuration or source changed.

| Preset family | -mcpu exact / BeginView trial % | -mtune exact / BeginView trial % |
| --- | --- | --- |
| default, 750, 740 | 14 / 99.733333 | 14 / 99.733333 |
| 601 | 3 / 45.839416 | 4 / 59.574468 |
| 602, 603, 603e | 4 / 92.942743 | 4 / 92.942743 |
| ec603e | 3 / 38.840580 | 4 / 92.942743 |
| 604, 604e, 620, powerpc | 6 / 79.840849 | 6 / 79.840849 |
| 401, 403 | 3 / 30.144928 | 4 / 49.066667 |
| 505 | 4 / 52.127660 | 4 / 52.127660 |
| 801, 821, 823, 860 | 3 / 30.724638 | 4 / 52.127660 |
| common | 4 / 58.974359 | 4 / 59.574468 |
| power, power2, rios, rios1 | assembler rejects POWER mnemonics | 4 / 63.115789 |
| rios2 | assembler rejects POWER mnemonics | 6 / 71.542553 |
| rsc, rsc1 | assembler rejects POWER mnemonics | 4 / 59.574468 |

The 750/740 whole objects are byte-identical to default, SHA1
9c3b341bb2f50a193d4a02fa3f44af4f162e1c73. Their two scheduling dumps likewise
remain identical to the default. This directly tests the plausible GameCube
processor family and establishes default equivalence for this unit; switching
to that family does not repair the independent constructor setup ordering.
Every other successful preset regresses previous exact functions. Failed
-mcpu POWER-family cases emit obsolete mnemonics such as l, lm, cal and br,
which NgcAs rejects; their objects/scores are not fabricated. All -mtune presets
are accepted and assembled because tuning preserves the target instruction set.

Independently audited every global_subroutine with AT_member referring to each
Transform aggregate across all retained libmatd debug units, including records
attached outside the aggregate's child range. All25 complete definitions retain
the same allocator-only declarations: __nw8, __dl2, __vn6 and __vd2. None retains
a Transform constructor or relevant ordinary method signature. InstanceCrowd.o
Transform is .debug0xE12D; its first allocator is0xE1B7. Full audit rows are in
scratch/beginview-rtl/transform-method-audit.json. Thus no new const-reference,
nonconst-reference or pointer constructor alternative has become evidenced;
the canonical constructor remains honestly T4. No signature was changed merely
to affect code generation.
