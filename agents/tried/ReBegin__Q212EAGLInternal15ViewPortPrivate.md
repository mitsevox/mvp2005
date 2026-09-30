# ViewPortPrivate::ReBegin

2026-09-30, ProDG 3.9.3, original `eagl/viewport.cpp` flags `-O2 -G0`.
Map name: FIFA05:369, UEFA:527, GoldenEye:597, MoH4:588; address 0x803E1F0C,
size 0x60. Only this function was recovered; BeginView remains assembly.

Types first: disc DWARF InstanceCrowd.o RenderContextBase 0x6C66, DerivedContextType
0x6E07, RenderContextPrivateBase 0x6E67. All known members and statics declared.
The base's virtual destructor name is map-proven at 0x803D9180; the private base's
virtual destructor identity is T3 from the deleting-destructor ABI: derived constructor
0x803D9A24 writes its vptr at +0x10; derived destructor 0x803D9AD0 restores base vtable
0x806867D0, whose function slot 0x806867DC points to 0x803D99F0. That function installs
the base vptr at +0x10, tests r4's deletion flag and calls the operator-delete path
0x80377408. Namespace placement in EAGLInternal remains a separate T4 inference.

Attempt 1: natural ViewPort local from mpBaseObject, external current-viewport setter,
clear active flag, restore stacked view when pointer value exceeds sentinel 1, clear
stack, begin base view. `tools/match/trial.py`: 24/24 instructions, 100.0% alike.
No alternate shaping or flag trials were needed; zero MATCH/fake-match notes.

The pointer-to-unsigned-int conversion is the original 32-bit sentinel guard, with a
port note. It does not reinterpret the object as a different type. The original
instruction is `cmplwi r3,1`; values 0 and 1 both bypass BeginView.

Relocation inspection: generated and target both call the external setter at
0x803DA154 once and map-proven BeginView at 0x803E0F9C twice. The setter stores its
second argument at RenderContextPrivateBase::mpCurrentViewPort (+8), then returns;
its reconstructed name is T3 and no setter body was added to viewport.cpp.

Whole build `main.dol: OK`; report adds 96 exact bytes and one function, preserving
the existing five viewport matches. The unit stays NonMatching and assembly-linked.
