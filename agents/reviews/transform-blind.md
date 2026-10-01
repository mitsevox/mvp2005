# Independent anonymous assembly review

Evidence read: `packet.txt`, followed by the parent-authorized anonymous numerical data in `constants.txt` and anonymous EXTERNAL_024/025 bodies in `anonymous-callees.txt`. No source, headers, maps, original game names, documentation, or reconciliation evidence were read. Semantic labels below are proposals, not recovered names. Signatures use free-function notation even where the first pointer could be C++ `this`; exact constness and source-level return types generally are not recoverable from leaf assembly.

## Conventions established by the instructions

For clarity, define `Mat4::m[i][j]` at byte offset `16*i + 4*j`. This is a row-major notation, and the vector routines compute **row vector times matrix**. Translation occupies `m[3][0..2]`, offsets `0x30..0x38`. An equally valid column-major interpretation transposes these matrices and reverses named product order; the equations here remove that ambiguity.

`Vec3` contains three floats; `Vec4` contains four. Quaternion inputs/outputs use `(x,y,z,w)` in successive floats, with the scalar at offset `0xc`. The rotation convention is fixed by the actual matrix below, without claiming a global coordinate-system handedness:

```
R(q) = [ 1-2y²-2z², 2xy+2wz,   2xz-2wy
         2xy-2wz,   1-2x²-2z², 2yz+2wx
         2xz+2wy,   2yz-2wx,   1-2x²-2y² ]
```

Quaternion construction does not normalize its quaternion inputs. Rotation interpretation assumes unit input. Point transformation implicitly supplies homogeneous `w=1`, direction transformation supplies `w=0`, and full `Vec4` transformation preserves/calculates all four components without perspective division.

EXTERNAL_005 is strongly inferred to be square root from two standard algorithms. EXTERNAL_015 is strongly inferred to copy the specified byte count. Those anonymous callees were not themselves supplied. The trigonometric identities used below identify expected sine/cosine roles but do not independently prove callee implementations.

## Function findings

### F01 — construct from quaternion and four-component final row

Plausible signature: `void setQuaternionRow(Mat4* out, const Quat* q, const Vec4* finalRow)`.

Writes `R(q)` into the upper 3×3, zeros `m[0..2][3]`, and copies all four components of `finalRow` into `m[3]`. Unlike a fixed affine constructor, it does **not** force `m[3][3]=1`. Quaternion loads finish before matrix stores, but the final-row source is read afterward; arbitrary overlap of that source with output is unsafe.

Intent comment: `// Build a quaternion rotation and copy the supplied homogeneous final row.`

### F02 — extract quaternion and four-component final row

Plausible signature: `void extractQuaternionRow(const Mat4* in, Quat* q, Vec4* finalRow)`.

Copies the upper 3×3 into a compact temporary. For positive trace, sets `w=0.5*sqrt(trace+1)` and vector components from antisymmetric differences scaled by `0.5/sqrt(trace+1)`. Otherwise chooses the largest diagonal (strict comparisons, ties favor an earlier axis), computes that quaternion component first, then the other components. Nonpositive-trace branches skip reciprocal conversion when the square-root result is exactly zero. They do not clamp a negative radicand or normalize the result. It assumes a rotation-like 3×3; this is not scale/shear decomposition. Copies all four final-row floats afterward. The temporary protects the 3×3 reads from quaternion output writes; overlapping output with the input final row could still affect extraction.

Intent comment: `// Recover a quaternion from the rotation block and copy the full final row.`

### F03 — general 4×4 inverse with determinant return

Plausible signature: `float inverseTo(const Mat4* in, Mat4* out)`.

Calculates the full 4×4 determinant and adjugate; no affine or orthonormal shortcut. Returns determinant in `f1`, including on the early path. If `-epsilon < det < epsilon`, with epsilon approximately `1e-5`, exits without any destination stores. Equality with either threshold proceeds with inversion. Otherwise writes adjugate divided by determinant. The threshold is a strict open interval, not a Boolean success return and not a normalized determinant. All input accesses precede destination stores in this listing, so exact `in==out` appears safe; wrappers nevertheless may choose a snapshot. Exceptional IEEE inputs are not screened by explicit finite checks.

Intent comment: `// Return the determinant; write the inverse only when it is outside the open singularity interval.`

### F04 — affine point transform

Plausible signature: `void transformPoint3(const Mat4* m, const Vec3* in, Vec3* out)`.

