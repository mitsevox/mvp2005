#!/usr/bin/env python3
"""Losslessly catalogue retained ELF debug metadata on an extracted disc.

No code, assets, source/header contents, or complete object files are exported.
Only ELF section descriptors, symbols, debug records/auxiliary metadata, and
relocations targeting debug sections are written. Unsupported debug encodings
remain explicit hexadecimal values. All exported sections are reconstructed
and checked against their original bytes before writing.
"""
import argparse
import collections
import hashlib
import json
import struct
from pathlib import Path

DEBUG_NAMES = {".line", ".stab", ".stabstr"}
TAGS = {
    1: "array_type", 2: "class_type", 3: "entry_point", 4: "enumeration_type",
    5: "formal_parameter", 6: "global_subroutine", 7: "global_variable",
    8: "imported_declaration", 10: "label", 11: "lexical_block",
    12: "local_variable", 13: "member", 15: "pointer_type",
    16: "reference_type", 17: "compile_unit", 18: "string_type",
    19: "structure_type", 20: "subroutine", 21: "subroutine_type",
    22: "typedef", 23: "union_type", 24: "unspecified_parameters",
    25: "variant", 26: "common_block", 27: "common_inclusion",
    28: "inheritance", 29: "inlined_subroutine", 30: "module",
    31: "ptr_to_member_type", 32: "set_type", 33: "subrange_type",
    34: "with_stmt",
}
ATTRS = {
    0x10: "sibling", 0x20: "location", 0x30: "name",
    0x50: "fund_type", 0x60: "mod_fund_type", 0x70: "user_def_type",
    0x80: "mod_u_d_type", 0x90: "ordering", 0xA0: "subscr_data",
    0xB0: "byte_size", 0xC0: "bit_offset", 0xD0: "bit_size",
    0xF0: "element_list", 0x100: "stmt_list", 0x110: "low_pc",
    0x120: "high_pc", 0x130: "language", 0x140: "member",
    0x150: "discr", 0x160: "discr_value", 0x170: "string_length",
    0x180: "common_reference", 0x190: "comp_dir", 0x1A0: "const_value",
    0x1B0: "containing_type", 0x1C0: "default_value",
    0x1E0: "friend", 0x200: "inline", 0x210: "is_optional",
    0x220: "lower_bound", 0x230: "program", 0x250: "prototyped",
    0x270: "return_addr", 0x280: "start_scope", 0x2A0: "stride_size",
    0x2C0: "upper_bound",
}
FIXED = {1: 4, 2: 4, 5: 2, 6: 4, 7: 8}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_slice(data, start, size):
    if start < 0 or size < 0 or start + size > len(data):
        raise ValueError(f"out of bounds slice {start:#x}+{size:#x}")
    return data[start:start + size]


def cstring(data, offset):
    end = data.index(0, offset)
    return data[offset:end].decode("latin1")


def members(raw):
    if not raw.startswith(b"!<arch>\n"):
        raise ValueError("not an ar archive")
    pos, names = 8, b""
    while pos < len(raw):
        head = checked_slice(raw, pos, 60)
        if head[58:] != b"`\n":
            raise ValueError(f"invalid archive header at {pos:#x}")
        size = int(head[48:58])
        label = head[:16].decode("ascii").strip()
        body = checked_slice(raw, pos + 60, size)
        if label == "//":
            names = body
        elif label not in ("/", "/SYM64/", "__.SYMDEF", "__.SYMDEF SORTED"):
            if label.startswith("#1/"):
                n = int(label[3:])
                name, body = body[:n].rstrip(b"\0").decode("latin1"), body[n:]
            elif label.startswith("/"):
                name = names[int(label[1:]):].split(b"/\n", 1)[0].decode("latin1")
            else:
                name = label.rstrip("/")
            yield name, body
        pos += 60 + size + size % 2
    if pos != len(raw):
        raise ValueError("archive alignment exceeds file")


