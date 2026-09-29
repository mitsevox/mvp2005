#!/usr/bin/env python3
"""Find where a library's compiled objects sit in main.dol, function by function.

Each object's functions are compared with the DOL's code with every relocated field masked (the
bits a relocation fills in: 16-bit halves, branch targets, small-data offsets). The objects are
walked in link order along the .text window: a function that matches at the cursor is kept there,
one that does not was dead-stripped by the linker; a function that matches uniquely elsewhere
ahead of the cursor (at least 16 bytes) resynchronises the walk and leaves a gap, which is code
that does not match yet.

Output, one row per kept function: address, name, size, scope, unit. Gaps are listed on stderr.
Feed the rows to tools/rename_symbols.py (the first three columns) and use the unit ranges for
splits.txt.

usage: libmatch.py --window 0x80414F30 0x8043F058 obj1.o obj2.o ...   (objects in link order,
       unstripped: build them without the strip step, or compile the upstream source directly)
"""
import argparse
import os
import struct
import sys

from elftools.elf.elffile import ELFFile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VER = os.environ.get("MVP_VERSION", "GV4E69")

# Bits a relocation fills in, by ELF PPC relocation type.
MASK = {1: 0xFFFFFFFF, 4: 0xFFFF, 5: 0xFFFF, 6: 0xFFFF, 10: 0x03FFFFFC, 11: 0xFFFC, 109: 0x1FFFFF}


class Dol:
    def __init__(self, path):
        self.data = open(path, "rb").read()
        self.secs = list(
            zip(
                struct.unpack(">18I", self.data[0:72]),
                struct.unpack(">18I", self.data[72:144]),
                struct.unpack(">18I", self.data[144:216]),
            )
        )

    def word(self, addr):
        for off, start, size in self.secs:
            if start <= addr < start + size:
                return struct.unpack(">I", self.data[off + addr - start : off + addr - start + 4])[0]
        return None


def obj_functions(path):
    """[(name, offset, size, words, masks, scope)] of an object's .text functions, in order."""
    out = []
    with open(path, "rb") as f:
        elf = ELFFile(f)
        symtab = elf.get_section_by_name(".symtab")
        for idx, sec in enumerate(elf.iter_sections()):
            if sec.name != ".text":
                continue
            data = sec.data()
            masks = [0] * (len(data) // 4)
            rela = elf.get_section_by_name(".rela.text")
            for r in rela.iter_relocations() if rela else ():
                masks[r["r_offset"] // 4] |= MASK.get(r["r_info_type"], 0xFFFFFFFF)
            for s in symtab.iter_symbols():
                if s["st_info"]["type"] == "STT_FUNC" and s["st_shndx"] == idx and s["st_size"]:
                    v, n = s["st_value"], s["st_size"]
                    words = [struct.unpack(">I", data[v + i : v + i + 4])[0] for i in range(0, n, 4)]
                    scope = "global" if s["st_info"]["bind"] == "STB_GLOBAL" else "local"
                    out.append((s.name, v, n, words, masks[v // 4 : (v + n) // 4], scope))
    return sorted(out, key=lambda f: f[1])


def matches(dol, addr, words, masks):
    for i, (w, m) in enumerate(zip(words, masks)):
        d = dol.word(addr + i * 4)
        if d is None or (w & ~m) != (d & ~m):
            return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", nargs=2, required=True, metavar=("START", "END"))
    ap.add_argument("--dol", default=os.path.join(ROOT, "orig", VER, "sys", "main.dol"))
    ap.add_argument("objects", nargs="+")
    args = ap.parse_args()
    lo, hi = int(args.window[0], 0), int(args.window[1], 0)
    dol = Dol(args.dol)
    units = [(os.path.splitext(os.path.basename(p))[0], obj_functions(p)) for p in args.objects]

    # Unique hits anywhere in the window, for resynchronising after code that does not match.
    unique = {}
    for unit, funcs in units:
        for name, _, n, words, masks, _ in funcs:
            if n < 16:
                continue
            hits = [a for a in range(lo, hi - n + 1, 4) if matches(dol, a, words, masks)]
            if len(hits) == 1:
                unique[(unit, name)] = hits[0]

    cur = lo
    for unit, funcs in units:
        first = None
        for name, _, n, words, masks, scope in funcs:
            at = None
            for pad in range(0, 32, 4):  # zero padding before a function
                if pad and dol.word(cur + pad - 4) != 0:
                    break
                if matches(dol, cur + pad, words, masks):
                    at = cur + pad
                    break
            if at is None and cur <= unique.get((unit, name), -1) < cur + 0x3000:
                at = unique[(unit, name)]
                print(f"gap {cur:08X}..{at:08X} ({at - cur:#x}) before {unit}:{name}", file=sys.stderr)
            if at is None:
                continue
            first = at if first is None else first
            print(f"{at:08X}\t{name}\t{n:#x}\t{scope}\t{unit}")
            cur = at + n
        if first is not None:
            print(f"unit {unit}: {first:08X}..{cur:08X}", file=sys.stderr)


if __name__ == "__main__":
    main()
