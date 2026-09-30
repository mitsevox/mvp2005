# ViewPortExtension constructor/destructor

2026-09-30, viewport-init lane, original viewport.cpp at unchanged -O2 -G0.

Constructor0x803E1EDC(8bytes) and destructor0x803E1EE4(40bytes) are absent from refnames. Types
are genuine DWARF: ViewPortExtension0xEE96 size4, mpBaseObject0xEEF1 offset0 ViewPort*.
ViewPort's map-confirmed constructor in viewport_cmn.o at803E1F98 calls the tiny constructor at
803E1FB4 with the ViewPort address as both destination and owner, then constructs private state
at offset0xC. The outer destructor803E2188 calls the extension destructor at803E21A4 withr4=2.

One natural constructor body, `: mpBaseObject(baseObject) {}`, gives2/2 identical instructions.
One natural empty destructor body, `{}`, gives10 instructions; trial initially90% because target
callee was fn_80377408 while GCC emits `__builtin_delete`. Naming that wrapper from the compiler
ABI and its call-site role yields10/10 identical instructions. No class allocator declaration
or fake inline wrapper was required. These ctor/dtor names and the delete wrapper are T3 inferred
from layout and ABI, not map-confirmed names.

80377408 is a32-byte wrapper to803772E0, adjacent to GCC allocation helpers including already
identified __builtin_vec_new80377458. Destructor'sr4&1 test is compiler-generated deleting-
destructor ABI; no source parameter or manual bit test is reconstructed. The extension owns
only its owner pointer and has no destructor resource work. No MATCH/fake notes or forced shapes.

Whole build still awaits owned data integration (static initializer ledger); root must rerun
the final object/report and hostile review after integration.
