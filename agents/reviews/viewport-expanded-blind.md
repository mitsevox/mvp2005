# Expanded viewport blind review

Fresh reviewer saw anonymized target assembly only, never source/maps/ledgers.
All fourteen exact functions were included; partial BeginView was added afterward.
Initial packet omitted containing-constructor evidence: E/L receiver interpretations
were wrong or incomplete. A second anonymous caller clarified the distinct outer,
private and extension bases without revealing source names. BeginView then clarified
fog receiver offsets and stack dependencies. These were packet-context omissions,
not source fixes; both original assessments and amendments are retained below.

Root reconciliation: final semantic names and intent comments agree for 15/15.
Exact original spelling is supported separately by maps/DWARF or labelled inference.
External dependency identities are verified by the named target callees and fields;
reviewer's uncertainty on identities not exposed by the packet remains recorded.

# Blind semantic review of functions A–N

Reviewed only `packet.txt`; no source, name maps, ledgers, reconciliation files, or other agent results consulted. Names below are descriptive proposals, not recoverable original spellings. This is semantic review, not compiler-match verification. Offsets refer to the immediate argument base unless stated otherwise.

## A — `SetViewportBoundsAndDepthRange`

**Confidence:** high for rectangle/depth storage and clipping; moderate for projection refresh contract.

**Intent comment:** Store the requested viewport rectangle and depth range, derive its clipped coverage against the attached surface, and refresh perspective state when the projection-mode query permits it.

Stores six floats at 216..236: x, y, width, height and two depth parameters. Resets integer origin fields 328/332 to zero and converts requested width/height to unsigned integer fields 336/340 with truncation; these are not the clipped width/height. The virtual dependency supplies surface limits. All four rectangle endpoints are independently clamped to [0, respective limit]. Offset 412 records exact full-surface coverage after clamping, not merely whether the requested rectangle lies inside the surface.

Offsets 312..324 describe clipped limits relative to the original rectangle center and half-size. They become all 1 when clipped dimensions exactly equal requested dimensions, or clipped area is zero. The latter is a fallback sentinel, not evidence that an empty viewport has a valid ordinary frustum. Negative, zero, NaN, or extreme inputs are not generally validated. It calls External2; only a zero return rebuilds via B using cached parameters 240..252. Need External2 semantics before claiming all projection modes refresh or that this programs GX viewport/scissor hardware directly.

## B — `SetPerspectiveProjectionAndClipPlanes`

**Confidence:** high for perspective installation; moderate for trigonometric plane-cache interpretation.

**Intent comment:** Build and install the perspective projection from the supplied lens and clip parameters, then update coefficients used to test its clipped side planes.

Stores four arguments at 240..252, builds a matrix at 344 with `C_MTXPerspective` using a fixed aspect argument of 1, then multiplies its vertical scale by the supplied second argument before installing it with GX projection type 0. Offset 16 is set to 0. This is consistent with horizontal field of view plus width/height aspect, rather than blindly labeling the first argument vertical FOV from the SDK API name: the SDK sees the fixed aspect, and the code applies its own scale afterward. Near/far supplied in f3/f4 remain SDK near/far parameters.

The subsequent half-angle degree conversion and External4/5/6 chains look like tan, atan, and sin respectively, caching slope and plane-normal factors at 280..308 from clipped extents 312..324. Those exact dependency semantics must be confirmed before naming the caches as tangents/secants or guaranteeing unit-normal distances. Copies selected projection coefficients to 24..84; do not call these a full matrix copy. The matrix used later for fog begins at 332, not the SDK projection base 344; the surrounding representation needs its layout established.

## C — `ClearViewportBuffers`

**Confidence:** high.

**Intent comment:** Clear selected viewport buffers with an untextured rectangle, using the full-surface copy-clear shortcut when eligible, and reinstall the saved projection after a drawn clear.

Low flag bit 0 selects color writes; bit 1 selects depth writes. Full coverage (412), matching a global current-object pointer, both low bits set, and a nonzero External8 result enable the copy-clear setup path. If its color matches the cached global color, it returns immediately: no rectangle, projection restoration, or final invalidation occurs. If color differs, it calls `GXSetCopyClear(color, 0xFFFFFF)` and **continues** into the rectangle path; it does not simply return after setting copy clear.

