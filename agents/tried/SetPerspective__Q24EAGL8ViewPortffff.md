# ViewPort::SetPerspective (0x803E0DD0)

Integrated source slice: `src/eagl/viewport_projection.cpp`, NonMatching. Root objdiff measures
96.347824% fuzzy (different metric from instruction-identical percentage below). Retail asm
remains linked; root source-linked sphere plus this partial slice builds `main.dol: OK`.

2026-09-30, frustum-setup lane. Retail target 115 instructions / 0x1CC bytes.
Natural shared EA ViewPort/VPFrustum/VPCullData/MATRIX4 declarations from the disc's
InstanceCrowd.o DWARF. No game behavior changed.

| Attempt | trial.py instruction similarity | Result |
| --- | --- | --- |
| Initial direct field writes; inherited GameLib -Os -G0 -ffloat-store | 23.2% | Parameter and angle homes absent in target; canonical libm C linkage also missing. |
| -O2 -G0, no float-store; libm declarations fixed to C linkage | 94.8% | 115 instructions; only zero-store scheduling and mode/half-FOV setup differ. |
| -fno-strength-reduce additionally | 94.8% | No change. |
| All six orders for matrix zero entries 12,13,15; each tested nested half-angle, updated fov, named halfFOV, and M_PI macro | 93.0%..95.7% | Best clear ascending indices12,13,15. Updated fov also alters initial store scheduling. |
| Named halfFOV before mode assignment; converted halfFOV before mode; mode after tanf; divide-by-two; swapped multiply operands; swapped degree conversion order | 95.7% | All remain nonexact. Mode after tanf additionally moves mode store later. |
| ProDG 3.5,3.5b140,3.7,3.8.1,3.9.3 | 95.7% each | Identical instructions across compilers. |
| -O3, -Os without float-store | 95.7% each | Same as O2. |
| Disable first scheduling / second scheduling / both / O1 | 67.5% /90.4% /60.5% /60.5% | Much larger differences. |
| No rerun-cse-after-loop, no expensive-optimizations | 95.7% each | No change. |
| mcpu750,mtune750; mcpu604,mcpu603 | 95.7%,95.7%;86.1%,87.0% | Default schedule fits target better. |
| Disable gcse,cse-follow-jumps,cse-skip-blocks,sched-interblock,sched-spec,caller-saves,peephole,optimize-register-move | 95.7% each | No change. |
| fast-math | 96.0% | Only112 instructions; not target. Not retained. |
| no-fused-madd,unroll-loops,no-branch-count-reg,no-regmove | 95.7% each | No change. |
| no-omit-frame-pointer | 87.1% | 117 instructions. |
| no-math-errno,no-guess-branch-probability | no score | Compiler rejects unsupported options. |

Best source remains natural O2 -G0 (no float-store), 95.7% instruction similarity,
115 instructions. Five instruction/register scheduling differences immediately
after GXSetProjection, before first tanf. One explained MATCH note on zero-store order.
No fake matches or banned tricks. Root must keep this source slice NonMatching until exact.

Reproducible trial scripts and detailed diffs are in the ignored scratch folder:
try_setup.py, try_mode.py, try_flags.py, try_compilers.py. They edit scratch candidates only.
