#!/usr/bin/env python3
"""Find where a compiled object's data sits in main.dol, and whether that placement is proven.

The linker dead-strips unused data objects, so a unit's data sections in the DOL are its
object's sections with holes closed up. This works the placement out from evidence and says how
strong the evidence is:

1. The object's functions are found in the DOL's code, walking from the unit's .text start with
   relocated fields masked (as libmatch.py does). A function that does not match is taken as
   stripped.
2. Every relocation in a found function that points into a data section is read back from the
   DOL instruction (lis/addi pairs, small-data r13/r2 offsets). That gives the DOL address of the
   data object it names: an "anchor".
3. Each data section is laid out from its anchors. An object with no anchor is placed at the next
   aligned address after the previous one and kept only if its bytes match the DOL there
   (relocated bytes masked); an object whose bytes are all zero, or that is in .bss, can only be
   kept when it fills the space before the next anchored object exactly.
4. Pointers inside kept data (ADDR32 relocations) are checked: each DOL word must equal the
   placed address of what it points to.

A section prints TRUSTED when every kept object is anchored, content-matched or an exact fit,
no two anchors disagree and every checked pointer resolves; otherwise UNTRUSTED with the reason.
The start..end it prints is what goes in splits.txt (round the end up to the next unit's start
when the next unit is aligned).

usage: datacheck.py OBJ TEXT [--dol main.dol] [-v]
       OBJ   the unit's object, unstripped (compile it as sdkcheck.py does) or as built
       TEXT  where the unit's .text starts in the DOL: an address, or the unit's name in
             config/<VERSION>/splits.txt (e.g. dolphin/vm/VM.c)
"""
import argparse
import os
import re
import struct
import sys

from elftools.elf.elffile import ELFFile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from libmatch import MASK, Dol, matches, obj_functions  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VER = os.environ.get("MVP_VERSION", "GV4E69")
DATA = (".data", ".rodata", ".bss", ".sdata", ".sbss", ".sdata2", ".sbss2")
R_ADDR32, R_LO, R_HI, R_HA, R_SDA21 = 1, 4, 5, 6, 109


def sext16(v):
    return v - 0x10000 if v & 0x8000 else v


def small_data_base(dol, reg):
    """The value the startup code loads into r13 or r2 (lis reg,X then addi or ori reg,reg,Y)."""
    for off, start, size in dol.secs[:7]:  # text sections
        for a in range(start, start + size - 4, 4):
            w = dol.word(a)
            if w >> 26 == 15 and (w >> 21) & 31 == reg and (w >> 16) & 31 == 0:
                n = dol.word(a + 4)
                if n >> 26 in (14, 24) and (n >> 21) & 31 == reg and (n >> 16) & 31 == reg:
                    lo = sext16(n & 0xFFFF) if n >> 26 == 14 else n & 0xFFFF
                    return ((w & 0xFFFF) << 16) + lo & 0xFFFFFFFF
    return None


def text_start(arg):
    if arg.lower().startswith("0x"):
        return int(arg, 16)
    unit = None
    for line in open(os.path.join(ROOT, "config", VER, "splits.txt")):
        if not line.startswith(("\t", " ")) and line.strip().endswith(":"):
            unit = line.strip()[:-1]
        elif unit == arg and line.split() and line.split()[0] == ".text":
            return int(re.search(r"start:(0x[0-9A-Fa-f]+)", line)[1], 16)
    sys.exit(f"{arg}: no .text range in splits.txt")


def named_functions():
    """{name: address} of the functions config/<VERSION>/symbols.txt names."""
    out = {}
    for line in open(os.path.join(ROOT, "config", VER, "symbols.txt")):
        m = re.match(r"(\S+) = \.text:(0x[0-9A-Fa-f]+);", line)
        if m:
            out[m[1]] = int(m[2], 16)
    return out