Draws four rectangle corners in screen coordinates with stored color 20 and vertex z = 0x3f7ffffe (just below 1). Temporary orthographic projection has SDK near 0 and far -1; do not collapse those and the vertex z into a claim of 'depth exactly 1'. Enables depth test/write with comparison 7 when requested; otherwise disables both. Color is disabled only if bit 0 is absent, then unconditionally reenabled afterward. Restores GX projection type from offset 16 (0 perspective, otherwise 1 orthographic), but does not visibly restore every GX state changed. Clears another global word after the drawn path. External8/9/10 semantics are needed to name shortcut availability and the wrapped vertex-state setup exactly.

## D — `SpherePassesViewportClipTest`

**Confidence:** high for radius-expanded rejection; moderate for coordinate transform.

**Intent comment:** Transform the sphere center through the current transform, reject it beyond the near or far depth limits, and apply the cached side-plane tests only in perspective mode.

External12 constructs/copies a local transform from a global address; External13 writes the transformed center. Need their semantics to distinguish world-to-view, model-to-view, and another current transform. Radius is f1. Returns 0 when z+near > radius or -(z+far) > radius, consistent with negative forward view z; equality passes. Offset 16 nonzero returns 1 after those depth tests, **without orthographic left/right/top/bottom rejection**. Perspective tests radius against signed expressions using the side-plane caches from B. This is an intersection/conservative acceptance predicate, not complete containment, and it does not prove anything about occlusion. NaN and invalid radii are not explicitly handled.

## E — `InitializeViewportState`

**Confidence:** high for initialization; low for all field meanings.

**Intent comment:** Initialize viewport bookkeeping and rectangle/depth fields to their defaults, retain the supplied coverage flag, and seed the stored matrix region with an identity matrix.

Sets 0/8/396/404/408 to zero, offset 4 to 1, and 412 to caller r4. Offset 240 and all floats 204..236 become -1, so these are sentinels rather than a zero-size default viewport or usable clipping distances. Writes a 4x4 identity beginning at 332. Leaves numerous fields, including the projection-mode word at 16 and much of projection/cache state, untouched. Do not describe this as fully clearing or fully constructing every object member, assigning an owner, or establishing a complete usable projection. Offset 4's value 1 is especially likely a sentinel given K/N's unsigned >1 checks; its precise meaning needs External23 and callers.

## F — `ApplyAttachedFogState`

**Confidence:** high.

**Intent comment:** Apply the attached fog settings and optional range adjustment, or disable fog when that attachment explicitly marks it inactive.

Null pointer at offset 0 returns without touching GX fog, rather than disabling it. Otherwise follows pointer->pointer; first config word controls fog enable, fields 4/8 supply fog start/end, field 12 supplies type, field 16 supplies color. Enabled fog uses viewport floats 236 and 240 as SDK near/far inputs in that order; their meanings across all projection modes must be verified rather than replaced with a conventional pair. Optional config word 20 builds range-adjustment table using truncated low-16-bit width from 212 and matrix address 332. Adjustment center is trunc(204 + 0.5*212), clamped below at zero and then narrowed to 16 bits; no upper clamp. Enabled fog without adjustment explicitly disables range adjustment. Disabled fog calls GXSetFog with type 0 and all zero distance arguments, but does **not** explicitly reset range adjustment on that branch.

## G — `GetViewportBoundsAndDepthRange`

**Confidence:** high.

**Intent comment:** Write the stored viewport rectangle and depth values to the six caller-provided destinations in argument order.

Loads and stores 216, 220, 224, 228, 232, 236 sequentially, with no null checks or temporary snapshot. Output pointers may alias one another (later stores win), or alias object storage (earlier writes can affect later loads). A rewritten bulk snapshot/getter would change that behavior. Do not promise independent outputs or an immutable snapshot.

## H — `SetStoredTransformAndRefreshIfActive`

**Confidence:** high for copy; moderate for matrix role and refresh.

**Intent comment:** Copy the supplied 64-byte transform into stored state and invoke the active-state refresh dependency when its flag is set.

