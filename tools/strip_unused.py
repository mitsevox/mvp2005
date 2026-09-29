#!/usr/bin/env python3
"""Remove the symbols from a compiled library object that the game's linker dead-stripped.

The game was linked with SN Systems' ngcld, which links whole library archives and then
dead-strips them at symbol granularity, keeping the remaining symbols in their original order:
  * functions (static or global) nobody references are dropped from .text entirely;
  * global data objects nobody references are removed in 8-byte units (the last size % 8 bytes
    stay, unnamed, and lose their relocations);
  * local data is kept whole when anything references it, or when its section is addressed through
    a -O4,p pool symbol (...data.0 / ...bss.0); local data nobody references is stripped like
    global data. An archive member whose every function was stripped still leaves its kept
    locals in the DOL.
So the DOL holds a subset of each library object. This tool reproduces that: it keeps the symbols
that config/<ver>/symbols.txt names inside the unit's ranges in config/<ver>/splits.txt, and
deletes every other function and global, fixing up section contents, relocations, symbols and
the Metrowerks .comment section. Local data follows the rules above.

Adapted from emoose/re4 tools/strip_unused.py (CC0-1.0), which found these rules; that version
reads its keep list from a symbol map the RE4 debug build shipped. MVP has no such map, so the
keep list is our own symbols.txt.

usage: strip_unused.py --unit dolphin/os/OS.c build/GV4E69/src/dolphin/os/OS.o
       strip_unused.py --gcc --unit <unit> <object>   (ProDG objects)
"""
import argparse
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VER = os.environ.get("MVP_VERSION", "GV4E69")

SHT_SYMTAB = 2
SHT_RELA = 4
SHT_NOBITS = 8
STT_OBJECT = 1
STT_FUNC = 2
STT_SECTION = 3
STB_LOCAL = 0
DATA_GRANULE = 8  # the linker strips global data in 8-byte units (the remainder stays)


def unit_ranges(unit):
    """{section: [(start, end)]} of the unit in splits.txt, or None if the unit is not split."""
    ranges = None
    cur = None
    with open(os.path.join(ROOT, "config", VER, "splits.txt")) as f:
        for line in f:
            m = re.match(r"^(\S+):\s*$", line)
            if m:
                cur = m.group(1)
                continue
            m = re.match(r"^\s+(\.\w+)\s+start:0x([0-9A-Fa-f]+) end:0x([0-9A-Fa-f]+)", line)
            if m and cur == unit:
                ranges = ranges or {}
                ranges.setdefault(m.group(1), []).append((int(m.group(2), 16), int(m.group(3), 16)))
    return ranges


def target_symbols(unit):
    """{section: set(names)} of the symbols symbols.txt names inside the unit's split ranges.
    Placeholder names (fn_/lbl_/...) are not kept: a symbol the DOL keeps must carry its real name."""
    ranges = unit_ranges(unit)
    if ranges is None:
        return None
    names = {sec: set() for sec in ranges}
    with open(os.path.join(ROOT, "config", VER, "symbols.txt")) as f:
        for line in f:
            m = re.match(r"^(\S+) = (\.\w+):0x([0-9A-Fa-f]+);", line)
            if not m:
                continue
            name, sec, addr = m.group(1), m.group(2), int(m.group(3), 16)
            if re.match(r"^(fn|lbl|jumptable|gap)_", name):
                continue
            if any(start <= addr < end for start, end in ranges.get(sec, ())):
                names[sec].add(name)
    return names


