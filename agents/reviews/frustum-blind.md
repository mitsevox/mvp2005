# Frustum instruction review, 2026-09-30

Both functions were reviewed from their original unnamed assembly, with no lane source,
headers, implementation report or naming rows shown. The reviewer was the full-disc-debug
agent, reused because the tool refused additional agent threads. It had previously read the
high-level camera investigation and supplied disc symbol evidence. This is independent
instruction analysis of 100% of this round, not complete contextual blindness.

The reviewer independently proposed `ViewPort::SetPerspective` for 0x803E0DD0 and
`ViewPort::IsSphereVisible` for 0x803E1850. The lane's `TestSphere` is equally accurate.
Names: 2 right, 0 wrong. Lane comments after integration: 2 right, 0 incomplete, 0 wrong.

Setup: horizontal FOV in degrees, effective width/height aspect, near/far distance limits,
hardware projection upload and matching side-plane coefficients are supported by instructions.
Sphere: transforms the center, leaves radius unchanged, rejects beyond the depth limits and
the perspective side planes, accepts equality for ordinary finite values, returns 0 or 1.

The reviewer's 'model-view matrix' phrase is not established by unnamed assembly and was not
adopted. Separate retail registration evidence identifies the backing of `gpViewMatrix`.
Both helper bodies support the affine point transform and 64-byte copy; assembly alone does
not prove the copy's exact constructor signature. That declaration remains explicitly T4.
