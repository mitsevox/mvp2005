#!/usr/bin/env python3
"""Rename symbols in config/<ver>/symbols.txt from a TSV of `address<TAB>name[<TAB>scope]` rows.

Only the name (and, when given, the scope attribute) changes; address, type and size stay. A row
whose address has no symbol yet is added with the type and size given in the optional 4th and 5th
columns (`object`/`function`, hex size). Refuses a name already used at another address.

usage: rename_symbols.py names.tsv [--dry-run]
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VER = os.environ.get("MVP_VERSION", "GV4E69")
LINE = re.compile(r"^(\S+) = (\.\w+):0x([0-9A-Fa-f]+);(.*)$")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    path = os.path.join(ROOT, "config", VER, "symbols.txt")
    lines = open(path).read().split("\n")
    by_addr = {}
    names = {}
    for i, line in enumerate(lines):
        m = LINE.match(line)
        if m:
            by_addr.setdefault(int(m.group(3), 16), []).append(i)
            names[m.group(1)] = int(m.group(3), 16)
    changed = 0
    added = []
    for row in open(args.tsv):
        row = row.rstrip("\n")
        if not row or row.startswith("#"):
            continue
        cols = row.split("\t")
        addr, name = int(cols[0], 16), cols[1]
        scope = cols[2] if len(cols) > 2 and cols[2] else None
        if name in names and names[name] != addr:
            sys.exit(f"{name} already names {names[name]:#010x}, not {addr:#010x}")
        idx = by_addr.get(addr, [])
        if not idx:
            if len(cols) < 6:
                sys.exit(f"no symbol at {addr:#010x}; give section, type and size to add {name}")
            sec, typ, size = cols[3], cols[4], cols[5]
            added.append((addr, f"{name} = {sec}:0x{addr:08X}; // type:{typ} size:{size}" + (f" scope:{scope}" if scope else "")))
            names[name] = addr
            continue
        if len(idx) > 1:
            # prefer the non-label symbol (a function or object) at this address
            idx = [i for i in idx if "type:label" not in lines[i]] or idx
        i = idx[0]
        m = LINE.match(lines[i])
        rest = m.group(4)
        if scope:
            rest = re.sub(r" scope:\w+", "", rest) + f" scope:{scope}"
        new = f"{name} = {m.group(2)}:0x{m.group(3)};{rest}"
        if new != lines[i]:
            if m.group(1) != name:
                names.pop(m.group(1), None)
            names[name] = addr
            lines[i] = new
            changed += 1
    if added:
        # keep the file sorted by section order, then address: insert after the last lower address
        for addr, text in sorted(added):
            sec = text.split(" = ")[1].split(":")[0]
            pos = None
            for i, line in enumerate(lines):
                m = LINE.match(line)
                if m and m.group(2) == sec:
                    if int(m.group(3), 16) < addr:
                        pos = i + 1
                    elif pos is None:
                        pos = i
            lines.insert(pos if pos is not None else len(lines), text)
    print(f"{changed} renamed, {len(added)} added")
    if not args.dry_run:
        open(path, "w").write("\n".join(lines))


if __name__ == "__main__":
    main()