def find_functions(dol, path, start):
    """{name: DOL address} of the object's functions that sit in the DOL from start on. A
    function symbols.txt already names is checked at that address; the rest are found by walking
    the code from start, as libmatch.py does."""
    found, cur, named = {}, start, named_functions()
    for name, _, n, words, masks, _ in obj_functions(path):
        if name in named and matches(dol, named[name], words, masks):
            found[name] = named[name]
            cur = max(cur, named[name] + n)
            continue
        for pad in range(0, 32, 4):
            if pad and dol.word(cur + pad - 4) != 0:
                break
            if matches(dol, cur + pad, words, masks):
                found[name] = cur + pad
                cur += pad + n
                break
    return found


class Obj:
    def __init__(self, path):
        self.elf = ELFFile(open(path, "rb"))
        self.secs = list(self.elf.iter_sections())
        self.syms = list(self.elf.get_section_by_name(".symtab").iter_symbols())

    def rela(self, name):
        s = self.elf.get_section_by_name(".rela" + name)
        return list(s.iter_relocations()) if s else []

    def target(self, r):
        """(section name, offset in it) that a relocation points at, or None if undefined."""
        y = self.syms[r["r_info_sym"]]
        if not isinstance(y["st_shndx"], int) or y["st_shndx"] == 0:
            return None
        base = 0 if y["st_info"]["type"] == "STT_SECTION" else y["st_value"]
        return self.secs[y["st_shndx"]].name, base + r["r_addend"]

    def objects(self, sec):
        """[(offset, size, name, local)] of a section's data objects, in order."""
        idx = self.secs.index(sec)
        out = [
            (y["st_value"], y["st_size"], y.name, y["st_info"]["bind"] == "STB_LOCAL")
            for y in self.syms
            if y["st_shndx"] == idx and y["st_info"]["type"] == "STT_OBJECT"
        ]
        return sorted(set(out))


def anchors(dol, obj, funcs, sda, sda2):
    """{(section, offset): {DOL address: [function]}} read from the found functions' code."""
    fpos = {}
    text = obj.elf.get_section_by_name(".text")
    tidx = obj.secs.index(text)
    for y in obj.syms:
        if y["st_info"]["type"] == "STT_FUNC" and y["st_shndx"] == tidx and y.name in funcs:
            fpos[y.name] = (y["st_value"], y["st_size"])
    halves, out = {}, {}

    def add(key, addr, fn):
        out.setdefault(key, {}).setdefault(addr, []).append(fn)

    for r in obj.rela(".text"):
        o = r["r_offset"]
        fn = next((n for n, (v, s) in fpos.items() if v <= o < v + s), None)
        t = obj.target(r)
        if fn is None or t is None or t[0] not in DATA:
            continue
        w = dol.word(funcs[fn] + o - fpos[fn][0] - o % 4)  # r_offset may point at the low half
        if r["r_info_type"] == R_SDA21:
            ra = (w >> 16) & 31
            base = {13: sda, 2: sda2, 0: 0}.get(ra)
            if base is not None:
                add(t, base + sext16(w & 0xFFFF) & 0xFFFFFFFF, fn)
        elif r["r_info_type"] in (R_HA, R_HI, R_LO):
            halves.setdefault(t, {}).setdefault(r["r_info_type"], []).append((w & 0xFFFF, fn))
    for t, h in halves.items():
        for hi, fn in h.get(R_HA, []):
            for lo, _ in h.get(R_LO, []):
                add(t, ((hi << 16) + sext16(lo)) & 0xFFFFFFFF, fn)
        for hi, fn in h.get(R_HI, []):
            for lo, _ in h.get(R_LO, []):
                add(t, ((hi << 16) | lo) & 0xFFFFFFFF, fn)
    # A lis/addi pair can only be matched by (section, offset); if a function uses several
    # halves for one target, keep the address the most pairs agree on.
    for t, h in halves.items():
        if t in out and len(out[t]) > 1:
            best = max(out[t], key=lambda a: len(out[t][a]))
            out[t] = {best: out[t][best]}
    return out


def align_up(a, n):
    return (a + n - 1) // n * n


def natural_align(off, size, secalign):
    """An object's alignment, read from where the compiler put it in its own section."""
    a = 1
    while a < min(secalign, 8) and off % (a * 2) == 0:
        a *= 2
    return a


