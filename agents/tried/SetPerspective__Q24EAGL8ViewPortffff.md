# ViewPort::SetPerspective (0x803E0DD0)

Integrated source: `src/eagl/viewport_projection.cpp`, Matching. Root independently rebuilt
both viewport source slices: `main.dol: OK`; setup objdiff is 100% / 460 code bytes,
24 literal bytes linked, and sphere remains 100% / 316 code bytes, 4 literal bytes linked.

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

Initial best source remained natural O2 -G0 (no float-store), 95.7% instruction similarity,
115 instructions. Five instruction/register scheduling differences immediately
after GXSetProjection, before first tanf. One explained MATCH note on zero-store order.
No fake matches or banned tricks. At that stage the source slice stayed NonMatching.

Reproducible trial scripts and detailed diffs are in the ignored scratch folder:
try_setup.py, try_mode.py, try_flags.py, try_compilers.py. They edit scratch candidates only.

## Compiler-internals follow-up: exact recovery

2026-09-30, explicit owner request. Successful SN diagnostic flags: -dr (initial RTL),
-dc (combine), -dN (register movement), -dS (first scheduler), -dg (allocation/reload),
-dR (second scheduler). -fsched-verbose=9 is rejected by this SN build. Upstream GCC2.95.3
pass documentation: https://gcc.gnu.org/onlinedocs/gcc-2.95.3/gcc_14.html .

Baseline regmove has mode store insn131 before the two constant loads. First scheduling
moves both literal address/load chains ahead of it. Baseline load of radians conversion
constant is mem/u:SF (unique readonly), with no dependency on the mode store. Allocation
then assigns r9/r11 to those chains; second scheduling preserves their resulting order.
This localizes the difference to first scheduling and inherited allocation, rather than
proving how the unavailable original source or compiler ran.

| New diagnostic/attempt | trial instruction similarity | Result |
| --- | --- | --- |
| -fno-strict-aliasing / -fstrict-aliasing | 95.7% each | Same instructions and dependency graph. |
| -fforce-mem / -fno-function-cse | 95.7% each | Same instructions. |
| Original named DegToRad(float) inline, converting half FOV | **100.0%** | **115 identical instructions; no call to the helper emitted.** |
| Same helper converting whole FOV before multiply0.5 | 99.1% | One scheduling difference. |
| Named halfFOV local initialized with DegToRad(fov*0.5f) | **100.0%** | Same exact result; direct expression retained. |

The full disc catalogue supplies a genuine EA conversion helper, not an invented
compiler-forcing wrapper: libmatd.a(Texture.o), archiveSHA1
91b461b8382ab3309cbf5b6687f95622a02edaa2, objectSHA1
5d2295fd9b52737de0d3fd1ce81837a08621c366. .debug0x24C8 names DegToRad and float return;
formal parameter0x24E6 is float deg. Double overload is at0x2538. Original body is not
retained; its multiply expression is reconstructed from retail math and exact build.
Global placement follows the realmath free-function declarations and is not claimed as
namespace proof from this old debug format.

Measured cause: after inlining, .regmove radians load insn145 is mem:SF, without the /u
flag. .sched explicitly adds mode-store insn131 to this load's dependency list. This
enforces the target's mode/constant order and subsequent integer-register assignments.
The original binary agreeing with this source is evidence for the natural helper use,
not proof that this is EA's precise original expression or spelling at the call site.

Final source-linked proof: configure Object(Matching), text803E0DD0..803E0F9C,
literal rodata8060C81C..8060C834; ninja ends main.dol: OK. Trial is100%/115instructions.
All relocations and literal bytes therefore agree after linking, not merely in normalized
instruction diff. One MATCH note remains for matrix zero ordering; no fake matches.

New ignored reproduction scripts/dumps: rtl_diagnostics.py, try_conversion_context.py,
rtl-baseline/, rtl-degtorad/. No RTL or game payload is added to tracked files.
Friction: one unrelated libc/mbtowc_r assembler wibo timeout during full rebuild; existing
30-second retry succeeded, then exact DOL check passed.
