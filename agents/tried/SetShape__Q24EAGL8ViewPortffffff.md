# ViewPort::SetShape

Target 0x803E0ACC, 0x304 bytes / 193 instructions; viewport.o. Work at unchanged
library -O2 -G0 flags, in the original whole viewport.cpp, 2026-09-30.

## Evidence before matching

GE map ge.tsv:585 and moh4.tsv:576 give the exact six-float mangled signature;
fifa05.tsv:357 and uefa.tsv:515 place it in libeaglSNz.a(viewport.o).
The disc DWARF supplies ViewPortPrivate geometry, clip dimensions, full-screen
bool, cull scales, frustum and render-context pointer, all already canonical.
New COORD2 is the disc's unnamed 8-byte x/y struct (InstanceCrowd.o .debug
0x1184, typedef 0x219B7, members 0x1196 and 0x11BA); ordinary 2D corner coordinates
account for the four stack-backed floating-point locals the target uses.

RenderContextBase is 0x10 bytes: EXTENSION_OBJ reference at 0x0 (0x6C8C),
const DerivedContextType at 0x4 (0x6CF6), mPrivate reference at 0x8 (0x6D29),
and implicit vptr at 0xC (0x6D94), static sVerbosityControl (0x6CC1) and
DEFAULT_BASE_VERBOSITY (0x6D59). The referenced types remain incomplete because
this function does not read their layout. Enum .debug 0x6E07 gives values
RCT_RENDERCONTEXT=0 and RCT_TEXTURERENDERCONTEXT=1.
Namespaces of the enum/private type are not retained and are explicitly guesses.

The retail base vtable 0x80686770 consists of three pure-virtual entries then
the map-proven destructor 0x803D9180. Derived table 0x80686740 supplies
BeginFrame 0x803D92D4, EndFrame 0x803D8640, GetSize 0x803D9810, and destructor
0x803D8234. The first two and destructor are map-proven; the TextureRenderContext
GetSize signature is map-proven at 0x803E074C and occupies the corresponding
slot. The target calls the third virtual slot (adjustor at 0x18, function at
0x1C). This evidence requires declaration order BeginFrame, EndFrame, GetSize,
destructor, not dummy virtuals or a raw vtable.

Out-of-line accessor 0x803E2200 loads ViewPort+0x10 and returns. That is the
DWARF's mPrivate.mProjectionType. No reference map or disc debug record names
the accessor: GetProjectionType is T3; its const qualification is T4 inferred
from read-only behavior and EAGL accessor convention, not recovered spelling.

## Trials, in order

1. Six geometry stores, float-to-unsigned clip dimensions, four scalar corner
   locals, scalar target dimensions, explicit clamps, direct bool expression,
   scalar half sizes/centre, right/bottom/left/top cull stores: 169 instructions,
   35.4% alike. Eight callee-saved floats instead of four, corners in registers,
   wrong first virtual declaration order (destructor/GetSize). No candidate
   containing that incorrect declaration was retained.
2. Correct retail virtual declaration order; two genuine COORD2 corner locals
   initialized with aggregate initializers: 199 instructions, 75.0%. Compiler
   adds six zero-initialization instructions, plus bool-expression difference.
3. COORD2 corner members assigned in the body; explicit full-screen if/else:
   193 instructions, 92.2%. Only culling arithmetic schedule/register allocation
   differs; no extra instructions or wrong behavior.
4. COORD2 halfSize and centre instead of scalars: 206 instructions, 53.1%.
   Extra stack space, stores and reloads. Not retained.
5. Restore scalar half sizes/centre; cull scales in ordinary member order
   left/right/top/bottom: 193/193, 100.0%, instructions identical.
6. Add explicit unsigned-int conversion casts to dimension assignments instead
   of implicit conversions (avoids SN warnings, same real value types): still
   193/193, 100.0%, instructions identical.

The retained body uses genuine COORD2 corners, natural comparison clamps,
normal full-screen if/else, readable scalar geometry calculations, no fake
helper, no assembly, no register tricks, no raw offsets, no statement order
matching the scheduled assembly, and no altered compile flags.

## Verification and limits

Target and candidate have the same two external code relocations: accessor at
function+0x2BC and SetPerspective at +0x2DC. The GetSize virtual sequence uses
the proven 0x18/0x1C vtable entry. Target literals are double 2147483648 at
0x8060C808, float zero at 0x8060C810, one at 0x8060C814 and half at 0x8060C818;
candidate literals have the same values. Internal SN branch relocations resolve
to the target's relative destinations.

Whole-unit report: SetShape 100%, previous six functions still 100%; 7/17,
2180/5324 matched bytes. +772/+1 against the SetViewMatrix worktree baseline.
Ninja main.dol OK. Viewport remains NonMatching and assembly-linked, so this is
not proof of source-linked viewport data ownership. No data ranges changed.

Parameter/local spellings are descriptive T4 guesses; the behavioral claims
are read from explicit geometry stores, bounds clamps, scale formulas and
perspective-refresh call. No width/height validity guards were added.