def lay_out(dol, obj, sec, refs):
    """Place a section's objects. Returns (placed [(name, off, size, addr, how)], problems)."""
    data = sec.data() if sec["sh_type"] != "SHT_NOBITS" else None
    mask = bytearray(sec["sh_size"])
    for r in obj.rela(sec.name):
        for q in range(4):
            if r["r_offset"] + q < len(mask):
                mask[r["r_offset"] + q] = 1
    objs = obj.objects(sec)
    if not objs:  # no object symbols: treat the section as one block (string pools and the like)
        objs = [(0, sec["sh_size"], "(section)", True)]
    problems = []
    fixed = {}
    for i, (off, size, name, _) in enumerate(objs):
        hits = {}
        for (s, o), addrs in refs.items():
            if s == sec.name and off <= o < off + max(size, 1):
                for a, fns in addrs.items():
                    hits.setdefault(a - (o - off), []).extend(fns)
        if len(hits) > 1:
            problems.append(f"{name}: anchors disagree ({', '.join(f'{a:08X}' for a in sorted(hits))})")
        if hits:
            fixed[i] = max(hits, key=lambda a: len(hits[a]))

    def content(i, addr):
        """True/False when the object's non-zero, non-relocated bytes (dis)agree; None if none."""
        off, size, _, _ = objs[i]
        if data is None or not size:
            return None
        informative = False
        for k in range(size):
            if mask[off + k]:
                continue
            want = data[off + k]
            got = dol.word((addr + k) & ~3)
            if got is None:
                return False
            got = (got >> (8 * (3 - (addr + k) % 4))) & 0xFF
            if want != got:
                return False
            informative |= want != 0
        return True if informative else None

    align = sec["sh_addralign"] or 1
    placed = [None] * len(objs)
    for i, a in fixed.items():
        placed[i] = (a, "anchored")
    if not fixed:
        return [], [f"no anchors: no found function refers to {sec.name}"]
    first = min(fixed)
    # Forward from the first anchor.
    cur = fixed[first] + objs[first][1]
    for i in range(first + 1, len(objs)):
        off, size, name, _ = objs[i]
        if i in fixed:
            cur = fixed[i] + size
            continue
        a = align_up(cur, natural_align(off, size, align))
        nj = next((j for j in range(i + 1, len(objs)) if j in fixed), None)
        c = content(i, a)
        if c:
            placed[i] = (a, "content")
        elif c is None and nj is None:
            placed[i] = (a, "unproven")
        elif c is None:
            # Kept only if it and everything up to the next anchor fill the space exactly.
            end = a + size
            for j in range(i + 1, nj + 1):
                end = align_up(end, natural_align(objs[j][0], objs[j][1], align))
                if j < nj:
                    end += objs[j][1]
            if end == fixed[nj]:
                placed[i] = (a, "fit")
        if placed[i]:
            cur = placed[i][0] + size
    # Backward from the first anchor: kept only when the bytes just before it match.
    nxt = fixed[first]
    for i in range(first - 1, -1, -1):
        off, size, name, _ = objs[i]
        n = natural_align(off, size, align)
        a = (nxt - size) // n * n
        c = content(i, a)
        if c:
            placed[i] = (a, "content")
            nxt = a
        else:
            placed[i] = None
            if c is None:
                problems.append(f"{name}: before the first anchor with nothing to check it by; taken as stripped")
    out = []
    for i, (off, size, name, _) in enumerate(objs):
        if placed[i]:
            a, how = placed[i]
            if how != "content" and content(i, a) is False:
                problems.append(f"{name}: bytes differ from the DOL at {a:08X}")
            if how == "unproven":
                problems.append(f"{name}: after the last anchor with no bytes to check; kept on trust")
            out.append((name, off, size, a, how))
        else:
            out.append((name, off, size, None, "stripped"))
    return out, problems


