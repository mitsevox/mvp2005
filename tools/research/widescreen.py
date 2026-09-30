#!/usr/bin/env python3
"""Inspect MVP's projection/culling path and check its recovered geometry.

Read-only: no patch, symbol rename, or game output. Requires the USA main.dol
and a configured build's generated assembly. The numerical checks use a
double-precision mathematical reconstruction, not execution of the game.
"""
import hashlib
import math
import random
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HASH = "da6becdbea614d03c4b5eae9f8a0fb08e0a184dd"
TARGETS = {
    "SetPerspective__Q24EAGL8ViewPortffff": "projection and side-plane coefficient setup",
    "TestSphere__CQ24EAGL8ViewPortRC6COORD3f": "sphere/frustum visibility test",
    "fn_8031E878": "game-side projection caller",
    "fn_8031E9E4": "viewport rectangle and effective aspect calculation",
    "fn_802D38E8": "conditional FOV multiplier",
    "fn_802D3920": "conditional aspect multiplier",
}


def functions():
    result = {}
    for path in sorted((ROOT / "build/GV4E69/asm").rglob("*.s")):
        name, body = None, []
        for line in path.read_text().splitlines():
            if line.startswith(".fn "):
                name, body = line.split()[1].rstrip(","), []
            elif line.startswith(".endfn ") and name:
                result[name] = (path, body)
                name = None
            elif name:
                body.append(line)
    return result


def parameters(fov_x, aspect, crop=(1.0, 1.0, 1.0, 1.0)):
    tangent = math.tan(math.radians(fov_x) / 2.0)
    angles = (
        math.atan(-tangent * crop[0]),
        math.atan(tangent * crop[1]),
        math.atan(tangent * crop[2] / aspect),
        math.atan(-tangent * crop[3] / aspect),
    )
    # Pairs at +0x118..+0x134: signed tangent, plane normalization.
    return [(math.tan(a), math.sin(math.pi / 2.0 - a)) for a in angles]


def recovered_visible(point, radius, planes, near=1.0, far=1000.0):
    """Branch structure read from 0x803E1894..0x803E1970, camera space."""
    x, y, z = point
    if z + near > radius or -(z + far) > radius:
        return False
    left, right, top, bottom = planes
    distance = z * right[0] + x
    if distance > 0.0:
        if distance * right[1] > radius:
            return False
    else:
        distance = z * left[0] + x
        if distance < 0.0 and distance * -left[1] > radius:
            return False
    distance = z * top[0] + y
    if distance > 0.0:
        if distance * top[1] > radius:
            return False
    else:
        distance = z * bottom[0] + y
        if distance < 0.0 and distance * -bottom[1] > radius:
            return False
    return True


def geometric_visible(point, radius, planes, near=1.0, far=1000.0):
    """Independent reference: signed distances to six normalized planes."""
    x, y, z = point
    left, right, top, bottom = [p[0] for p in planes]
    distances = [
        z + near,
        -z - far,
        -(x + z * left) / math.hypot(1.0, left),
        (x + z * right) / math.hypot(1.0, right),
        (y + z * top) / math.hypot(1.0, top),
        -(y + z * bottom) / math.hypot(1.0, bottom),
    ]
    return all(d <= radius for d in distances)


def verify_geometry():
    rng = random.Random(2005)
    count = 0
    for fov in (30.0, 60.0, 100.0):
        for aspect in (4.0 / 3.0, 16.0 / 9.0):
            for crop in ((1.0, 1.0, 1.0, 1.0), (0.8, 0.9, 0.7, 0.95)):
                planes = parameters(fov, aspect, crop)
                for _ in range(1000):
                    point = tuple(rng.uniform(-1200.0, 1200.0) for _ in range(3))
                    radius = rng.uniform(0.0, 100.0)
                    assert recovered_visible(point, radius, planes) == geometric_visible(point, radius, planes)
                    count += 1

    old_fov, old_aspect, new_aspect = 60.0, 4.0 / 3.0, 16.0 / 9.0
    new_fov = math.degrees(2.0 * math.atan(
        math.tan(math.radians(old_fov) / 2.0) * new_aspect / old_aspect))
    old_tan = math.tan(math.radians(old_fov) / 2.0)
    new_tan = math.tan(math.radians(new_fov) / 2.0)
    assert math.isclose(old_tan / old_aspect, new_tan / new_aspect)
    old, wide = parameters(old_fov, old_aspect), parameters(new_fov, new_aspect)
    # Points newly visible on each horizontal edge, beyond the old side planes.
    x = 100.0 * (old_tan + new_tan) / 2.0
    for point in ((x, 0.0, -100.0), (-x, 0.0, -100.0)):
        assert not recovered_visible(point, 0.25, old)
        assert recovered_visible(point, 0.25, wide)
        # Widening the GPU alone leaves this false result in the old CPU test.
    for point in ((0.0, 50.0, -100.0), (0.0, -50.0, -100.0),
                  (0.0, 0.0, 10.0), (0.0, 0.0, -1100.0)):
        assert not recovered_visible(point, 0.25, old)
        assert not recovered_visible(point, 0.25, wide)
    print(f"Geometry model: {count} sphere cases agree with six-plane reference")
    print(f"Hor+ example: {old_fov:.1f} -> {new_fov:.6f} degrees horizontal FOV")
    print("Both new side edges pass; vertical, near and far rejection remain intact")
    print("These are mathematical checks, not PowerPC or Dolphin execution")


def main():
    raw = (ROOT / "orig/GV4E69/sys/main.dol").read_bytes()
    assert hashlib.sha1(raw).hexdigest() == HASH, "unexpected game version"
    offsets = struct.unpack_from(">18I", raw)
    addresses = struct.unpack_from(">18I", raw, 0x48)
    sizes = struct.unpack_from(">18I", raw, 0x90)

    def read_float(address):
        for offset, base, size in zip(offsets, addresses, sizes):
            if base <= address <= base + size - 4:
                return struct.unpack_from(">f", raw, offset + address - base)[0]
        raise ValueError(hex(address))

    print(f"GV4E69 original SHA-1: {HASH}")
    fs = functions()
    for name, purpose in TARGETS.items():
        assert name in fs, f"missing generated assembly: {name}"
        print(f"{name}: {purpose}")
        for caller, (_, body) in fs.items():
            for line in body:
                if re.search(r"\bbl " + re.escape(name) + r"$", line):
                    print(f"  caller {caller} at {line.split()[1]}")
    setup = "\n".join(fs["SetPerspective__Q24EAGL8ViewPortffff"][1])
    test = "\n".join(fs["TestSphere__CQ24EAGL8ViewPortRC6COORD3f"][1])
    assert "bl C_MTXPerspective" in setup and "bl GXSetProjection" in setup
    for offset in range(0x118, 0x138, 4):
        assert f"0x{offset:x}(r30)" in setup
        assert f"0x{offset:x}(r31)" in test
    for address in (0x8060C81C, 0x8060C828, 0x8060C82C, 0x8060C830,
                    0x805E3FB8, 0x805E3FBC, 0x805E3FC0, 0x805E3FC4):
        print(f"constant {address:#010x}: {read_float(address):.10g}")
    verify_geometry()


if __name__ == "__main__":
    main()