For `j=0..2`, computes `out[j]=in.x*m[0][j]+in.y*m[1][j]+in.z*m[2][j]+m[3][j]`. Reads/writes exactly three floats. Does not compute output `w` or divide by it; ignores the matrix fourth column. Exact input/output equality uses a temporary, making an in-place point transform safe. Distinct partial overlaps are not protected, nor is arbitrary matrix/output overlap.

Intent comment: `// Transform a 3D point with implicit w=1, supporting exact in-place input.`

### F05 — full homogeneous vector transform

Plausible signature: `void transformVector4(const Mat4* m, const Vec4* in, Vec4* out)`.

Computes `out[j]=sum(in[k]*m[k][j], k=0..3)` for all four components. There is no perspective divide. A temporary protects exact `in==out`, but not arbitrary partial overlap.

Intent comment: `// Multiply all four homogeneous components by the matrix.`

### F06 — strided batch affine point transform

Plausible signature: `void transformPoints3(const Mat4* m, unsigned count, const void* in, int inStrideBytes, void* out, int outStrideBytes)`.

Argument registers are respectively `r3..r8`. Each element receives the same F04 point equation; strides are byte offsets, and either zero stride is replaced by 12. Zero count returns immediately. Initial equality of the two base pointers selects a per-element temporary; it does not require equal strides. This protects each currently read point, not future points against overlapping/differently-strided writes. A distinct overlapping range is not handled as a safe move. Count is used by `mtctr/bdnz`; a signed negative count would be a huge iteration count, so unsigned/nonnegative is the plausible contract.

Intent comment: `// Transform a strided array of 3D points, defaulting each zero stride to 12 bytes.`

### F07 — general matrix product

Plausible signature: `void multiplyTo(const Mat4* a, const Mat4* b, Mat4* out)`.

Computes `out[i][j]=sum(a[i][k]*b[k][j], k=0..3)`, hence `out=A*B` in the stated notation. Stores interleave with subsequent source loads: output must not alias either matrix in general. This is a full 4×4 product, including the homogeneous row and column.

Intent comment: `// Write A*B to a separate destination.`

### F08 — axis-angle rotation matrix in degrees

Plausible signature: `void setAxisAngleDegrees(Mat4* out, float angle, float axisX, float axisY, float axisZ)`.

Multiplies `angle` by approximately pi/180. If the converted angle equals zero, writes the identity without normalizing the axis. Otherwise evaluates sine/cosine-shaped helpers EXTERNAL_013/014, normalizes the three supplied axis components using the square root of their squared length, and builds Rodrigues rotation with the same row-vector signs as `R(q)`. Sets translation to zero and the affine fourth column to `(0,0,0,1)`. Nonzero angle with a zero-length axis is not guarded, so division by zero can contaminate the rotation block. No modulo reduction is visible here.

Intent comment: `// Build a degree-based axis-angle rotation, normalizing a nonzero-angle axis.`

### F09 — multiply current matrix on the right

Plausible signature: `void multiplyRight(Mat4* current, const Mat4* rhs)`.

Calls F07 with `(current,rhs,temp)` and copies 64 bytes back: `current=current*rhs`. With row vectors, the rhs acts after current. Temporary output makes exact `current==rhs` safe as squaring.

Intent comment: `// Compose the current transform followed by rhs.`

### F10 — four-dimensional diagonal matrix

Plausible signature: `void setDiagonal(Mat4* out, float x, float y, float z, float w)`.

Writes diagonal `(x,y,z,w)` and zeros all off-diagonal entries. The fourth diagonal is caller-controlled, not fixed at one; this can scale homogeneous `w` as well as xyz.

Intent comment: `// Set all four diagonal components and clear the remaining entries.`

### F11 — translation matrix

Plausible signature: `void setTranslation(Mat4* out, float x, float y, float z)`.

Writes identity plus `m[3][0..2]=(x,y,z)`.

Intent comment: `// Build an affine translation matrix.`

### F12 — identity matrix

Plausible signature: `void setIdentity(Mat4* out)`.

Writes all 16 components of the 4×4 identity.

Intent comment: `// Reset the matrix to identity.`

### F13 — expand a compact 3×3 and translation

Plausible signature: `void setLinearTranslation(Mat4* out, const Mat3* linear, const Vec3* translation)`.

Copies the nine contiguous input floats in row order into the upper 3×3, then writes xyz translation; fixes the fourth column to `(0,0,0,1)`. It does not impose orthonormality. In-place expansion from `linear==out` is unsafe because inserted zero stores overwrite later compact source floats.

Intent comment: `// Expand a compact linear block and xyz translation to an affine 4×4 matrix.`

