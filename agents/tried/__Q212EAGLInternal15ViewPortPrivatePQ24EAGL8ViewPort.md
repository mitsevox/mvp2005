# ViewPortPrivate constructor (0x803E198C)

2026-09-30, viewport-init lane, baseline 785eafe. One original `eagl/viewport.cpp`, unchanged
library `-O2 -G0`, unit stays NonMatching and assembly-linked. Target: 0xAC bytes, 43 instructions.

## Evidence

FIFA 2005 refnames row 362 and UEFA row 520 name
`EAGLInternal::ViewPortPrivate::ViewPortPrivate(EAGL::ViewPort *)` in
`libeaglSNz.a(viewport.o)`. GoldenEye row 590 and MoH4 row 581 agree on the 0xAC size and mangled
`__Q212EAGLInternal15ViewPortPrivatePQ24EAGL8ViewPort`.
Disc libmatd.a(InstanceCrowd.o) DWARF: ViewPortPrivate at 0xEFCF, size 0x1A0, all members match
the existing complete header (`dwarf_lookup.py ViewPortPrivate --dir <full export>`).
Colour is the named struct at 0x2C93, c is unsigned int at offset 0 (0x2CAE).
Its genuine default constructor is recorded at 0x2F7C; Colour(unsigned long), assignment from
unsigned long, and conversion to unsigned int follow it. Its unsigned-long constructor at
0x2FA7 supplies mBackgroundColour(0), and the static cached gScreenColour(0x12345678). The body
stores its packed argument to c; DWARF retains the declaration, not the body.

## Attempts

All scores are `tools/match/trial.py` instruction similarity against the whole unit's target
object, with 43 generated instructions each. No flags or types changed to chase a match.

| Form | Score | Result |
| --- | --- | --- |
| Body assignments, linkage pointers first, then scalar state, geometry/frustum and explicit GX identity | 90.7% | Early scalar stores reordered |
| Scalar member initializer list, explicit background c=0 in body | 93.0% | Early scalar stores reordered |
| Body assignments with base pointer before next pointer and projection | 90.7% | Same early store differences |
| Initializer list for next/base pointers, other assignments in body | 90.7% | Same differences |
| Initializer list for base pointer alone | 90.7% | Same differences |
| Initializer list for next pointer alone | 90.7% | Same differences |
| Body next pointer reset after geometry/frustum | 93.0% | First four stores differ |
| Body next pointer reset after GX identity | 81.4% | Integer allocation and next-store location differ |
| Scalar initializer list except base pointer (body assignment) | 93.0% | Same as full scalar list |
| Scalar assignments before geometry/frustum, linkage/projection after | 93.0% | First four stores differ |
| Body fields in declaration-offset order | 79.1% | Integer allocation and flag stores differ |
| Genuine Colour default ctor declaration, assumed body `Colour() : c(0) {}`, scalar initializer list | 100.0% | Superseded: default body was not proven by this caller |
| Assumed sentinel Colour default body, explicit c=0 body assignment | 93.0% | Early scalar stores reordered; assumption dropped |
| Genuine Colour(unsigned long) ctor, explicit mBackgroundColour(0) member initializer | **100.0%** | **43/43 instructions identical; final form** |

The last form explains the target naturally: initializing the member Colour invokes its genuine
unsigned-long constructor, rather than replacing its initialization with an explicit later assignment.
No MATCH/fake-match notes, new wrappers, casts, raw offsets, or statement-order tricks retained.
The Colour helper is evidenced by the disc; it was not invented for codegen.

## Verification

Full local `ninja`: `build/GV4E69/main.dol: OK`. Unit remains NonMatching, so this proves the normal
build stays unchanged; the object comparison proves this recovered body. Objdiff report:
6/17 exact viewport functions, 1,428/5,324 code bytes, +172/+1 from baseline. SetPerspective,
IsSphereInView, GetShape, SetOrthographic, and SetOrthographicScreenSpace remain 100.0%.
Instructions and target relocations were inspected: constants are -1, +1, +0 (disc
0x8060C860/64/68), and there are no calls or other new relocations. Constructor returns this
in r3 under the compiler's constructor ABI, without a source return statement.

Unknowns: the complete original constructor text and Colour constructor body are not retained;
their bodies are reconstructed. It deliberately leaves mFullScreen, the realmath matrices,
clip state, and culling state untouched, just as target stores show.
Friction: initial local ninja downloaded dtk despite shared tool setup; normal warnings during
split/build, no matching failures. A raw JSON query initially used the wrong kind `debug_record`;
correct export record kind is `debug`. Initial interpretation of fundamental12 as float was
wrong: it is unsigned long (DWARF1 0xC). Corrected before final integration; default zero body
replaced by evidenced unsigned-long constructor and explicit packed-zero initializer.
