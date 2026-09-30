#!/usr/bin/env python3
"""Export selected EA viewport type evidence from the owner's disc archive.

Reads libmatd.a directly; writes names/layout metadata only, never object code,
debug-section dumps or SDK declarations. Debug offsets are relative to the
selected member's .debug section. They are not addresses in main.dol.
"""
import argparse
import csv
import hashlib
import struct
from pathlib import Path

DEFAULT_TYPES = (
    "ViewPort", "ViewPortExtension", "ViewPortPrivate", "VPGeometry",
    "VPFrustum", "VPClipData", "VPCullData", "ProjectionType", "Transform",
)


def archive_member(raw, wanted):
    if raw[:8] != b"!<arch>\n":
        raise ValueError("expected ar archive")
    pos, names = 8, b""
    while pos < len(raw):
        header = raw[pos:pos + 60]
        if len(header) != 60 or header[58:] != b"`\n":
            raise ValueError(f"invalid archive header at {pos:#x}")
        size = int(header[48:58])
        label = header[:16].decode("ascii").strip()
        payload = raw[pos + 60:pos + 60 + size]
        if len(payload) != size:
            raise ValueError("truncated archive member")
        if label == "//":
            names = payload
        elif label.startswith("#1/"):
            length = int(label[3:])
            name = payload[:length].rstrip(b"\0").decode("ascii")
            payload = payload[length:]
            if name == wanted:
                return payload
        elif label not in ("/", "/SYM64/"):
            if label.startswith("/"):
                name = names[int(label[1:]):].split(b"/\n", 1)[0].decode("ascii")
            else:
                name = label.rstrip("/")
            if name == wanted:
                return payload
        pos += 60 + size + size % 2
    raise ValueError(f"archive has no member {wanted}")


def debug_section(raw):
    if raw[:6] != b"\x7fELF\x01\x02":
        raise ValueError("expected big-endian ELF32 object")
    shoff = struct.unpack_from(">I", raw, 32)[0]
    shsize, shnum, shstr = struct.unpack_from(">HHH", raw, 46)
    sections = [struct.unpack_from(">10I", raw, shoff + i * shsize) for i in range(shnum)]
    table = sections[shstr]
    names = raw[table[4]:table[4] + table[5]]
    for section in sections:
        if names[section[0]:].split(b"\0", 1)[0] == b".debug":
            return raw[section[4]:section[4] + section[5]]
    raise ValueError("object has no .debug section")


def entries(data):
    """SN GCC's old-style DWARF attributes: form in the low four bits."""
    result, pos = [], 0
    while pos < len(data):
        length = struct.unpack_from(">I", data, pos)[0]
        if length < 4 or pos + length > len(data):
            raise ValueError(f"invalid debug entry length at {pos:#x}")
        if length < 6:
            pos += length
            continue
        tag = struct.unpack_from(">H", data, pos + 4)[0]
        q, end, attrs = pos + 6, pos + length, {}
        while q < end:
            attr = struct.unpack_from(">H", data, q)[0]
            q += 2
            form = attr & 15
            if form in (1, 2, 5, 6, 7):
                size = {1: 4, 2: 4, 5: 2, 6: 4, 7: 8}[form]
                value = int.from_bytes(data[q:q + size], "big")
                q += size
            elif form in (3, 4):
                prefix = 2 if form == 3 else 4
                size = int.from_bytes(data[q:q + prefix], "big")
                q += prefix
                value = data[q:q + size]
                q += size
            elif form == 8:
                stop = data.index(0, q, end)
                value = data[q:stop].decode("latin1")
                q = stop + 1
            else:
                raise ValueError(f"unsupported form {form} at {pos:#x}")
            if q > end:
                raise ValueError(f"attribute exceeds entry at {pos:#x}")
            attrs[attr & ~15] = value
        result.append((pos, tag, attrs))
        pos = end
    return result


def member_offset(location):
    # Constant u32 followed by ADD: the debug member-location expression.
    if isinstance(location, bytes) and len(location) == 6 and location[0] == 4 and location[-1] == 7:
        return f"0x{int.from_bytes(location[1:5], 'big'):X}"
    raise ValueError("unsupported member location; do not guess an offset")


def type_reference(attrs, by_offset):
    for key, label in ((0x70, "user"), (0x50, "fundamental"),
                       (0x80, "modified_user"), (0x60, "modified_fundamental")):
        if key not in attrs:
            continue
        value = attrs[key]
        if isinstance(value, bytes):
            return label + ":" + value.hex()
        name = by_offset.get(value, {}).get(0x30, "") if key == 0x70 else ""
        return f"{label}:0x{value:X}" + (f":{name}" if name else "")
    return ""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--member", default="InstanceCrowd.o")
    parser.add_argument("--types", nargs="+", default=DEFAULT_TYPES)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raw = args.archive.read_bytes()
    obj = archive_member(raw, args.member)
    records = entries(debug_section(obj))
    by_offset = {offset: attrs for offset, _, attrs in records}
    rows, found = [], set()
    prefix = [args.archive.name, hashlib.sha1(raw).hexdigest(), args.member,
              hashlib.sha1(obj).hexdigest()]
    for offset, tag, attrs in records:
        name = attrs.get(0x30)
        if name not in args.types or tag not in (2, 4, 0x13, 0x16):
            continue
        if tag in (2, 4, 0x13) and 0xB0 not in attrs:
            continue  # incomplete declarations do not establish layouts
        found.add(name)
        size = f"0x{attrs[0xB0]:X}" if 0xB0 in attrs else ""
        rows.append(prefix + [f"0x{offset:X}", f"0x{tag:X}", "type", name, "", size, "", type_reference(attrs, by_offset)])
        for child_offset, child_tag, child in records:
            if child_tag == 0xD and child.get(0x140) == offset:
                rows.append(prefix + [f"0x{child_offset:X}", f"0x{child_tag:X}", "member",
                    child[0x30], name, "", member_offset(child.get(0x20)), type_reference(child, by_offset)])
    missing = set(args.types) - found
    if missing:
        raise ValueError("no complete selected types: " + ", ".join(sorted(missing)))
    with args.output.open("w", newline="") as out:
        writer = csv.writer(out, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_ALL)
        writer.writerow(("archive", "archive_sha1", "member", "member_sha1", "debug_offset",
                         "debug_tag", "kind", "name", "owner", "byte_size", "member_offset", "type_reference"))
        writer.writerows(rows)
    print(f"Parsed {len(records)} debug entries; exported {len(found)} types and {len(rows) - len(found)} members to {args.output}")


if __name__ == "__main__":
    main()
