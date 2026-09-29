#!/usr/bin/env python3
"""Measure how much code a related GameCube build shares with MVP 2005.

Every function in the reference build (from its ELF symbol table, or from an SN linker map plus
the ELF's code) is reduced to a relocation-blind fingerprint: branch targets and 16-bit
immediates of loads, stores, addi/addis and lis are masked, so the same C compiled the same way
matches even when it was linked at other addresses. The same is done for every function in
MVP's config/GV4E69/symbols.txt. A reference function "matches" when exactly one MVP function
has the same fingerprint. Short functions (under --min-insns) are skipped: they collide by chance.

Nothing from the reference build is written to the repo: the output is counts, plus a
per-library breakdown (by object or source file) to stdout and an optional TSV of matched
names for local use.

    python tools/research/refmatch.py --elf REF.elf [--map REF.map] [--tsv out.tsv]
"""

import argparse
import collections
import hashlib
import re
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOL = ROOT / "orig/GV4E69/sys/main.dol"
SYMBOLS = ROOT / "config/GV4E69/symbols.txt"

# D-form opcodes whose 16-bit immediate is often a relocation (lo/ha/sda21).
IMM_MASKED = {14, 15, 24, 25} | set(range(32, 56))


def mask(words):
    out = []
    for w in words:
        op = w >> 26
        if op == 18:  # b/bl: keep opcode, AA and LK
            w &= 0xFC000003
        elif op in IMM_MASKED:
            w &= 0xFFFF0000
        out.append(w)
    return out


def fingerprint(code):
    n = len(code) // 4
    words = struct.unpack(">%dI" % n, code[: n * 4])
    return hashlib.sha1(struct.pack(">%dI" % n, *mask(words))).hexdigest(), n


class Image:
    """Address-to-bytes lookup over a list of (address, bytes) sections."""

    def __init__(self, sections):
        self.sections = sections

    def read(self, addr, size):
        for base, data in self.sections:
            if base <= addr and addr + size <= base + len(data):
                return data[addr - base : addr - base + size]
        return None


def load_dol(path):
    raw = path.read_bytes()
    offs = struct.unpack(">18I", raw[0:72])
    addrs = struct.unpack(">18I", raw[72:144])
    sizes = struct.unpack(">18I", raw[144:216])
    return Image([(a, raw[o : o + s]) for o, a, s in zip(offs[:7], addrs[:7], sizes[:7]) if s])


def load_elf(path):
    """Returns (image, [(name, addr, size)]) from a big-endian 32-bit ELF."""
    raw = path.read_bytes()
    shoff, = struct.unpack(">I", raw[32:36])
    shentsize, shnum, shstrndx = struct.unpack(">HHH", raw[46:52])
    shdrs = [struct.unpack(">10I", raw[shoff + i * shentsize : shoff + i * shentsize + 40]) for i in range(shnum)]
    names = shdrs[shstrndx]
    def secname(off):
        s = raw[names[4] + off :]
        return s[: s.index(0)].decode("latin-1")
    sections, funcs = [], []
    for sh in shdrs:
        name, typ, flags, addr, off, size, link = sh[0], sh[1], sh[2], sh[3], sh[4], sh[5], sh[6]
        if typ == 1 and flags & 4 and addr:  # PROGBITS + EXECINSTR
            sections.append((addr, raw[off : off + size]))
    for sh in shdrs:
        if sh[1] != 2:  # SYMTAB
            continue
        strtab = shdrs[sh[6]]
        for i in range(sh[5] // 16):
            st_name, value, size, info, other, shndx = struct.unpack(">IIIBBH", raw[sh[4] + i * 16 : sh[4] + i * 16 + 16])
            if info & 0xF == 2 and size:
                s = raw[strtab[4] + st_name :]
                funcs.append((s[: s.index(0)].decode("latin-1"), value, size, ""))
    return Image(sections), funcs


# "addr size align" then the Out/In/File/Symbol column, told apart by its indent.
MAP_LINE = re.compile(r"^([0-9a-f]{8}) ([0-9a-f]{8}) +\d+( +)(\S.*)$")


def load_sn_map(path):
    """SN ngcld map: an object (File column) line, then its symbols one column deeper."""
    funcs, obj = [], ""
    for line in path.read_text(encoding="latin-1").splitlines():
        m = MAP_LINE.match(line)
        if not m:
            continue
        addr, size, indent, rest = int(m.group(1), 16), int(m.group(2), 16), len(m.group(3)), m.group(4)
        if indent >= 24 and size:
            funcs.append((rest.strip(), addr, size, obj))
        elif indent >= 16:
            obj = rest.strip()
    return funcs


def load_mvp():
    image = load_dol(DOL)
    funcs = []
    for line in SYMBOLS.read_text().splitlines():
        m = re.match(r"(\S+) = \.\w+:0x([0-9A-F]+); // type:function size:0x([0-9A-F]+)", line)
        if m:
            funcs.append((m.group(1), int(m.group(2), 16), int(m.group(3), 16)))
    return image, funcs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--elf", type=Path, required=True)
    ap.add_argument("--map", type=Path)
    ap.add_argument("--min-insns", type=int, default=12)
    ap.add_argument("--tsv", type=Path)
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()

    mimg, mfuncs = load_mvp()
    by_fp = collections.defaultdict(list)
    for name, addr, size in mfuncs:
        code = mimg.read(addr, size)
        if code and size // 4 >= args.min_insns:
            by_fp[fingerprint(code)[0]].append((name, addr, size))

    rimg, rfuncs = load_elf(args.elf)
    if args.map:
        rfuncs = load_sn_map(args.map)
    # One entry per reference function (aliases share an address), keyed by fingerprint.
    seen, ref = set(), []
    for name, addr, size, obj in rfuncs:
        if (addr, size) in seen or size // 4 < args.min_insns:
            continue
        seen.add((addr, size))
        code = rimg.read(addr, size)
        if code:
            ref.append((fingerprint(code)[0], name, obj))
    ref_count = collections.Counter(fp for fp, _, _ in ref)

    total, matched, rows = len(ref), 0, []
    per_obj = collections.Counter()
    per_obj_total = collections.Counter()
    for fp, name, obj in ref:
        key = obj or "(no object info)"
        per_obj_total[key] += 1
        hits = by_fp.get(fp, [])
        # Unique on both sides, or the name could belong to a look-alike.
        if len(hits) == 1 and ref_count[fp] == 1:
            matched += 1
            per_obj[key] += 1
            rows.append((hits[0][1], hits[0][2], name, obj))
    mvp_total = sum(len(v) for v in by_fp.values())
    print(f"reference functions (>= {args.min_insns} insns): {total}")
    print(f"unique fingerprint matches in MVP: {matched} "
          f"({matched / max(total, 1):.1%} of reference, {matched / max(mvp_total, 1):.1%} of MVP's {mvp_total})")
    if args.map:
        print("top objects by matches:")
        for obj, n in per_obj.most_common(args.top):
            print(f"  {n:5d}/{per_obj_total[obj]:<5d} {obj}")
    if args.tsv:
        with open(args.tsv, "w") as f:
            for mvp_addr, size, name, obj in sorted(rows):
                f.write(f"0x{mvp_addr:08X}\t0x{size:X}\t{name}\t{obj}\n")


if __name__ == "__main__":
    sys.exit(main())