Copies 16 words into offset 88 in ascending order. It is a forward word copy, not overlap-safe memmove or a preloaded snapshot: partially overlapping input/destination can propagate overwritten words. An exact self-copy is harmless. Offset 408 nonzero calls N with **argument base +12**, which matters to N's field offsets. Likely a model/view transform, but the anonymous instructions do not alone identify it as model, view, or combined model-view. Need caller and N/External23 semantics to claim device upload or a particular activation operation.

## I — `SetNormalizedOrthographicProjection`

**Confidence:** high.

**Intent comment:** Install an orthographic projection with horizontal bounds -1..1, symmetric vertical bounds from the supplied half-height, and the supplied near/far depths.

`C_MTXOrtho` receives top = f1, bottom = -f1, left = -1, right = 1, near = original f2, far = original f3. Stores 240=0, 244=half-height, 248=near, 252=far; sets 16=1 and installs GX projection type 1. Copies selected coefficients to 24..84 and sets cached perspective coefficients to zero. This is not inferred pixel-coordinate orthographic projection, nor can 244 automatically be called an aspect ratio without caller evidence. Cached side-plane terms from B are not refreshed, consistent with D bypassing them in this mode.

## J — `SetPixelOrthographicProjection`

**Confidence:** high.

**Intent comment:** Install a top-left-origin orthographic projection spanning the stored viewport width and height with the supplied near/far depth limits.

SDK bounds are top=0, bottom=stored height 228, left=0, right=stored width 224; x/y origin 216/220 are not included. Stores 240=0, 244=0.75, 248=near, 252=far; sets 16=1 and installs GX type 1. Copies selected coefficients to the common cache and clears perspective-only coefficients. The fixed 0.75 is bookkeeping, not an argument used to scale this SDK matrix. 'Pixel' is a descriptive inference from width/height bounds, not proof of any particular screen resolution or pixel-center bias.

## K — `EndViewportState`

**Confidence:** moderate; dependency semantics unresolved.

**Intent comment:** End the viewport's active state, notify its attached backend, and process the saved state value when it is above the sentinel range.

Calls External22 on `*(this+12)+8` with 0, clears offset 408, calls External23 with the unsigned value at 4 only if it exceeds 1, and finally clears offset 4. It does not call deletion, clear the global current pointer visibly, or use a signed >1 check. Values 0 and 1 are deliberately excluded; a pointer/previous-state token interpretation is plausible, not established. Need External22/23 behavior before calling this resource release, previous-viewport restoration, or destruction.

## L — `SetFogAttachment`

**Confidence:** high for store; moderate for pointer type.

**Intent comment:** Replace the stored attachment used by fog application with the supplied pointer/value.

Single store to offset 0. Link to F supports a fog-configuration attachment interpretation. No ownership transfer, refcount operation, deletion, null filtering, or immediate GX application is visible.

## M — `DeleteViewportStorageIfRequested`

**Confidence:** high for deallocation; moderate for destructor classification.

**Intent comment:** Deallocate this object's storage only when the low bit of the destruction flags requests it.

Calls `__builtin_delete(this)` iff r4 bit 0 is set. It performs no visible cleanup of the fields/attachments examined above. Consistent with a deleting-destructor stub, but original class spelling and destructor ABI details are not recoverable. Do not describe it as always destroying/freeing or as invoking K.

## N — `ResetOwnerStateAndReapply`

**Confidence:** low-to-moderate beyond concrete operations.

**Intent comment:** Reset the owner selected by the context, process any saved state above the sentinel range, and unconditionally invoke the state dependency again for the current owner.

Gets owner from offset 412 of its own argument. Calls External22 on owner's attached backend with 0, clears owner's 408, conditionally calls External23 with owner's offset 4 when its unsigned value >1, clears that value, reloads owner from context+412, and calls External23 with the owner itself unconditionally. The reload can matter if callbacks mutate context. Calling this 'refresh/reapply' follows H's active-update use, but depends on External23's semantics; the final call cannot safely be labeled free/delete.

**Base-offset warning:** H calls N with its own base+12, so N reads owner from H-base+424, not H-base+412. N's owner field must not be conflated with the viewport full-coverage field in A/C/E. Similar-looking cleanup steps in K and N do not prove identical receivers or object layouts. Need context layout, External22, and External23 to resolve a confident lifecycle name.