def elf_sections(raw):
    if raw[:5] != b"\x7fELF\x01" or raw[5] not in (1, 2):
        raise ValueError("expected ELF32")
    endian = "<" if raw[5] == 1 else ">"
    fields = struct.unpack_from(endian + "HHIIIIIHHHHHH", raw, 16)
    etype, machine, version, entry, phoff, shoff, flags, ehsize, phsize, phnum, shsize, shnum, shstr = fields
    if shsize != 40 or shnum == 0:
        raise ValueError("unsupported ELF section header layout")
    headers = [struct.unpack(endian + "10I", checked_slice(raw, shoff + i * shsize, 40)) for i in range(shnum)]
    names = checked_slice(raw, headers[shstr][4], headers[shstr][5])
    sections = []
    for i, h in enumerate(headers):
        section = dict(zip(("name_offset", "type", "flags", "address", "file_offset", "size", "link", "info", "alignment", "entry_size"), h))
        section.update(index=i, name=cstring(names, h[0]))
        if h[1] != 8:
            section["sha256"] = digest(checked_slice(raw, h[4], h[5]))
        sections.append(section)
    return {"class": 32, "byte_order": "little" if endian == "<" else "big", "type": etype, "machine": machine,
            "entry": entry, "flags": flags}, sections


def is_debug(name):
    return name.startswith((".debug", ".zdebug")) or name in DEBUG_NAMES


def dwarf_records(data, byte_order="big"):
    """DWARF1 forms decoded structurally; block expression semantics stay raw.

    Attributes stay ordered (including duplicates). Integer/string/block values
    re-encode exactly; each attribute's code includes its original form nibble.
    An unrecognised form preserves the unparsed remainder of that record.
    """
    pos = 0
    while pos < len(data):
        length = int.from_bytes(checked_slice(data, pos, 4), byte_order)
        if length < 4:
            raise ValueError(f"invalid DWARF record length at {pos:#x}")
        record = checked_slice(data, pos, length)
        row = {"kind": "debug", "offset": pos, "length": length}
        if length < 6 or int.from_bytes(record[4:6], byte_order) == 0:
            row["padding_hex"] = record[4:].hex()
        else:
            tag = int.from_bytes(record[4:6], byte_order)
            row.update(tag=tag, tag_name=TAGS.get(tag, "unknown"), attributes=[])
            q = 6
            while q < length:
                start = q
                code = int.from_bytes(checked_slice(record, q, 2), byte_order)
                q += 2
                form = code & 15
                if form in FIXED:
                    size = FIXED[form]
                    value = int.from_bytes(checked_slice(record, q, size), byte_order)
                    q += size
                elif form in (3, 4):
                    prefix = 2 if form == 3 else 4
                    size = int.from_bytes(checked_slice(record, q, prefix), byte_order)
                    q += prefix
                    value = checked_slice(record, q, size).hex()
                    q += size
                elif form == 8:
                    end = record.index(0, q)
                    value = record[q:end].decode("latin1")
                    q = end + 1
                else:
                    row["unparsed_tail_hex"] = record[start:].hex()
                    break
                row["attributes"].append([code, value])
                if code & ~15 == 0x30:
                    row["name"] = value
        yield row
        pos += length


def encode_record(row, byte_order="big"):
    data = row["length"].to_bytes(4, byte_order)
    if "padding_hex" in row:
        return data + bytes.fromhex(row["padding_hex"])
    data += row["tag"].to_bytes(2, byte_order)
    for code, value in row["attributes"]:
        form = code & 15
        data += code.to_bytes(2, byte_order)
        if form in FIXED:
            data += value.to_bytes(FIXED[form], byte_order)
        elif form in (3, 4):
            block = bytes.fromhex(value)
            data += len(block).to_bytes(2 if form == 3 else 4, byte_order) + block
        elif form == 8:
            data += value.encode("latin1") + b"\0"
    data += bytes.fromhex(row.get("unparsed_tail_hex", ""))
    if len(data) != row["length"]:
        raise ValueError("record re-encoding length mismatch")
    return data


