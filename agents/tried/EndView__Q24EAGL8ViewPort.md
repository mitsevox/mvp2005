# ViewPort::EndView

2026-09-30, coordinating lane. Target 0x803E1E88, 0x54 bytes / 21 instructions.
Original whole viewport.cpp and unchanged library -O2 -G0 flags.

FIFA05 refnames:368 and UEFA:526 place EndView(void) in libeaglSNz.a(viewport.o).
GoldenEye:596 and MoH4:587 confirm mangled name and size. Disc DWARF names the
render-context pointer, active flag and stacked viewport link used by the body.

First candidate: clear the context's current viewport, mark this inactive,
resume a stacked viewport when its pointer exceeds the sentinel value 1,
then clear the stack link. Natural member operations, no invented helper.
Pointer-to-unsigned guard follows the target cmplwi 1 and carries a port note.
Combined objdiff: 21/21 instructions, 100%, first candidate. Full ninja ends
main.dol: OK. Viewport is 11/17 exact, 2816/5324 bytes; all prior ten remain exact.
Unit remains NonMatching and assembly-linked; data ownership is still open.
No MATCH/fake notes or altered flags. Calls match SetCurrentViewPort and BeginView.