## Principal review hazards

- Preserve G's sequential read/write alias behavior and H's forward overlapping copy behavior.
- Preserve E's -1 defaults and K/N's unsigned >1 sentinel tests.
- Preserve C's cached-color early return and its fall-through after GXSetCopyClear.
- Keep perspective (0) and orthographic (1) GX flags distinct; D's nonzero mode accepts after depth only.
- Keep depth parameters, matrix depth mapping, clear vertex z, and copy-clear integer depth separate.
- Confirm external math/transform/lifecycle dependency semantics before upgrading plausible interpretations to exact intent.

# Amendment after anonymous caller P

The first assessment overgeneralized receiver bases for E and L. The following supersedes their names/comments and the erroneous linkage from L to F.

## E corrected — `InitializeEmbeddedViewportState`

**Confidence:** high for embedded-state initialization and owner linkage; moderate for naming its exact class/subobject.

**Corrected intent comment:** Initialize the embedded state with sentinel geometry/projection parameters, an identity projection matrix, default mode and bookkeeping values, and a link back to its containing owner.

P calls E with r3 = P's receiver +12 and r4 = P's receiver. Therefore E's offset 412 receives an **owner pointer**, not a coverage flag. This independently explains H's call to N with base+12 and N's owner lookup at context+412: the owner lives at outer-base+424.