### F14 — scaled Euler rotation and translation

Plausible signature: `void setScaleEulerTranslation(Mat4* out, float sx, float sy, float sz, float ax, float ay, float az, float tx, float ty, float tz)`.

The first eight floats arrive in `f1..f8`; the ninth is read from the incoming stack at old-SP+8. Each angle is divided by **360.0**, then passed to EXTERNAL_024/025. The supplied anonymous callee bodies multiply that phase by `6.2831854820251465` in double precision before calling standard `sin`/`cos` and rounding to float. Thus public angles are **degrees**, with a float-rounded approximation of 2*pi promoted to double in these helpers.

Let `sX/cX` etc be those helper results. The linear block is:

```
[ sx*cY*cZ,                    sx*cY*sZ,                   -sx*sY
  sy*(sX*sY*cZ-cX*sZ),        sy*(sX*sY*sZ+cX*cZ),        sy*sX*cY
  sz*(cX*sY*cZ+sX*sZ),        sz*(cX*sY*sZ-sX*cZ),        sz*cX*cY ]
```

This equals `S*Rx*Ry*Rz` for the row-vector rotation convention. Translation is copied directly, unscaled, into the final row; the affine fourth column is fixed. Euler order is established by this equation, not by a guessed original name.

Intent comment: `// Build row-scaled X-then-Y-then-Z Euler rotation with an independent translation.`

### F15 — extract compact linear block and xyz translation

Plausible signature: `void extractLinearTranslation(const Mat4* in, Mat3* linear, Vec3* translation)`.

Copies the upper 3×3 in row order and xyz final-row entries. Ignores all four fourth-column entries, including `m[3][3]`. It does not extract scale or rotation parameters. No general overlap guard; exact compression into the matrix base appears safe for the linear copy, but output interactions with the later translation reads can still matter.

Intent comment: `// Copy the compact 3×3 linear block and xyz translation.`

### F16 — raw matrix copy

Plausible signature: `void copyMatrix(Mat4* out, const Mat4* in)`.

Copies 64 bytes as integer words, preserving all bit patterns. Exact equality is harmless; forward interleaved copying is not a general overlapping-memory move. The destination register advances internally, so it should not be interpreted as returning the original output pointer.

Intent comment: `// Copy all 16 matrix words verbatim.`

### F17 — forwarding inverse wrapper

Plausible signature: `float inverseForward(const Mat4* in, Mat4* out)`.

Forwards unchanged arguments to F03 and preserves its `f1` result. No additional handling. A source-level void wrapper could discard that result without any different instructions; float is the more useful inferred signature, not certain type recovery.

Intent comment: `// Forward to the determinant-returning inverse routine.`

### F18 — inverse current matrix through snapshot

Plausible signature: `float invertInPlace(Mat4* current)`.

Copies all 64 input bytes to the stack, then calls F03 with `(snapshot,current)`. Preserves determinant in `f1`; as for F17, a source-level discarded return cannot be excluded. Near-singular failure leaves current unchanged because F03 makes no writes. There is no Boolean conversion.

Intent comment: `// Invert the matrix from a snapshot and preserve it when the determinant is too small.`

### F19 — in-place transpose

Plausible signature: `void transposeInPlace(Mat4* current)`.

Swaps the six off-diagonal pairs; keeps diagonal entries unchanged. Handles the full 4×4, including translation/homogeneous entries.

Intent comment: `// Swap all off-diagonal pairs in place.`

### F20 — transpose to output, with exact alias support

Plausible signature: `void transposeTo(const Mat4* in, Mat4* out)`.

Writes `out[i][j]=in[j][i]`. Exact equality redirects output to a stack temporary and copies it back. Distinct partial overlaps are not protected.

Intent comment: `// Transpose all four rows and columns, supporting identical input and output.`

### F21 — right-compose four-component diagonal scale

Plausible signature: `void scaleRight(Mat4* current, float x, float y, float z, float w)`.

Constructs `D=diag(x,y,z,w)`, computes `current*D` into a temporary, and copies back. Thus each column is scaled, including xyz translation components and all entries of the fourth column. With row vectors, this scale acts after current; it is not merely local-basis scaling.

Intent comment: `// Apply a four-component diagonal scale after the current transform.`

### F22 — right-compose degree-based axis-angle rotation

Plausible signature: `void rotateRightDegrees(Mat4* current, float angle, float axisX, float axisY, float axisZ)`.

