#!/usr/bin/env python3
"""Name what imported code refers to: read each relocation of a compiled unit against main.dol.

For every relocation in an object's .text, the original instruction at the unit's split address
holds the target the original linker filled in: a branch target (R_PPC_REL24), or a 32-bit
address split over an @ha/@lo pair (R_PPC_ADDR16_HA + R_PPC_ADDR16_LO). The relocation names the
symbol, so each target address gets the name the imported source uses for it.

Only external (undefined) symbols are reported; references inside the unit are its own. Rows
disagreeing with each other (one name at two addresses, or two names at one address) are
reported on stderr and left out.

Output (TSV): address, name, first unit that refers to it. Feed the first two columns to
tools/rename_symbols.py; list the ones still asm in config/<ver>/linked_names.tsv.
With --defs: the units' own functions and objects (address, name, scope) at their split
addresses, the rows rename_symbols.py needs for the units themselves.

usage: relocnames.py <unit> [<unit> ...]   (unit as in splits.txt, e.g. snd/cmn/spitch.c;
       its object is build/<ver>/src/<unit>.o, so run ninja first)
"""
import argparse
import os
import struct
import sys

from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VER = os.environ.get("MVP_VERSION", "GV4E69")

R_ADDR32, R_ADDR16_LO, R_ADDR16_HA, R_REL24 = 1, 4, 6, 10


class Dol:
    def __init__(self, path):
        self.data = open(path, "rb").read()
        hdr = self.data
        offs = struct.unpack(">18I", hdr[0:72])
        addrs = struct.unpack(">18I", hdr[72:144])
        sizes = struct.unpack(">18I", hdr[144:216])
        self.segs = [(a, o, s) for o, a, s in zip(offs, addrs, sizes) if s]

    def word(self, addr):
        for a, o, s in self.segs:
            if a <= addr < a + s:
                return struct.unpack(">I", self.data[o + addr - a:o + addr - a + 4])[0]
        raise ValueError(f"0x{addr:08X} is not in the DOL")


def split_starts(unit):
    """The unit's section start addresses from splits.txt, e.g. {".text": 0x803A9170}."""
    cur, out = None, {}
    for line in open(os.path.join(ROOT, "config", VER, "splits.txt")):
        if line and not line[0].isspace() and line.rstrip().endswith(":"):
            cur = line.rstrip()[:-1]
        elif cur == unit and "start:" in line:
            out[line.split()[0]] = int(line.split("start:")[1].split()[0], 16)
    return out


def text_start(unit):
    """The unit's .text start address from splits.txt."""
    start = split_starts(unit).get(".text")
    if start is None:
        sys.exit(f"{unit}: no .text split")
    return start


def obj_path(unit):
    return os.path.join(ROOT, "build", VER, "src", os.path.splitext(unit)[0] + ".o")


def defs(unit):
    """The unit's own named functions and objects at their split addresses: (addr, name, scope)."""
    starts = split_starts(unit)
    e = ELFFile(open(obj_path(unit), "rb"))
    secs = list(e.iter_sections())
    for s in e.get_section_by_name(".symtab").iter_symbols():
        if not isinstance(s["st_shndx"], int) or not s.name:
            continue
        sec = secs[s["st_shndx"]].name
        # GCC 2.95 leaves some data symbols untyped (STT_NOTYPE); code labels are never named
        if s["st_info"]["type"] not in ("STT_FUNC", "STT_OBJECT") and (
                s["st_info"]["type"] != "STT_NOTYPE" or sec == ".text"):
            continue
        if sec not in starts:
            sys.exit(f"{unit}: {s.name} is in {sec}, which has no split")
        scope = "global" if s["st_info"]["bind"] == "STB_GLOBAL" else "local"
        yield starts[sec] + s["st_value"], s.name, scope


def sext16(v):
    return v - 0x10000 if v & 0x8000 else v


def refs(dol, unit):
    base = text_start(unit)
    e = ELFFile(open(obj_path(unit), "rb"))
    symtab = e.get_section_by_name(".symtab")
    for sec in e.iter_sections():
        if not isinstance(sec, RelocationSection) or sec.name not in (".rela.text", ".rel.text"):
            continue
        has = {}
        for r in sec.iter_relocations():
            sym = symtab.get_symbol(r["r_info_sym"])
            if sym["st_shndx"] != "SHN_UNDEF":
                continue
            t, off, add = r["r_info_type"], r["r_offset"], (r["r_addend"] if r.is_RELA() else 0)
            if t == R_REL24:
                ins = dol.word(base + (off & ~3))
                li = ins & 0x03FFFFFC
                if li & 0x02000000:
                    li -= 0x04000000
                yield base + (off & ~3) + li - add, sym.name
            elif t == R_ADDR16_HA:
                has[(sym.name, add)] = dol.word(base + off - 2) & 0xFFFF
            elif t == R_ADDR16_LO and (sym.name, add) in has:
                hi = has[(sym.name, add)]
                lo = sext16(dol.word(base + off - 2) & 0xFFFF)
                yield ((hi << 16) + lo - add) & 0xFFFFFFFF, sym.name
            elif t == R_ADDR16_LO:
                print(f"{unit}: @lo of {sym.name} with no @ha before it, skipped", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("units", nargs="+")
    ap.add_argument("--dol", default=os.path.join(ROOT, "orig", VER, "sys", "main.dol"))
    ap.add_argument("--defs", action="store_true",
                    help="list the units' own functions and objects instead (address, name, scope)")
    args = ap.parse_args()
    if args.defs:
        for unit in args.units:
            for addr, name, scope in defs(unit):
                print(f"0x{addr:08X}\t{name}\t{scope}")
        return
    dol = Dol(args.dol)
    by_addr, by_name, first = {}, {}, {}
    for unit in args.units:
        for addr, name in refs(dol, unit):
            by_addr.setdefault(addr, set()).add(name)
            by_name.setdefault(name, set()).add(addr)
            first.setdefault(addr, unit)
    bad = False
    for addr in sorted(by_addr):
        names = by_addr[addr]
        if len(names) > 1 or any(len(by_name[n]) > 1 for n in names):
            print(f"conflict at 0x{addr:08X}: {sorted(names)} "
                  f"{[f'0x{a:08X}' for n in names for a in sorted(by_name[n])]}", file=sys.stderr)
            bad = True
            continue
        print(f"0x{addr:08X}\t{next(iter(names))}\t{first[addr]}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
