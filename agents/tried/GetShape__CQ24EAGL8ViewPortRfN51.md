# ViewPort::GetShape, 0x803E1C10

2026-09-30, viewport-geometry lane. Whole `eagl/viewport.cpp`, unchanged `-O2 -G0`.

| Attempt | Result | Evidence |
| --- | --- | --- |
| Sequential scalar stores, provisional scratch pointer signature | 100.0%, 13 / 13 instructions | Six MVP DWARF VPGeometry fields; provisional signature was scratch only. |
| Natural const member, six float references from relayed map signature | 100.0%, 13 / 13 instructions, identical | Owner-relayed Claude FIFA/UEFA name/signature excerpt; raw map TSVs not directly read locally. |

The six sequential assignments preserve retail's alias behavior: each member is loaded immediately
before its output store, including when an output aliases a later member. No local geometry copy
or reordered store was introduced. All three written viewport functions remain instruction-exact.
The object remains NonMatching because unrecovered functions stay in assembly.

Root integration: the refnames published on main in f1e1763 were inspected directly:
fifa05.tsv:364, uefa.tsv:522, ge.tsv:593 and moh4.tsv:584 agree on the const six-reference
signature and 0x34-byte size. Combined whole-unit report keeps all five recovered functions
at 100.0%; viewport has 1,256 matched bytes and 5/17 exact functions. No existing exact
address was lost. `main.dol: OK` remains an assembly-linked build check.