Builds F08 rotation `R`, then computes `current*R` via a temporary. The current xyz translation is rotated too. Inherits F08's degree conversion, zero-angle identity shortcut, axis normalization, and absent zero-axis guard.

Intent comment: `// Apply an axis-angle rotation after the current transform.`

### F23 — right-compose translation

Plausible signature: `void translateRight(Mat4* current, float x, float y, float z)`.

Builds affine translation `T` and computes `current*T`. For an affine current matrix it adds `(x,y,z)` directly to the final xyz row; for a general matrix each row's fourth component contributes to its xyz additions.

Intent comment: `// Apply a translation after the current transform.`

### F24 — snapshot rhs then right-compose

Plausible signature: `void multiplyRightSnapshot(Mat4* current, const Mat4* rhs)`.

First copies rhs to a stack matrix, then computes `current*snapshot` into another temporary and copies back. Semantically the same multiplication side as F09, with an explicit rhs snapshot. Exact self-composition is safe.

Intent comment: `// Snapshot rhs and compose it after the current transform.`

### F25 — left-compose four-component diagonal scale

Plausible signature: `void scaleLeft(Mat4* current, float x, float y, float z, float w)`.

Constructs `D` and passes it to F31, yielding `current=D*current`. Scales matrix rows, so xyz basis rows receive x/y/z and the final row, including translation, receives w. With `w=1`, translation is unchanged and this is a local-input scale.

Intent comment: `// Apply a four-component diagonal scale before the current transform.`

### F26 — snapshot lhs then left-compose

Plausible signature: `void multiplyLeftSnapshot(Mat4* current, const Mat4* lhs)`.

Copies lhs to the stack and passes it to F31, yielding `current=snapshot*current`. Exact self-composition is safe.

Intent comment: `// Snapshot lhs and compose it before the current transform.`

### F27 — 3D direction transform

Plausible signature: `void transformDirection3(const Mat4* m, const Vec3* in, Vec3* out)`.

Computes F04's equation without translation: `out[j]=sum(in[k]*m[k][j],k=0..2)`. Reads/writes three floats, ignores fourth row and column, and supports exact in-place input with a temporary. This is a generic linear direction transform, not automatically a mathematically correct normal transform under nonuniform scale/shear.

Intent comment: `// Transform a 3D direction with implicit w=0.`

### F28 — scale/quaternion/translation matrix from scalar arguments

Plausible signature: `void setScaleQuaternionTranslation(Mat4* out, float sx, float sy, float sz, float qx, float qy, float qz, float qw, float tx, float ty, float tz)`.

`f1..f3` scale the respective three rows of `R(q)`; `f4..f7` are `(qx,qy,qz,qw)`. `f8` is tx, with ty/tz at old-SP+8/+12. Final row is `(tx,ty,tz,1)` and the upper fourth column is zero. No quaternion normalization. Under the established notation this is `S*R(q)*T`.

Intent comment: `// Build row-scaled quaternion rotation with independent xyz translation.`

### F29 — quaternion/translation matrix from scalar arguments

Plausible signature: `void setQuaternionTranslation(Mat4* out, float qx, float qy, float qz, float qw, float tx, float ty, float tz)`.

Writes the same `R(q)` as F01/F28 with translation xyz from `f5..f7`; fixes the affine final component to one. No normalization. Unlike F01, there is no caller-provided homogeneous final component.

Intent comment: `// Build an affine quaternion rotation and xyz translation.`

### F30 — reversed-argument product to separate destination

Plausible signature: `void multiplyReversedTo(const Mat4* a, const Mat4* b, Mat4* out)`.

Swaps `r3/r4` and calls F07, yielding `out=B*A`. Inherits F07's lack of output/input alias protection. Merely reversing the call does not create a safe in-place product.

Intent comment: `// Write B*A to a separate destination.`

### F31 — multiply current matrix on the left

Plausible signature: `void multiplyLeft(Mat4* current, const Mat4* lhs)`.

Calls F07 with `(lhs,current,temp)`, then copies back: `current=lhs*current`. With row vectors, lhs acts before current. Temporary output protects exact self-composition.

Intent comment: `// Compose lhs followed by the current transform.`

## Missing anonymous context

1. Anonymous bodies of EXTERNAL_005,013,014,015 would confirm square root, ordinary sine/cosine, and byte copy rather than leaving their identities algorithmically inferred.
2. Stripped callers that consume or discard F17/F18 returns would distinguish their source-level return contracts. F03's determinant computation and return are directly visible; wrappers preserve that register but cannot prove declared types.

All F01 through F31 were independently investigated, including forwarding/copy wrappers.
