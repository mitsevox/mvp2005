# Final scoped validation

Source verdict: SHIP. Tool verdict: SHIP (unchanged from trial-tool-review.md). Shared policy: supported measured reconstruction, with the limitations recorded in docs/compiler.md.

Rechecked prior FAILs and changed scope only; unchanged first-pass PASS items are carried forward.

- Prior item 7: transform.cpp:461 now uses appended.m = *matrix, consistently with PrependMatrix at line 475. The alias comments at lines 458 and 472 correctly describe the snapshots made before composition.
- Prior item 8: name_sources.tsv now records PostMult/PreMult parameter transform as a T4 spelling guess, distinct from its map-established type.
- Prior item 13: the redundant SetMatrix comment is removed; its three-line assignment remains plain. Transpose at line 390 explains why the in-place overload exists.
- Transpose at line 392 uses one reusable scalar for six real swaps. BuildRotate lines 216–218 compute three reused sine/axis products, each used twice in the Rodrigues terms and recorded as T4 spelling guesses. Neither change introduces a dummy local, alias cast, offset hack or unsupported inline helper.
- ExtractQuatTrans line 83 now evaluates the Y-largest sum as Z + X, agreeing with the original fadds operand order at 0x803DE6B0. The algorithm and branch/output contracts remain intact.
- The 30 written definitions follow the original function sequence, retaining the omitted Invert assembly range. The known emitted-order difference remains documented; source order is not represented as complete object equivalence.

The actual Ninja commands for both full EAGL units contain -O2 -G0 -finline-functions through the shared EaglLib policy, with no unit/function override. docs/compiler.md now records the independent three-policy full-unit experiment, five gains and zero losses, O3/O2inline indistinguishability, the final combined counts and NonMatching limitation.

I compared final build/GV4E69/src/eagl/transform.o with the original build/GV4E69/obj/eagl/transform.o for all five inlining gains. Normalized instruction sequences agree, and a separate ELF relocation inspection resolves the literal bytes instead of collapsing their names:

| Function | Instructions | Actual retained calls | Literal float bits |
| --- | ---: | --- | --- |
| AppendScale | 36 | MultMatrix, MEM_copy | 00000000 |
| AppendRotate | 20 | BuildRotate, MultMatrix, MEM_copy | None |
| AppendTranslate | 38 | MultMatrix, MEM_copy | 3f800000, 00000000 |
| AppendMatrix | 46 | MultMatrix, MEM_copy | None |
| PrependScale | 28 | PreMult | 00000000 |

Relocation kinds and corresponding literal bit sequences agree in target and candidate. Instruction comparison includes matrix argument setup, destination/source registers and the MEM_copy size 64. Detailed relocation results are saved in final-gained-bindings.json.

The current actual combined report confirms transform 25/31 exact functions and 4,760 matched code bytes, viewport 15/17 and 5,092 bytes. Independently comparing exact function virtual-address sets in baseline.json and the current report gives 1,139 before, 1,165 after and zero lost addresses. I independently ran dtk shasum -c config/GV4E69/build.sha1 and received build/GV4E69/main.dol: OK.

That DOL check links original assembly for both NonMatching objects. It validates the configured combined build, not replacement of the incomplete source objects or their data. The source-fidelity verdict does not depend on the score and does not certify full compiler/object equivalence.