def pointer_anchors(dol, obj, layout):
    """{(section, offset): {DOL address: [where]}} read from the ADDR32 pointers in placed data."""
    out = {}
    for name, placed in layout.items():
        for r in obj.rela(name):
            t = obj.target(r)
            if r["r_info_type"] != R_ADDR32 or t is None or t[0] not in DATA:
                continue
            home = next((a + r["r_offset"] - off for n, off, size, a, _ in placed if a is not None and off <= r["r_offset"] < off + size), None)
            w = dol.word(home) if home is not None else None
            if w:
                out.setdefault(t, {}).setdefault(w, []).append(f"pointer in {name}")
    return out


def check_pointers(dol, obj, sec, placed, layout, funcs):
    """(ok, bad) counts of ADDR32 pointers in the section's kept objects."""
    where = {n: (off, size, a) for n, off, size, a, _ in placed if a is not None}
    ok = bad = 0
    text = obj.elf.get_section_by_name(".text")
    tidx = obj.secs.index(text) if text else -1
    fstart = {
        y["st_value"]: funcs[y.name]
        for y in obj.syms
        if y["st_info"]["type"] == "STT_FUNC" and y["st_shndx"] == tidx and y.name in funcs
    }
    for r in obj.rela(sec.name):
        if r["r_info_type"] != R_ADDR32:
            continue
        home = next(((off, a) for off, size, a in where.values() if off <= r["r_offset"] < off + size), None)
        t = obj.target(r)
        if home is None or t is None:
            continue
        if t[0] == ".text":
            want = fstart.get(t[1])
        else:
            want = next(
                (a + t[1] - off for n, off, size, a, _ in layout.get(t[0], []) if a is not None and off <= t[1] < off + max(size, 1)),
                None,
            )
        if want is None:
            continue
        if dol.word(home[1] + r["r_offset"] - home[0]) == want:
            ok += 1
        else:
            bad += 1
    return ok, bad


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("obj")
    ap.add_argument("text")
    ap.add_argument("--dol", default=os.path.join(ROOT, "orig", VER, "sys", "main.dol"))
    ap.add_argument("-v", action="store_true", help="list every object")
    args = ap.parse_args()
    dol = Dol(args.dol)
    obj = Obj(args.obj)
    funcs = find_functions(dol, args.obj, text_start(args.text))
    total = len(obj_functions(args.obj))
    print(f"functions: {len(funcs)} of {total} found in the DOL (the rest taken as stripped)")
    sda, sda2 = small_data_base(dol, 13), small_data_base(dol, 2)
    refs = anchors(dol, obj, funcs, sda, sda2)
    for _ in range(4):  # data only pointed to by other data is anchored once that data is placed
        layout, problems = {}, {}
        for sec in obj.secs:
            if sec.name in DATA and sec["sh_size"]:
                layout[sec.name], problems[sec.name] = lay_out(dol, obj, sec, refs)
        more = pointer_anchors(dol, obj, layout)
        new = {k: v for k, v in more.items() if k not in refs}
        if not new:
            break
        refs.update(new)
    for name, placed in layout.items():
        kept = [p for p in placed if p[3] is not None]
        ok, bad = check_pointers(dol, obj, obj.elf.get_section_by_name(name), placed, layout, funcs)
        if bad:
            problems[name].append(f"{bad} of {ok + bad} pointers do not resolve to the placed objects")
        if not kept:
            print(f"{name}: nothing placed ({'; '.join(problems[name]) or 'all stripped'})")
            continue
        start = min(p[3] for p in kept)
        end = max(p[3] + p[2] for p in kept)
        verdict = "UNTRUSTED" if problems[name] else "TRUSTED"
        extra = f", {ok} pointers checked" if ok else ""
        print(f"{name}: {start:08X}..{end:08X} ({len(kept)} of {len(placed)} objects kept{extra}) {verdict}")
        for p in problems[name]:
            print(f"   {p}")
        if args.v:
            for n, off, size, a, how in placed:
                at = f"{a:08X}" if a is not None else "--------"
                print(f"   {at}  +{off:<#6x} {size:<#6x} {how:9} {n}")


if __name__ == "__main__":
    main()
