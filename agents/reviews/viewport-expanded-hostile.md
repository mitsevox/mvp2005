1 PASS
2 PASS
3 PASS
4 PASS
4b PASS
5 PASS
6 PASS
7 PASS
8 FAIL config/GV4E69/name_sources.tsv:183: the evidence ledger assigns a global-initializer name to 0x803E198C, which the maps and original instructions identify as the currently written ViewPortPrivate constructor; the actual initializer is 0x803E1F6C. Rows 137, 151 and 152 also still claim the render-context types are only forward-declared/incomplete, and row 152 describes EAGL placement while the declaration and later namespace row use EAGLInternal -> remove or correct the conflicting historical rows so each reviewed name has accurate current evidence; keep startup ownership explicitly unresolved.
9 PASS
10 PASS
11 PASS
12 PASS
13 PASS
14 FAIL src/eagl/viewport.cpp:128: the sphere-test comment is attached to BeginView and stops mid-sentence; its final fragment is stranded at line 253. src/eagl/viewport.h:6 also says the declared methods use names given by reference maps although Transform's constructor and GetProjectionType are explicitly reconstructed below -> put the complete sphere-test intent immediately above IsSphereInView, retain BeginView's own intent, and say the header includes both recovered and explicitly reconstructed method names.
15 PASS
16 PASS
17 FAIL docs/compiler.md:122: the current unit description still says twelve functions remain unrecovered, despite fourteen complete source functions plus BeginView now being present; the text extent and boundary evidence themselves are sound -> update the current partial-unit statement to distinguish the written functions from the two omitted startup functions and unresolved data ownership, and identify BeginView as not yet exact.
18 PASS
19 PASS
MATCH notes: 1, fake match notes: 0, banned tricks: 0, inconsistencies: 0 unexplained
FIX
ClearViewPort looks like EA code: the SDK calls and literal clear quad are ordinary platform work, and its one operand-order deviation is explained. BeginView also looks like EA code: the stack sentinel and discriminator-guarded downcasts agree with the original instructions, rather than disguising unrelated memory as a convenient struct. The known data and static members are complete, Colour's constructor signature is retained, and the FIFO is a genuine ProDG absolute declaration; fix the misleading comments and evidence ledger before calling this ready.

---

Round 2: rechecked only the prior FAILs and changed comments/evidence. Item 8: the incorrectly addressed startup-thunk row is absent, and rows 137/151/152 accurately describe the full declarations and separately guessed namespace. Item 14: the complete sphere comment now immediately precedes IsSphereInView, BeginView retains its own intent, and viewport.h distinguishes recovered from reconstructed names. Item 17: compiler.md now identifies fourteen exact functions, partial BeginView, two omitted startup functions and unresolved constructed-global/data ownership; viewport.cpp's revised ownership comment agrees. No source bodies, types or flags changed in these fixes.

1 PASS
2 PASS
3 PASS
4 PASS
4b PASS
5 PASS
6 PASS
7 PASS
8 PASS
9 PASS
10 PASS
11 PASS
12 PASS
13 PASS
14 PASS
15 PASS
16 PASS
17 PASS
18 PASS
19 PASS
MATCH notes: 1, fake match notes: 0, banned tricks: 0, inconsistencies: 0 unexplained
SHIP
The three local failures are fixed, and the unit now tells the truth about its evidence and partial scope. ClearViewPort and BeginView retain ordinary EA platform code with documented departures and real shared types. This ships as the reviewed partial unit; the omitted startup ownership remains unresolved.
