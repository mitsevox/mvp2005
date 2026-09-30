# ViewPort::SetOrthographic

Target: 0x803E1CDC, 0xD4 bytes (53 instructions), in the existing whole
`libeaglSNz.a(viewport.o)` unit. Compiler: ProDG 3.9.3, library `-O2 -G0` unchanged.

## Evidence and types

The owner relayed Claude's reference-map excerpt: FIFA 2005 and UEFA CL 04-05 name this
address and size `EAGL::ViewPort::SetOrthographic(float,float,float)` in viewport.o.
The raw map TSVs at `/mnt/project-files/mvp2005/refnames/*.tsv` were not accessible to this
local lane and were not independently inspected. ProDG confirms the mangling
`SetOrthographic__Q24EAGL8ViewPortfff`. MVP's disc DWARF confirms every member touched here
(`dwarf_lookup.py` against the private full export): ViewPort, ViewPortPrivate, VPFrustum,
MATRIX4 and ProjectionType agree with the shared header; no type modifications needed.

Target assembly calls SDK `C_MTXOrtho`, whose prototype and implementation take top, bottom,
left, right, near, far: this body passes aspect, -aspect, -1, +1, nearPlane, farPlane. It saves
zero FOV and the remaining three settings in mFrustum, copies the GX projection transposed
to EA's row-vector matrix, selects ORTHOGRAPHIC and uploads the GX projection.

## Attempts (2026-09-30)

1. Scratch provisional free function under the unknown target label (not tracked source),
   natural projection copy with row-2 diagonal and w before x/y: 53 instructions,
   trial.py 98.1%. Only the relative position of one zero store differed.
2. Same body, row-2 x/y/diagonal/w in increasing column order, consistent with the existing
   SetPerspective copy: trial.py 100.0%, 53/53 normalized instructions identical.
3. Actual named member declaration in existing viewport.h and body in existing viewport.cpp,
   same increasing-column copy: 53/53 normalized instructions identical, independently
   compiled by scratch/ortho/check_member.py using the whole unit's ninja compile command.
   Both original exact functions also remained instruction-identical in that same raw object.

The successful form uses no MATCH notes, fake matches, casts, wrappers, or configuration
changes. The earlier scratch free function was solely a provisional symbol for trial.py;
it is not present in tracked source. The consistent ascending matrix column order is the
natural final form, rather than a specially rearranged sequence.

## Verification limits

Raw target literal relocations resolve to 0x8060C874 = +0 (00000000),
0x8060C878 = -1 (BF800000), 0x8060C87C = +1 (3F800000); candidate literal pool uses exactly
the same bytes. C_MTXOrtho and GXSetProjection call relocations agree. Normalized instruction
equality does not prove fully relocated linked C bytes. No splits or symbols were edited by
this lane; root must apply the verified name in symbols.txt for objdiff to score the function.

`ninja`: main.dol OK, still using original assembly because the unit remains NonMatching.
`ninja build/GV4E69/report.json`: original SetPerspective and IsSphereInView preserved; whole
build retains 1,127 exact functions / 253,740 matched code bytes. This report cannot score the
new named member until the root applies the symbol rename. No commit yet, pending integration.

Friction: trial.py requires one identical symbol in target and candidate. Before symbol rename,
the actual member comparison used its existing normalization functions in the ignored scratch
script, without touching configuration. A guessed scratch glob failed with zsh no-matches;
no file was read or changed by that failed search.

Root integration: main f1e1763 published the refnames, and root read fifa05.tsv:366 and
uefa.tsv:524 directly. Both name this non-const three-float method in viewport.o, size 0xD4.
After the root symbol rename and integration in retail address order, the combined whole-unit
report scores all five recovered functions 100.0%: 1,256 matched bytes, 5/17 functions.
No existing exact address was lost. No source slice, flags or link-mode changes were needed;
`main.dol: OK` remains the assembly-linked check, not proof of source-linked viewport data.
