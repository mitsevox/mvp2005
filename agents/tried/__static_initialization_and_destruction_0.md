# Viewport static initialization (0x803E1B54) and thunk (0x803E1F6C)

2026-09-30, viewport-init lane. Unchanged library -O2 -G0, one viewport.cpp, NonMatching.

GoldenEye refnames row592, MoH4 row583, MoH3 row410 and NFSU row405 identify the compiler's
`__static_initialization_and_destruction_0`, size0xBC. The thunk is registered in the constructor
table at0x805A2CF8 and calls it with the compiler's normal (1,65535) arguments. Neither is
handwritten source: natural globals let GCC generate both bodies.

The initializer copies a64-byte identity matrix from0x8060E938 to0x806AA990 (the matrix addressed
by ViewPort::gpProjectionMatrix's data pointer at0x8062C284), stores packed sentinel0x12345678
at0x8062C2BC (ClearViewPort compares its background colour to this cache), and initializes a
12-byte VerbosityControl at0x8062C2C0 to(4,4,1). Colour's unsigned-long constructor is genuine
DWARF0x2FA7; VerbosityControl(int defaultBaseVerbosity) is genuine0x573D with parameter spelling
recorded0x57D4. Bodies are reconstructed. Namespace/spelling of backing and identity matrices
are guesses; their representation and values are observed.

| Attempt | Result |
| --- | --- |
| Projection matrix copied from external identity constant, gScreenColour(0x12345678), then ViewPort::sVerbosityControl(4), with genuine inline constructors | 47/47 instructions100%; generated thunk11/11 instructions100% |
| Group all EAGL definitions before EAGLInternal colour definition | 47instructions83%; static initialization order changed |
| Restore semantic initialization order projection, screen-colour cache, verbosity, using reopened namespaces | 47/47instructions100%; thunk100% |

The restored order follows the target's dynamic initialization sequence. No manual compiler
functions, casts, register hacks, padding, flag changes, or fake helpers. A constant identity
matrix external to this object is read, not duplicated into viewport's owned data.

## Data ownership still unresolved

Generated gProjectionMatrix is .bss64bytes, matching target0x806AA990..0x806AA9D0. The screen
colour and verbosity are generated in .bss; target locations are .data and target verbosity's
initial bytes are(0,0,0), and generated initial bytes are zero. The word4 is at0x8062C2B8;
an initial tuple dump was misread and this was corrected by an address-by-address dump.
Do not mark this object Matching
on instruction scores alone. Root is investigating whole data ownership/layout. The source
identity matrix resides at0x8060E938 outside viewport's .rodata0x8060C808..0x8060C8E4; its
ownership and original name are not established. No data splits changed in this lane.

Compiler thunk symbol suffix is its first external symbol's name; here it is
`_GLOBAL_.I.__Q212EAGLInternal15ViewPortPrivatePQ24EAGL8ViewPort`. Whole source function-order
integration must use the compiler's actual suffix and update the target symbol accordingly.

Latest full ninja stops at `strip_unused: .text still references removed symbol
_4EAGL.gProjectionMatrix`, because no owned viewport .bss/.data ranges have yet been added.
The latest reports therefore predate the static globals: do not cite them as integrated static
initializer proof. Trial compiles preserve the whole unsplit candidate and show the two exact
instruction sequences; root must complete data ownership before a fresh whole build/report.

## Follow-up data audit

- Direct constructor definitions and copy-initialization definitions both retain47/47 instructions
  and all three globals in `.bss` (`.lcomm` in source assembly).
- ProDG3.5,3.5b140,3.7,3.8.1,3.9.3 all retain47/47 and `.lcomm` emission. This is not a version issue
  in any available compiler. Diagnostic `-fno-common` and `-fdata-sections` do not change placement.
- `-fno-zero-initialized-in-bss` is rejected by cc1plus as an invalid option (GCC2.95).
- Adding an ordinary `const int DEFAULT_BASE_VERBOSITY=4` before the constructed objects leaves
  them `.lcomm`; removed from retained source because its exact class association is unresolved.
- No section attribute or linker override added: without EA evidence these would merely force
  placement and would not establish the original source form.

Strong boundary evidence, not yet source-layout proof:
`.bss`0x806AA990..0x806AAB10 consists of the six64-byte matrices named by the viewport's gp*
registration strings/data pointers. Previous neighbor's static initializer803E097C writes
VerbosityControl0x806AA984..0x806AA990. Next viewport_cmn.o initializer803E2140 writes a separate
VerbosityControl0x806AAB10..0x806AAB1C. The two neighbors bound the six-matrix group exactly.
`.data`0x8062C280..0x8062C2CC is six matrix pointers, float[7] projection values, first viewport
pointer, integer4, packed screen cache, and a12-byte verbosity object. Zero0x8062C2CC..C2D0 is
alignment to the next64-byte identity matrix0x8062C2D0..C310, addressed by pointerC310 that the
viewport_cmn.o constructor reads. The class association of the integer4 and verbosity object
needs more evidence: ViewPort and ViewPortExtension both declare default verbosity and control.

`ViewPortExtension::gpFirstViewPort` at0x8062C2B4 is much stronger: genuine scoped DWARF global
0xEF5A parent0xEE96 typeViewPort*, plus exact external symbol in object000; BeginView stores
incomingthis there only when null (803E0FC8..0FDC), ClearViewPort comparesincomingthis, and
reset803D9358..9360 writes zero. Its name and class are T1; target address inference is T3.

## Executed compiler diagnostics (owner request)

Invoked the actual ProDG3.9.3 pipeline with unchanged-O2-G0 plus diagnostic-only
`-dr -dc -dN -dS -dg -dR -fverbose-asm`. Output is in ignored
`scratch/startup-diagnostics.o`, `.s`, `.i.rtl`, `.i.combine`, `.i.regmove`, `.i.sched`, `.i.greg`,
and `.i.sched2`. The diagnostic object still gives47/47 identical initializer instructions.
Initial RTL already describes the correct matrix copy, packed cache store, and verbosity
construction; final scheduling is not the unresolved issue. The allocation choice appears
outside these RTL passes: final assembler unambiguously emits three `.lcomm` directives,
and NgcAs object symbol table puts all three in `.bss`.

The current ngcld script separately collects `.data { *(.data) }` and `.bss { *(.bss) }`.
It does not merge the constructed globals into `.data`; the original game's linker script
has not been recovered, so its exact allocation policy cannot be inferred from ours.
Local compiler help and binary strings show ordinary section/nocommon attributes and SN-specific
snda section support, but no cited EA source, DWARF attribute, or reference object proves viewport
used any section attribute. None was added merely to make the data land at the desired address.

Comparative genuine constructed global: the immediately neighboring viewport_cmn.o initializer
at803E2140 writes VerbosityControl at806AAB10 in `.bss`, whereas this initializer writes the
same12-byte shape at8062C2C0 in `.data`. This is not a uniform EAGL policy of moving every
constructed class to `.data`; the differing class/global declarations or original linking policy
remain the question. Their exact ViewPort versus ViewPortExtension scope is not yet proven.
No direct data names appear in the public refnames rows for these addresses.