On that outer coordinate system, E's identity matrix beginning at relative 332 lies at outer+344, the projection matrix base used by B/I/J. E's relative 4=1 lies at outer+16, consistent with the orthographic projection-mode default in those routines; it is **not** K's outer+4 saved-state sentinel. E's -1 assignments land at outer+216..252, spanning viewport rectangle/depth and stored projection parameters, rather than the previous mistaken outer+204..236 interpretation. Relative 396=0 becomes outer+408 (H/K's active flag); relative 404/408=0 become outer+416/420. Relative 0/8 become outer+12/20. The numerical stores are certain; assigning shared meanings across functions still requires their receivers to be the same outer type, but the matrix and owner provenance provide substantially stronger evidence than offset coincidence.

E does not initialize outer+412, the full-coverage flag used by A/C. It also does not initialize outer+4. Thus the original E passage's 'supplied coverage flag' and association of its relative+4=1 with K/N's >1 tests are withdrawn. E's relative+0 is not F's outer+0 fog attachment. Its uninitialized-field caution remains valid, but the projection-mode field is now observed initialized to 1 in outer coordinates.

## L corrected — `InitializeOwnerLink`

**Confidence:** high for owner-link store in P; low for a broader standalone setter contract.

**Corrected intent comment:** Store the supplied owner pointer at the beginning of the destination object or subobject.

P calls L with r3 still equal to P's receiver and r4 explicitly set to that same receiver. Thus this call writes a self/owner link, not an evidenced fog attachment. L alone permits any value and destination; P establishes a construction/link-initialization use. It has no visible ownership/refcount/delete/apply effects. Exact subobject type and whether the original was a constructor or setter require more callers/ABI evidence. The initial name `SetFogAttachment` and assertion that offset coincidence links L to F are withdrawn.

## Changed dependency caveats

Receiver provenance must precede field naming. E/N's relative+412 owner and A/C's outer+412 coverage coexist at different addresses. E's relative+4 and K's outer+4 also coexist without sharing sentinel semantics. H/N's +12 adjustment is now explained by P's embedded-state initialization rather than merely flagged as an unknown offset. External22/23 semantics remain necessary to decide whether K/N deactivate, restore, or reapply state. F's attachment interpretation still follows its own GX fog use; L supplies no evidence for a setter of that attachment.

# Amendment after anonymous Function O

## O — `BeginViewportRendering`

**Confidence:** high for activation and GX programming; moderate for transform-composition order and backend-dependent horizontal offset.

**Intent comment:** Suspend the backend's active viewport while preserving its saved predecessor, activate this viewport, refresh transform caches, and program its viewport, scissor, projection, and fog state.

The global pointer at 0x8062c2b4 is assigned this receiver only when null. It is not unconditionally updated to the newly active viewport; calling it the current viewport pointer without qualification is unsafe. External25 on the attachment at outer+12 obtains a viewport-like pointer. The code calls it repeatedly, rather than snapshots one result. If nonnull and its active flag 408 is nonzero, this receiver's offset 4 gets that pointer; its prior offset 4 is saved across K and restored afterward through the reloaded this+4 pointer. If this receiver's offset 4 is zero after that path, it becomes sentinel 1. A preexisting nonzero value is retained otherwise. No same-receiver guard is visible. This establishes K/O/N's saved predecessor chain interpretation far more strongly, and connects earlier External23 to O: K's >1 call reactivates a saved predecessor; N ends/rebegins its owner through O.

Sets active flag 408 to 1 and passes this viewport to External22 through the attached backend. External12 initializes a local transform from outer+88; External24 combines/updates it using outer+24. The resulting 64 bytes go to outer+152; the original outer+88 transform is copied to two globals, including the source used by D. Without External24's implementation, the exact multiplication direction and transform convention remain unresolved. There is no visible GX matrix upload here, so 'program all GX matrices' overclaims this body.

A virtual call on the attachment writes dimensions to two local float outputs. Horizontal viewport offset starts at 0. If attachment+4 is nonzero, External26 on attachment+60 supplies that offset; otherwise the attachment is eligible for an alternate-field test through attachment+76, byte 24. When that byte is set, calls VIGetNextField and GXSetViewportJitter; otherwise GXSetViewport. Both pass x+horizontalOffset, y, width, height and stored depth-range floats 232/236 unchanged. Do not claim field jitter always happens, infer a fixed offset, or replace these viewport depth-range values with projection near/far.

Scissor calculation uses truncation toward zero and preserves this sequence:

- Raw left = trunc(x + unsigned offset328); raw top = trunc(y + unsigned offset332).
- Raw scissor right/bottom = raw left/top + unsigned width336/height340, using machine integer arithmetic, **before** lower-clamping left/top.
- Left/top are clamped below at zero.
- Right limit is min(surface width, trunc(x+viewportWidth), raw scissor right); bottom limit similarly uses height, trunc(y+viewportHeight), and raw scissor bottom. The comparisons convert signed integer endpoints to floats.
- GXSetScissor receives unsigned conversions of clampedLeft+horizontalOffset, clampedTop, rightLimit-clampedLeft and bottomLimit-clampedTop.

There is no explicit final nonnegative extent clamp or left<=right/top<=bottom guarantee. The horizontal offset affects scissor x but not the width computation. Rewriting this as generic intersection of two fully validated unsigned rectangles, flooring instead of truncating, clamping far endpoints below zero, or adding max(0,width/height) changes behavior on edge cases. Extreme input/overflow behavior is not validated.

Finally reinstalls matrix outer+344 with GX type 0 if mode16 is zero, otherwise type 1, and invokes F with **outer+12**. No clear draw is performed here. Its device calls are sequenced and may have side effects; replacing repeated External25 calls or predecessor reloads with cached values requires proving those dependencies pure/stable.

## F receiver correction established by O

O supplies F with outer+12. Consequently the original F commentary's caveat about an unusual near/far pair was caused by mixing receiver bases, and is withdrawn for this observed call. F's relative 236/240 are outer+248/252, the projection near/far values stored by B/I/J. Its fog-adjustment width relative212 is outer+224, horizontal origin relative204 is outer+216, and matrix relative332 is outer+344. These are coherent projection/viewport values. F's relative+0 is outer+12: the attached backend/context itself, followed by its config pointer. It is not outer+0, and L does not set that field in P. Existing F branch conclusions remain: null attachment leaves GX fog untouched; inactive fog does not explicitly reset range adjustment; enabled fog without range adjustment does explicitly disable adjustment.

## K/N naming confidence after O

K can now be described more confidently as `EndViewportRendering`: detach this active viewport, clear its active flag, and rebegin a saved predecessor when the saved pointer exceeds the 0/1 sentinel range, then clear its predecessor field. N can be described as `RebeginOwnerViewport`: end/reset its linked owner's viewport state, handle any saved predecessor, then begin the owner again through O. External22 is still an anonymous backend setter; the precise backend type and External25 query contract remain unidentified. The global assigned only when null must remain distinct from the backend's queried active viewport.
