# Quaternion/matrix retry, 2026-09-30

Scope: BuildQuatTrans (0x803DE414,264B) and ExtractQuatTrans (0x803DE51C,692B).
Base is reviewed be5011e; no tracked file or older worktree was edited.
All variants contain the whole original transform unit in the existing definition order;
compile flags are unchanged shared EAGL `-O2 -G0 -finline-functions`.

## Evidence checked before trials

- Read current CLAUDE/state/pass/brief/fidelity/checklist and both tried-ledgers.
- Read the previous independent quaternion findings and source-order comparison.
  Did not repeat O2/O3/inlining/store-permutation experiments already exhausted there.
- GE/MoH3/MoH4 give BuildQuatTrans's exact COORD4 pointer signature;
  NFSU/MoH3 give ExtractQuatTrans's exact output COORD4 pointer signature.
- All25 libmatd.a DWARF objects agree: MATRIX3 is a36-byte plain union with m[9]
  and m33[3][3]; Transform contains MATRIX4 m at0; Quaternion is a distinct16-byte
  named struct, but these mapped functions expressly use COORD4, not that type.
- Scanned symbol and subroutine names in all67 local raw disc export objects:
  1,077 distinct names, none naming a quaternion/MATRIX3 conversion helper.
  The raw exports retain some unrelated inline functions, so this is more than a
  type-only lookup. It cannot establish that an unretained inline did not exist.
- Available local related-build resources are map-name TSVs, not retained related
  ELF/DWARF files. No downloads were made.

## Separate measured attempts

Scores below are trial.py literal normalized-instruction similarity, not objdiff.
No score is exact.

1. Existing source baseline for extraction:167/173 instructions,24.1%.
   Retains the previously corrected cyclic Y-largest Z+X sum. Inspection shows
   trace computed from the original matrix load registers, without the target's
   reloads through persistent MATRIX3 address r31.
2. `retry-qmatrix-snapshot.cpp`: snapshot the full COORD4 input before constructing
   rotation. BuildQuatTrans73/66 instructions,17.3%;64-byte frame rather than48.
   The compiler copies the quaternion with integer loads/stores, giving a pointer
   to the quaternion copy rather than the target's rotation-address register.
   Rejected: it does not explain target matrix addressing or improve its form.
3. `retry-qmatrix-doubled-vector.cpp`: represent the doubled quaternion xyz as the
   real COORD3 type instead of three scalar locals. BuildQuatTrans67/66,19.5%;
   again64-byte frame. Three extra vector stack stores appear; rotation itself
   remains frame-relative. Rejected: near instruction count hides wrong lifetimes.
4. `retry-qmatrix-row-column.cpp`, BuildQuatTrans: use MATRIX3's actual m33 row/column
   view for all constant-index accesses.64/66,15.4%; normalized stream verified
   identical to current source object, so no patch is recommended.
5. Same row/column variant, ExtractQuatTrans:167/173,24.1%; normalized stream
   verified identical to current source object. Dynamic largest-diagonal access
   still uses the union's m view; no invented indexing helper was introduced.

Every diff is retained separately beside its source. `dump.py` emitted the actual
six GCC stages (.rtl,.combine,.regmove,.sched,.greg,.sched2) for each new source form.
The dumps/assembly confirm these representation changes cannot reproduce the target
matrix pointer's lifetime. No compiler-policy experiment was performed.

## Defensible remaining blocker

Both target routines retain a pointer to the genuine local MATRIX3 conversion object.
BuildQuatTrans uses r9 after its first frame-relative store. Extraction saves four
integer registers, including r31 for this matrix, and reloads its diagonals through
r31 before trace and its off-diagonal values after sqrtf. Current natural bodies
save only three integer registers and treat the matrix as an ordinary frame local.

A genuine pointer-taking inlined conversion API would explain that boundary. Neither
the mapped names nor the retained disc declarations establish its name/signature/body.
Inventing a helper, redundant pointer local, or escape solely to preserve that address
would cross the fidelity rule. No such workaround was tested or proposed.

Preserve current natural partials and their scores. A next attempt needs additional
realmath conversion-header/inline provenance or a new compiler mechanism evidenced
across the whole original unit; changing scalar/store order blindly is not that evidence.

No proposed tracked patch; no exact-match gain; no full-unit build needed because no
candidate is recommended. Quaternion nonnormalization, full translation including w,
strict diagonal ties, zero-root guard, and cyclic diagonal arithmetic remain intact.