def export_elf(raw, provenance, output):
    header, sections = elf_sections(raw)
    endian = "<" if header["byte_order"] == "little" else ">"
    result = dict(provenance, elf=header, sections=sections, debug_sections=[],
                  symbol_count=0, debug_relocation_count=0, record_count=0,
                  tags={}, unknown_attributes={}, unparsed_records=0)
    rows = [{"kind": "object", **provenance, "elf": header, "sections": sections}]
    symtabs = {}
    for section in sections:
        if section["type"] not in (2, 11):
            continue
        data = checked_slice(raw, section["file_offset"], section["size"])
        strings = sections[section["link"]]
        names = checked_slice(raw, strings["file_offset"], strings["size"])
        if section["entry_size"] != 16 or len(data) % 16:
            raise ValueError("invalid symbol table")
        symbols, rebuilt = [], bytearray()
        for offset in range(0, len(data), 16):
            nameoff, value, size, info, other, shndx = struct.unpack_from(endian + "IIIBBH", data, offset)
            row = dict(kind="symbol", table=section["index"], index=offset // 16,
                       name_offset=nameoff, name=cstring(names, nameoff), value=value,
                       size=size, info=info, other=other, section_index=shndx)
            if shndx < len(sections):
                row["section_name"] = sections[shndx]["name"]
            symbols.append(row)
            rebuilt.extend(struct.pack(endian + "IIIBBH", nameoff, value, size, info, other, shndx))
        if bytes(rebuilt) != data:
            raise ValueError("symbol roundtrip failed")
        symtabs[section["index"]] = symbols
        rows.extend(symbols)
        result["symbol_count"] += len(symbols)
    tagcounts, unknown = collections.Counter(), collections.Counter()
    for section in sections:
        if not is_debug(section["name"]):
            continue
        if section["flags"] & 2:
            raise ValueError("refusing allocated debug section")
        data = checked_slice(raw, section["file_offset"], section["size"])
        summary = dict(index=section["index"], name=section["name"], size=len(data), sha256=digest(data))
        if section["name"] == ".debug":
            records = list(dwarf_records(data, header["byte_order"]))
            rebuilt = b"".join(encode_record(row, header["byte_order"]) for row in records)
            if rebuilt != data:
                raise ValueError("DWARF record roundtrip failed")
            summary.update(encoding="dwarf1_records", record_count=len(records))
            rows.append({"kind": "debug_section", **summary})
            for row in records:
                row["section"] = section["index"]
                tagcounts[f"0x{row.get('tag', 0):x}"] += 1
                for code, _ in row.get("attributes", []):
                    if code & ~15 not in ATTRS:
                        unknown[f"0x{code & ~15:x}"] += 1
                result["unparsed_records"] += "unparsed_tail_hex" in row
            rows.extend(records)
            result["record_count"] += len(records)
        else:
            summary["encoding"] = "uninterpreted_metadata_hex"
            payload = data.hex()
            if bytes.fromhex(payload) != data:
                raise ValueError("auxiliary section roundtrip failed")
            rows.append({"kind": "debug_section", **summary, "payload_hex": payload})
        result["debug_sections"].append(summary)
    for section in sections:
        if section["type"] not in (4, 9) or not is_debug(sections[section["info"]]["name"]):
            continue
        data = checked_slice(raw, section["file_offset"], section["size"])
        rela = section["type"] == 4
        size = 12 if rela else 8
        if section["entry_size"] != size or len(data) % size:
            raise ValueError("invalid relocation table")
        symbols, rebuilt = symtabs[section["link"]], bytearray()
        for pos in range(0, len(data), size):
            offset, info = struct.unpack_from(endian + "II", data, pos)
            index = info >> 8
            if index >= len(symbols):
                raise ValueError("relocation symbol index out of bounds")
            fields = [section["index"], pos // size, section["info"], offset,
                      info & 255, section["link"], index]
            if rela:
                addend = struct.unpack_from(endian + "i", data, pos + 8)[0]
                fields.append(addend)
                rebuilt.extend(struct.pack(endian + "IIi", offset, info, addend))
            else:
                rebuilt.extend(struct.pack(endian + "II", offset, info))
            rows.append({"kind": "debug_relocation", "fields": fields})
        if bytes(rebuilt) != data:
            raise ValueError("relocation roundtrip failed")
        result["debug_relocation_count"] += len(data) // size
    result.update(tags=dict(sorted(tagcounts.items())), unknown_attributes=dict(sorted(unknown.items())))
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w") as stream:
            for row in rows:
                stream.write(json.dumps(row, separators=(",", ":"), ensure_ascii=True) + "\n")
        result.update(output=output.name, output_sha256=digest(output.read_bytes()))
    return result


