#!/usr/bin/env python3
"""Print EA's layout of a named type from the disc's retained DWARF1 debug data.

Reads the private export (mitsevox/mvp2005-build, disc-debug/GV4E69), written by
disc_debug_full.py; nothing here needs game files. For each object that defines
the type completely, prints its members with offsets and types, plus the record
offsets to cite in name_sources.tsv. Identical definitions from several objects
are printed once, with every object listed.

    python3 tools/research/dwarf_lookup.py ViewPortPrivate
"""
import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_DIR = Path(__file__).resolve().parents[2] / ".." / "mvp2005-build" / "disc-debug" / "GV4E69"

# DWARF1 fundamental types (FT_*).
FUNDAMENTAL = {
    0x1: "char", 0x2: "signed char", 0x3: "unsigned char", 0x4: "short", 0x5: "signed short",
    0x6: "unsigned short", 0x7: "int", 0x8: "signed int", 0x9: "unsigned int", 0xA: "long",
    0xB: "signed long", 0xC: "unsigned long", 0xD: "void*", 0xE: "float", 0xF: "double",
    0x10: "long double", 0x14: "void", 0x15: "bool", 0x8008: "long long",
    0x8208: "unsigned long long",
}
MODIFIERS = {1: "*", 2: "&", 3: "const", 4: "volatile"}
AT_SIBLING, AT_LOCATION, AT_NAME, AT_FUND, AT_MOD_FUND = 0x10, 0x20, 0x30, 0x50, 0x60
AT_USER, AT_MOD_USER, AT_SUBSCR, AT_BYTE_SIZE, AT_ELEMENTS = 0x70, 0x80, 0xA0, 0xB0, 0xF0
AT_MEMBER = 0x140
AGGREGATES = {0x2: "class", 0x13: "struct", 0x17: "union", 0x4: "enum"}


class Unit:
    def __init__(self, path):
        self.records, self.label = {}, path.name
        for line in path.open():
            row = json.loads(line)
            if row["kind"] == "object":
                self.label = f"{Path(row['source']).name}({row.get('member') or ''})"
            elif row["kind"] == "debug" and "attributes" in row:
                attrs = {}
                for code, value in row["attributes"]:
                    attrs.setdefault(code & ~15, value)
                row["attrs"] = attrs
                self.records[row["offset"]] = row

    def children(self, record):
        """DWARF1 children run from the end of the record to its sibling."""
        end = record["attrs"].get(AT_SIBLING)
        offset, out = record["offset"] + record["length"], []
        while end is not None and offset < end and offset in self.records:
            child = self.records[offset]
            out.append(child)
            offset = child["attrs"].get(AT_SIBLING)
            if offset is None:
                break
        return out

    def members(self, record):
        own = [c for c in self.children(record) if c["tag"] == 0xD]
        if own:
            return own
        # Some records attach members through AT_member instead of nesting.
        return [r for r in self.records.values()
                if r["tag"] == 0xD and r["attrs"].get(AT_MEMBER) == record["offset"]]

    def type_name(self, attrs):
        if AT_FUND in attrs:
            return FUNDAMENTAL.get(attrs[AT_FUND], f"fundamental_0x{attrs[AT_FUND]:X}")
        if AT_USER in attrs:
            return self.user_name(attrs[AT_USER])
        for key, base in ((AT_MOD_FUND, 2), (AT_MOD_USER, 4)):
            if key in attrs:
                raw = bytes.fromhex(attrs[key])
                mods, tail = raw[:-base], raw[-base:]
                value = int.from_bytes(tail, "big")
                name = (FUNDAMENTAL.get(value, f"fundamental_0x{value:X}") if base == 2
                        else self.user_name(value))
                for mod in reversed(mods):
                    word = MODIFIERS.get(mod, f"mod{mod}")
                    name = f"{word} {name}" if word in ("const", "volatile") else name + word
                return name
        return "?"

    def user_name(self, offset):
        record = self.records.get(offset)
        if record is None:
            return f"<0x{offset:X}>"
        if record["tag"] == 0x1:
            return self.array_name(record)
        return record["attrs"].get(AT_NAME) or f"<anonymous 0x{offset:X}>"

    def array_name(self, record):
        raw = bytes.fromhex(record["attrs"].get(AT_SUBSCR, ""))
        dims, pos, element = [], 0, "?"
        while pos < len(raw):
            fmt = raw[pos]
            pos += 1
            if fmt == 0x0:  # FMT_FT_C_C: index type, constant low and high bounds
                low, high = (int.from_bytes(raw[pos + 2 + i:pos + 6 + i], "big") for i in (0, 4))
                dims.append(high - low + 1)
                pos += 10
            elif fmt == 0x8:  # FMT_ET: the element type attribute follows
                code = int.from_bytes(raw[pos:pos + 2], "big")
                pos += 2
                form, value = code & 15, None
                if form == 5:
                    value = int.from_bytes(raw[pos:pos + 2], "big")
                elif form == 2:
                    value = int.from_bytes(raw[pos:pos + 4], "big")
                elif form == 3:
                    size = int.from_bytes(raw[pos:pos + 2], "big")
                    value = raw[pos + 2:pos + 2 + size].hex()
                element = self.type_name({code & ~15: value})
                break
            else:
                return f"<array 0x{record['offset']:X}>"
        return element + "".join(f"[{d}]" for d in dims)

    def enum_values(self, record):
        raw = bytes.fromhex(record["attrs"].get(AT_ELEMENTS, ""))
        values, pos = [], 0
        while pos + 4 < len(raw):
            value = int.from_bytes(raw[pos:pos + 4], "big", signed=True)
            stop = raw.index(0, pos + 4)
            values.append((raw[pos + 4:stop].decode("latin1"), value))
            pos = stop + 1
        return list(reversed(values))


