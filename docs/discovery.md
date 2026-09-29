# Discovery checklist (before any matching)

Everything here is measured against the binary. A guess is labelled as a guess. tw2004's first guess
at its compiler was wrong, and one test pointed at a compiler built two years after the game shipped:
an impossible result is a red flag, not a finding.

1. **Target.** `GV4E69` (USA), `main.dol` SHA-1 `da6becdbea614d03c4b5eae9f8a0fb08e0a184dd`
   (6,837,728 bytes). Still to check: the disc revision, any `.rel` modules.
2. **First dtk analysis.** `python configure.py && ninja`: function count, sections; the rebuild
   must be byte-identical before anything else happens.
3. **Compiler and language.** CodeWarrior (which GC/x version) or SN ProDG (GCC 2.95)? C or C++
   (mangled names in strings, vtables, `__ct`/`__dt`, exception tables)? A mixed binary (tw2004 had a
   ProDG block inside CodeWarrior code)? Method: compile small known functions (SDK, MSL) on each
   candidate and compare; prologue style; build dates vs. the ship date. Write it up in
   `docs/compiler.md`. This decides which of tw2004's matching rulebook ports.
4. **SDK and runtime.** Dolphin SDK build date (version strings), MSL, MetroTRK, MusyX or other
   middleware. Match them from public decomps first; they are not part of the naming pass.
   Done 2026-09-29: `docs/sdk.md`.
5. **Leaked names.** Assert strings and source paths (`.c`/`.cpp` names), error strings, RTTI or
   mangled names. Each one is T1 evidence and a unit boundary.
   Done 2026-09-29: `docs/names.md`.
6. **Reference builds.** Look for symbol-bearing related builds: MVP 2003/2004/2005 on other
   platforms, EA Canada GameCube titles of the same years with DWARF, maps or STABS, and public
   decomps of EA games (e.g. NFS Most Wanted GC, EA Canada, 2005). Ask the owner before any download.
   Record what each one gives (names, types, file order) in `docs/reference-builds/`.
   Surveyed and measured 2026-09-29 (`docs/reference-builds/README.md`, `tools/research/refmatch.py`).
7. **The file map.** Unit boundaries from 5 and 6, plus data ownership and alignment gaps. Every
   function belongs to a named unit (EA's name, or "(our name)") before bulk matching starts.
8. **Pilot pick.** The first section per `agents/pass.md` "Loop 4".
