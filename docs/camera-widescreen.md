# Camera projection and frustum culling (GV4E69)

Investigated 2026-09-30 against the retail DOL, SHA-1
`da6becdbea614d03c4b5eae9f8a0fb08e0a184dd`. The local baseline rebuild ends with
`main.dol: OK`. These are reverse-engineering findings, not newly matched C,
an in-game widescreen test, or a shipped fix. Descriptive function labels below
are ours; the functions retain their existing symbols.

## Finding

The EAGL viewport path has a sphere/frustum visibility test. The same setup
function constructs the GPU projection and the CPU side-plane coefficients.
Changing only the uploaded projection can leave the CPU rejecting objects in
the widened screen edges. Changing the setup inputs updates both paths.

The original path already contains conditional 4:3 and 16:9 constants. This is
evidence of aspect-related logic, not proof that a working widescreen mode is
available to the player, or that an existing widescreen patch is broken.

## Functions and direct connections

| Address / symbol | Size | Behavior established from instructions |
| --- | --- | --- |
| `0x803E0DD0` / `fn_803E0DD0` | `0x1CC` | Stores horizontal FOV, effective aspect, near and far; builds and uploads projection; derives four side-plane coefficient pairs. |
| `0x803E1850` / `fn_803E1850` | `0x13C` | Transforms a sphere center by the current matrix; rejects against near/far and, for perspective, four side planes. Returns 0 for rejection, 1 otherwise. |
| `0x803E0ACC` / `fn_803E0ACC` | `0x304` | Sets viewport rectangle and clipping factors; re-runs projection setup using stored inputs for the perspective case. |
| `0x8031E878` / `fn_8031E878` | `0xE8` | Game-side caller: obtains aspect and camera FOV, applies multipliers, obtains depth limits, calls `0x803E0DD0` at `0x8031E93C`. |
| `0x8031E9E4` / `fn_8031E9E4` | `0x39C` | Calculates viewport rectangle and effective aspect, including cropping and camera adjustments. |
| `0x802D38E8` / `fn_802D38E8` | `0x38` | Returns 4/3 when either of two game-state flags is nonzero, otherwise 1. Used as a FOV multiplier. |
| `0x802D3920` / `fn_802D3920` | `0x38` | Returns 16/9 for the same flag condition, otherwise 4/3. Used in effective aspect calculation. |

The last two functions read the object pointer at `0x8061FEDC`, then words at
object offsets `0x204` and `0x208`. Their original field names, the flag owners,
and how the flags are set have not been established. Do not name them
`widescreenEnabled` without further evidence.

Projection setup also has direct callers at `0x80241FBC` and `0x803E0DA8`.
The sphere test has four direct callers:

- `0x801874AC` in `fn_801873D0`;
- `0x802403DC` in `fn_80240284`;
- `0x803D697C` in `fn_803D68AC`;
- `0x803D6DE0` in `fn_803D6C84`.

Each caller branches away when the result is zero. These sites establish that
the test participates in game-side visibility decisions and EAGL processing;
the precise objects/actors handled by each caller remain to be identified.
This direct-call inventory does not exclude indirect callers or other cullers.

The unit placement comes from `config/GV4E69/filemap.tsv`: the reference SN map
places `libeaglsnz.a(viewport.o)` starting at `0x803E0ACC`. Its end is still open.
Do not declare this reconstructed subset a complete original source unit.

## Projection convention

The first float argument to `0x803E0DD0` is **horizontal FOV in degrees**, despite
Nintendo's `C_MTXPerspective` naming its argument `fovY`. At `0x803E0E08`, EAGL
passes aspect 1 to that SDK routine; at `0x803E0E44` it multiplies matrix element
`[1][1]` by the saved second argument. Thus, with `T = tan(horizontalFOV / 2)`:

```
projection[0][0] = 1 / T
projection[1][1] = effectiveAspect / T
horizontal half-extent at depth d = d * T
vertical half-extent at depth d = d * T / effectiveAspect
```

The input parameters are saved at viewport offsets `0xF0`, `0xF4`, `0xF8`,
`0xFC`. The projection matrix starts at `0x158`. At `0x803E0E90`, the setup
uploads it with `GXSetProjection`.

Effective aspect is not necessarily raw framebuffer width/height. The
game-side rectangle helper computes a cropped width/height ratio, multiplies
by `0x802D3920`'s result and a camera-side value at offset `0xAC`, and returns
the result through its first output pointer (`0x8031ED30`). Camera field names
and the physical pixel/display convention still need confirmation.