def inventory(root):
    """Scan every loose file and every standard BIG directory entry by magic."""
    sources, skipped_big, entries = [], [], 0
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        with path.open("rb") as stream:
            magic = stream.read(8)
            if magic.startswith(b"\x7fELF") or magic == b"!<arch>\n":
                sources.append((rel, path.read_bytes()))
            elif magic[:4] in (b"BIGF", b"BIG4"):
                stream.seek(8)
                count, end = struct.unpack(">II", stream.read(8))
                if end > path.stat().st_size:
                    raise ValueError(f"BIG directory out of bounds: {rel}")
                directory = []
                for _ in range(count):
                    offset, size = struct.unpack(">II", stream.read(8))
                    name = bytearray()
                    while True:
                        byte = stream.read(1)
                        if not byte or stream.tell() > end:
                            raise ValueError(f"BIG name exceeds directory: {rel}")
                        if byte == b"\0":
                            break
                        name.extend(byte)
                    directory.append((offset, size, name.decode("latin1")))
                for offset, size, name in directory:
                    if offset + size > path.stat().st_size:
                        raise ValueError(f"BIG entry out of bounds: {rel}({name})")
                    stream.seek(offset)
                    signature = stream.read(min(size, 8))
                    if signature.startswith(b"\x7fELF") or signature == b"!<arch>\n":
                        stream.seek(offset)
                        sources.append((f"{rel}({name})", stream.read(size)))
                entries += count
            elif path.suffix.lower() == ".big":
                skipped_big.append(rel)
    return sources, entries, skipped_big