class Elf:
    def __init__(self, data):
        self.data = bytearray(data)
        (self.shoff,) = struct.unpack(">I", data[0x20:0x24])
        (self.shentsize, self.shnum, self.shstrndx) = struct.unpack(">HHH", data[0x2E:0x34])
        self.sections = []
        for i in range(self.shnum):
            off = self.shoff + i * self.shentsize
            self.sections.append(list(struct.unpack(">IIIIIIIIII", data[off : off + 40])))
        shstr = self.sec_bytes(self.shstrndx)
        self.names = []
        for sh in self.sections:
            end = shstr.index(b"\0", sh[0])
            self.names.append(shstr[sh[0] : end].decode())
        self.contents = [bytearray(self.sec_bytes(i)) for i in range(self.shnum)]

    def sec_bytes(self, i):
        sh = self.sections[i]
        if sh[1] == SHT_NOBITS:
            return b"\0" * sh[5]
        return self.data[sh[4] : sh[4] + sh[5]]

    def index(self, name):
        return self.names.index(name)

    def write(self, path):
        out = bytearray(self.data[:0x34])
        pos = 0x34
        for i in range(1, self.shnum):
            sh = self.sections[i]
            body = self.contents[i]
            align = max(sh[8], 1)
            pos = (pos + align - 1) // align * align
            sh[4] = pos
            sh[5] = len(body)
            if sh[1] != SHT_NOBITS:
                out += b"\0" * (pos - len(out))
                out += body
                pos += len(body)
        pos = (pos + 3) // 4 * 4
        out += b"\0" * (pos - len(out))
        struct.pack_into(">I", out, 0x20, pos)
        for sh in self.sections:
            out += struct.pack(">IIIIIIIIII", *sh)
        with open(path, "wb") as f:
            f.write(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", required=True)
    ap.add_argument(
        "--gcc",
        action="store_true",
        help="ProDG (gcc 2.95) object: .lcomm statics are untyped symbols, data only referenced from "
        "stripped functions is stripped too, and surviving pointers to stripped functions become 0",
    )
    ap.add_argument("object")
    args = ap.parse_args()

    keep = target_symbols(args.unit)
    if keep is None:
        sys.exit(f"strip_unused: unit {args.unit} not in splits.txt")

    elf = Elf(open(args.object, "rb").read())
    symtab = elf.index(".symtab")
    strtab = elf.sections[symtab][6]
    syms = [
        list(struct.unpack(">IIIBBH", elf.contents[symtab][o : o + 16]))
        for o in range(0, len(elf.contents[symtab]), 16)
    ]
    strs = elf.contents[strtab]

    def sym_name(s):
        end = strs.index(b"\0", s[0])
        return strs[s[0] : end].decode()

    # Reference counts per symbol and "pooled" sections: with -O4,p MWCC addresses local data through
    # a per-section pool symbol (...data.0 / ...bss.0, NOTYPE at offset 0), so the linker could not
    # attribute those references to individual local objects and kept every local in such a section.
    # Local data with no reference at all (e.g. axartlfo's unused wave tables) was stripped.
    # References from functions that are themselves stripped do not count (gcc's libgcc statics
    # that only the dropped exception runtime used are gone from the DOL).
    dead_funcs = {}
    for s in syms:
        shndx, stype = s[5], s[3] & 0xF
        if shndx == 0 or shndx >= elf.shnum or stype != STT_FUNC:
            continue
        nm = sym_name(s)
        ks = keep.get(elf.names[shndx], ())
        if nm not in ks:
            dead_funcs.setdefault(shndx, []).append((s[1], s[1] + s[2]))

    def in_dead_func(shndx, off):
        return args.gcc and any(start <= off < end for start, end in dead_funcs.get(shndx, ()))

    refcount = [0] * len(syms)
    pooled_sections = set()
    for i, sh in enumerate(elf.sections):
        if sh[1] != SHT_RELA:
            continue
        for o in range(0, len(elf.contents[i]), 12):
            r_off, r_info = struct.unpack(">II", elf.contents[i][o : o + 8])
            sym = r_info >> 8
            if in_dead_func(sh[7], r_off):
                continue
            refcount[sym] += 1
            s = syms[sym]
            if (s[3] & 0xF) in (STT_SECTION, 0) and s[5] != 0:
                pooled_sections.add(s[5])

    # Byte ranges to delete, per section: {shndx: [(start, end), ...]}; symbols to drop; original
    # extents of dropped symbols (relocations inside them are dropped too, e.g. a stripped pointer
    # variable's initializer ends up as zero in the DOL).
    removed = {}
    dead = {}
    removed_idx = set()
    for i, s in enumerate(syms):
        shndx, stype, bind = s[5], s[3] & 0xF, s[3] >> 4
        if shndx == 0 or shndx >= elf.shnum:
            continue
        if args.gcc and stype == 0 and s[2] and not (elf.sections[shndx][2] & 0x4):
            stype = STT_OBJECT  # gcc .lcomm statics are untyped
        if stype not in (STT_FUNC, STT_OBJECT):
            continue
        secname = elf.names[shndx]
        name = sym_name(s)
        if name in keep.get(secname, ()):
            continue
        if stype == STT_FUNC:
            removed.setdefault(shndx, []).append((s[1], s[1] + s[2]))
        elif bind != STB_LOCAL or (refcount[i] == 0 and shndx not in pooled_sections):
            # unreferenced data: the linker removed it in 8-byte units, leaving the last
            # size % 8 bytes (unnamed, relocations dropped). Exception (seen in RE4): an
            # unreferenced *global* in a gcc object is dropped whole, while function-local statics
            # of a dead function keep their remainder.
            cut = s[2] if (args.gcc and bind != STB_LOCAL) else s[2] - s[2] % DATA_GRANULE
            if cut:
                removed.setdefault(shndx, []).append((s[1], s[1] + cut))
        else:
            continue
        dead.setdefault(shndx, []).append((s[1], s[1] + s[2]))
        removed_idx.add(i)
    if not removed_idx:
        return
    for r in removed.values():
        r.sort()

    def in_dead(shndx, off):
        return any(start <= off < end for start, end in dead.get(shndx, ()))

    def shift(shndx, off):
        """New offset for an old offset in a section (must not be inside a removed range)."""
        d = 0
        for start, end in removed.get(shndx, ()):
            if start <= off < end:
                raise ValueError(f"offset {off:#x} in {elf.names[shndx]} lies inside a removed range")
            if end <= off:
                d += end - start
        return off - d

    # Section contents
    for shndx, ranges in removed.items():
        old = elf.contents[shndx]
        new = bytearray()
        pos = 0
        for start, end in ranges:
            new += old[pos:start]
            pos = end
        new += old[pos:]
        elf.contents[shndx] = new

    # Symbols: drop removed, shift values, renumber.
    remap = {}
    new_syms = []
    for i, s in enumerate(syms):
        if i in removed_idx:
            continue
        if i != 0 and s[5] in removed and (s[3] & 0xF) != STT_SECTION:
            try:
                s[1] = shift(s[5], s[1])
            except ValueError as e:
                if (s[3] & 0xF) in (STT_FUNC, STT_OBJECT):
                    sys.exit(f"strip_unused: symbol {sym_name(s)}: {e}")
                # untyped label (gcc2_compiled., .LC*) inside a stripped function: keep it at
                # the point where the removed range collapsed to
                d = 0
                for start, end in removed[s[5]]:
                    if end <= s[1]:
                        d += end - start
                    elif start <= s[1]:
                        d += s[1] - start
                s[1] -= d
        remap[i] = len(new_syms)
        new_syms.append(s)
    elf.contents[symtab] = bytearray().join(struct.pack(">IIIBBH", *s) for s in new_syms)
    first_global = next((k for k, s in enumerate(new_syms) if (s[3] >> 4) != 0), len(new_syms))
    elf.sections[symtab][7] = first_global

    # Relocations
    for i, sh in enumerate(elf.sections):
        if sh[1] != SHT_RELA:
            continue
        target = sh[7]
        out = bytearray()
        for o in range(0, len(elf.contents[i]), 12):
            r_off, r_info, r_add = struct.unpack(">IIi", elf.contents[i][o : o + 12])
            sym, rtype = r_info >> 8, r_info & 0xFF
            if in_dead(target, r_off):
                continue  # relocation inside a stripped symbol
            if target in removed:
                r_off = shift(target, r_off)
            if sym in removed_idx:
                if not args.gcc or elf.sections[target][2] & 0x4:  # SHF_EXECINSTR
                    sys.exit(
                        f"strip_unused: {elf.names[target]} still references removed symbol "
                        f"{sym_name(syms[sym])} (unit {args.unit})"
                    )
                # a surviving pointer to a stripped function: the linker left it zero
                elf.contents[target][r_off : r_off + 4] = b"\0\0\0\0"
                continue
            s = syms[sym]
            if (s[3] & 0xF) == STT_SECTION and s[5] in removed:
                try:
                    r_add = shift(s[5], r_add)
                except ValueError as e:
                    sys.exit(f"strip_unused: {elf.names[target]} relocation: {e}")
            out += struct.pack(">IIi", r_off, (remap[sym] << 8) | rtype, r_add)
        elf.contents[i] = out

    # Metrowerks .comment: fixed header followed by one 8-byte record per symbol.
    if ".comment" in elf.names:
        ci = elf.index(".comment")
        body = elf.contents[ci]
        hdr = len(body) - 8 * len(syms)
        if hdr >= 0:
            recs = [body[hdr + 8 * k : hdr + 8 * k + 8] for k in range(len(syms))]
            elf.contents[ci] = bytearray(body[:hdr]) + bytearray().join(
                r for k, r in enumerate(recs) if k not in removed_idx
            )

    elf.write(args.object)


if __name__ == "__main__":
    main()