def offset_of(location):
    raw = bytes.fromhex(location or "")
    if len(raw) == 6 and raw[0] == 4 and raw[5] == 7:  # OP_CONST n, OP_ADD
        return int.from_bytes(raw[1:5], "big")
    return None


def render(unit, record):
    attrs, tag = record["attrs"], record["tag"]
    size = attrs.get(AT_BYTE_SIZE)
    head = f"{AGGREGATES.get(tag, 'typedef')} {attrs.get(AT_NAME) or '(unnamed)'}"
    if tag == 0x16:
        lines = [f"typedef {unit.type_name(attrs)} {attrs.get(AT_NAME)};"]
        # A typedef of an unnamed struct or union (COORD3, COORD4): show that aggregate's layout.
        target = unit.records.get(attrs.get(AT_USER))
        if target is not None and target["tag"] in AGGREGATES and AT_NAME not in target["attrs"]:
            lines += render(unit, target)
        return lines
    lines = [head + (f"  // size 0x{size:X}" if size is not None else "  // declaration only")]
    if tag == 0x4:
        lines += [f"    {name} = {value}," for name, value in unit.enum_values(record)]
        return lines
    for member in unit.members(record):
        offset = offset_of(member["attrs"].get(AT_LOCATION))
        where = f"0x{offset:X}" if offset is not None else "?"
        lines.append(f"    {where:>6}  {unit.type_name(member['attrs'])} {member['attrs'].get(AT_NAME)};"
                     f"  // .debug 0x{member['offset']:X}")
    for child in unit.children(record):
        if child["tag"] == 0x7:
            lines.append(f"    static  {unit.type_name(child['attrs'])} {child['attrs'].get(AT_NAME)};"
                         f"  // .debug 0x{child['offset']:X}")
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("name", nargs="+", help="type names (struct, class, union, enum or typedef)")
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR, help="private disc-debug export")
    args = parser.parse_args()
    files = sorted(args.dir.glob("object-*.jsonl"))
    if not files:
        sys.exit(f"no export in {args.dir}; clone mitsevox/mvp2005-build beside this repo")
    units = [Unit(path) for path in files]
    for name in args.name:
        seen = {}
        for unit in units:
            for record in unit.records.values():
                if record["attrs"].get(AT_NAME) != name or record["tag"] not in (*AGGREGATES, 0x16):
                    continue
                if record["tag"] != 0x16 and AT_BYTE_SIZE not in record["attrs"]:
                    continue  # incomplete declarations prove nothing about layout
                text = "\n".join(render(unit, record))
                # Record offsets differ per object; group identical layouts, cite the first.
                key = re.sub(r"  // \.debug 0x[0-9A-F]+|<anonymous 0x[0-9A-F]+>", "", text)
                seen.setdefault(key, (text, []))[1].append(f"{unit.label} .debug 0x{record['offset']:X}")
        if not seen:
            print(f"{name}: no complete definition in the export\n")
        for text, where in seen.values():
            print(text)
            print(f"  // defined in {len(where)} object(s), first {where[0]}\n")


if __name__ == "__main__":
    main()