def verify_catalogue(directory):
    """Reconstruct exported metadata sections from saved JSON, without the disc."""
    manifest = json.loads((directory / "manifest.json").read_text())
    checked = 0
    for obj in manifest["objects"]:
        path = directory / obj["output"]
        if digest(path.read_bytes()) != obj["output_sha256"]:
            raise ValueError(f"output hash mismatch: {path}")
        rows = [json.loads(line) for line in path.open()]
        head = rows[0]
        if head["kind"] != "object" or head["sections"] != obj["sections"]:
            raise ValueError("object metadata mismatch")
        endian = "<" if head["elf"]["byte_order"] == "little" else ">"
        rebuilt = collections.defaultdict(bytearray)
        for row in rows[1:]:
            kind = row["kind"]
            if kind == "debug_section":
                section = head["sections"][row["index"]]
                if not is_debug(section["name"]) or section["flags"] & 2:
                    raise ValueError("non-debug section payload")
                if row["encoding"] == "uninterpreted_metadata_hex":
                    rebuilt[row["index"]].extend(bytes.fromhex(row["payload_hex"]))
                else:
                    rebuilt[row["index"]]  # also track empty sections
            elif kind == "debug":
                if len(rebuilt[row["section"]]) != row["offset"]:
                    raise ValueError("debug record offset mismatch")
                rebuilt[row["section"]].extend(encode_record(row, head["elf"]["byte_order"]))
            elif kind == "symbol":
                if len(rebuilt[row["table"]]) != row["index"] * 16:
                    raise ValueError("symbol index mismatch")
                rebuilt[row["table"]].extend(struct.pack(endian + "IIIBBH",
                    row["name_offset"], row["value"], row["size"], row["info"],
                    row["other"], row["section_index"]))
            elif kind == "debug_relocation":
                sec, index, target, offset, typ, table, symbol, *addend = row["fields"]
                section = head["sections"][sec]
                if not is_debug(head["sections"][target]["name"]):
                    raise ValueError("non-debug relocation exported")
                if len(rebuilt[sec]) != index * section["entry_size"]:
                    raise ValueError("relocation index mismatch")
                rebuilt[sec].extend(struct.pack(endian + "II", offset, symbol << 8 | typ))
                if addend:
                    rebuilt[sec].extend(struct.pack(endian + "i", addend[0]))
            else:
                raise ValueError(f"unsupported output row kind: {kind}")
        for index, payload in rebuilt.items():
            section = head["sections"][index]
            if len(payload) != section["size"] or digest(payload) != section["sha256"]:
                raise ValueError(f"saved metadata roundtrip failed: {path} {section['name']}")
            checked += 1
    print(f"Verified {len(manifest['objects'])} JSONL objects; {checked} metadata sections reconstructed exactly.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("disc", nargs="?", type=Path, help="extracted disc directory (contains files/ and sys/)")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path, help="verify a saved catalogue without game files")
    args = parser.parse_args()
    if args.verify:
        verify_catalogue(args.verify)
        return
    if args.disc is None or args.output is None:
        parser.error("disc and --output are required when exporting")
    args.output.mkdir(parents=True, exist_ok=True)
    sources, big_entries, skipped_big = inventory(args.disc)
    manifest = {"format": "mvp2005-disc-debug-v1", "game_id": "GV4E69",
                "relocation_fields": ["section", "index", "target_section", "offset",
                                      "type", "symbol_table", "symbol_index", "addend_if_RELA"],
                "attribute_names": {f"0x{k:x}": v for k, v in sorted(ATTRS.items())},
                "tag_names": {f"0x{k:x}": v for k, v in sorted(TAGS.items())},
                "scan": {"loose_files": sum(p.is_file() for p in args.disc.rglob("*")),
                         "standard_big_entries": big_entries, "unindexed_big_files": skipped_big},
                "sources": [], "objects": [], "unparsed_candidates": []}
    for source, raw in sources:
        archive = raw.startswith(b"!<arch>\n")
        provenance = {"source": source, "source_sha1": hashlib.sha1(raw).hexdigest(),
                      "source_sha256": digest(raw)}
        items = list(members(raw)) if archive else [(None, raw)]
        sourceinfo = {**provenance, "kind": "ar" if archive else "ELF", "member_count": len(items)}
        manifest["sources"].append(sourceinfo)
        for index, (name, obj) in enumerate(items):
            if not obj.startswith(b"\x7fELF"):
                raise ValueError(f"non-ELF archive member: {source}({name})")
            try:
                _, sections = elf_sections(obj)
            except ValueError as error:
                manifest["unparsed_candidates"].append({**provenance, "member": name,
                    "size": len(obj), "reason": str(error)})
                continue
            has_debug = any(is_debug(s["name"]) for s in sections)
            identity = {**provenance, "member": name, "member_index": index,
                        "object_sha1": hashlib.sha1(obj).hexdigest(), "object_sha256": digest(obj)}
            # Symbol-only objects are also exported, supporting the disc-wide audit.
            filename = f"object-{len(manifest['objects']):03d}.jsonl"
            result = export_elf(obj, identity, args.output / filename)
            result["has_debug"] = has_debug
            manifest["objects"].append(result)
    manifest["totals"] = {key: sum(o[key] for o in manifest["objects"])
                          for key in ("record_count", "symbol_count", "debug_relocation_count", "unparsed_records")}
    manifest["totals"].update(objects=len(manifest["objects"]),
                              debug_objects=sum(o["has_debug"] for o in manifest["objects"]),
                              debug_sections=sum(len(o["debug_sections"]) for o in manifest["objects"]))
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest["totals"], sort_keys=True))
    print(f"Audited {manifest['scan']['loose_files']} loose files and {big_entries} standard BIG entries; "
          f"{len(skipped_big)} nonstandard BIG files remain unindexed.")


if __name__ == "__main__":
    main()