## CPU frustum data

`0x803E0DD0` computes `T` using the constants 0.5 and pi/180, then derives four
angles from the clipping factors at `0x138..0x144`. For an unclipped viewport
those factors are all 1 (written by `0x803E0ACC` at `0x803E0D18..0x803E0D24`).
In clipping-factor order:

```
leftAngle   = atan(-T * factor138)
rightAngle  = atan( T * factor13C)
topAngle    = atan( T * factor140 / effectiveAspect)
bottomAngle = atan(-T * factor144 / effectiveAspect)
```

Each angle becomes a pair `(tan(angle), sin(pi/2 - angle))`, stored at
`0x118/0x11C`, `0x120/0x124`, `0x128/0x12C`, and `0x130/0x134`. The second
component normalizes the side-plane distance for the sphere-radius comparison.
The visibility function reads all eight values. It does not construct its own
independent hardcoded 4:3 frustum.

The sphere's transformed Z is negative in front of the camera. Near/far
rejections are `z + near > radius` and `-(z + far) > radius`. The perspective
side tests compare normalized signed plane distances with the radius. When
the projection-mode word at `0x10` is nonzero, this function skips the side
tests; its orthographic behavior should not be generalized from this path.

## What a widescreen experiment should change

For a Hor+ view that preserves the original vertical framing, change both
setup inputs together:

```
newHorizontalFOV = 2 * atan(tan(oldHorizontalFOV / 2)
                            * newEffectiveAspect / oldEffectiveAspect)
```

Angles in that expression are radians; convert to degrees for the setup call.
For an illustrative 60-degree horizontal FOV at 4:3, changing to 16:9 gives
75.178179 degrees, not 80 degrees. The existing helper's linear 4/3 FOV
multiplier is different from this framing-preserving conversion; that alone
does not establish a bug in EA's intended camera composition.

The setup routine is the common dependency to recover first. Apply any
experimental change in a separate mod/patch artifact, preserving the matching
decomp's retail behavior. Do not blindly replace every aspect constant: PIP,
cropped viewports, alternate cameras and the other direct setup caller need
their own coverage. Changing cached side coefficients alone is also fragile:
viewport changes regenerate them from the saved inputs.

## Reproduction and validation

Run after configuring and building:

```
python3 tools/research/widescreen.py
```

The tool verifies the retail hash, checks the generated assembly's setup/test
coefficient connections, reports direct callers and reads the relevant float
constants from the original DOL. Its mathematical reconstruction agrees with
an independent six-normalized-plane reference for 12,000 random spheres across
three FOVs, two aspects and full/asymmetric clipping factors. A Hor+ example
admits spheres at both new horizontal edges while retaining rejection beyond
vertical, near and far bounds.

These checks use double-precision host mathematics. They do not execute the
PowerPC functions, reproduce every single-precision rounding/NaN case, or
prove correct on-screen rendering. No functions were promoted to matching and
no game behavior was changed.

Remaining runtime work: identify the two aspect flags and the active viewport
at a gameplay camera update; capture the FOV/aspect and coefficient values;
test both new side edges, camera changes/replays, PIP and UI framing in Dolphin.
At the time of this trace the checkout contained only `main.dol`, so that
runtime test was not performed.

## Disc inspection follow-up (2026-09-30)

The owner's GameCube disc was subsequently inspected (see
`docs/disc-inspection.md`). Its `libmatd.a` rendering archive retains debug
metadata with EA's `ViewPort`, `ViewPortPrivate`, `VPFrustum` and `VPCullData`
declarations. `ViewPort::mPrivate` starts at `0x0C`;
`ViewPortPrivate::mFrustum` at `0xE4` and `mCullData` at `0x10C`. Together they
give the exact `0xF0` and `0x118` offsets traced above.

EA's frustum field names are `mFOV`, `mAspect`, `mNearPlane`, `mFarPlane`.
The cull-data pairs are `mLeftTan/mLeftSin`, `mRightTan/mRightSin`,
`mTopTan/mTopSin`, `mBottomTan/mBottomSin`; the four factors previously
described as clipping factors are `mLeftScale`, `mRightScale`, `mTopScale`,
`mBottomScale`. The debug layouts agree with the main executable's accesses.
Use these actual types/names when starting the matching work; the functions'
original method names remain unestablished. A complete disc copy is now
available in ignored scratch for runtime investigation.
