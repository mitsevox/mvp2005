#!/usr/bin/env python3
"""EA's class type IDs (docs/names.md "Class type IDs").

EA's classes carry a hand-rolled type system: a virtual function returns the class name
("cCameraBasic") and another returns a 32-bit ID, which is the djb2 hash of that name
(h = 5381; h = h * 33 + c). This tool finds every 32-bit constant the code builds
(lis + ori/addi on the same register) and prints the ones that hash a string found in the DOL.

  python tools/research/typeids.py            # summary
  python tools/research/typeids.py --tsv      # function, address, kind, class name

Needs `ninja` to have run (reads build/GV4E69/asm and orig/GV4E69/sys/main.dol).
"""
import argparse
import collections
import re

DOL = "orig/GV4E69/sys/main.dol"
ASM = "build/GV4E69/asm/auto_01_800034A0_text.s"


def djb2(data: bytes) -> int:
    h = 5381
    for c in data:
        h = (h * 33 + c) & 0xFFFFFFFF
    return h


def dol_strings(path: str, minlen: int = 3):
    """Every NUL-terminated printable run in the DOL's sections."""
    data = open(path, "rb").read()
    for m in re.finditer(rb"[\x20-\x7e]{%d,}" % minlen, data):
        yield m.group(0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", action="store_true")
    args = ap.parse_args()

    names = {}
    for s in dol_strings(DOL):
        names.setdefault(djb2(s), s.decode("ascii"))

    rows = []  # (function, address, kind, name)
    fn = None
    body = []  # instructions of the current function
    pending = []  # (address, name) hits in the current function
    lis = {}
    built = 0
    ins_re = re.compile(r"^/\* ([0-9A-F]{8}) [^*]*\*/\t(.*)$")

    def flush():
        # A type-ID getter is exactly: lis r3; ori/addi r3, r3; blr.
        getter = len(body) == 3 and body[0].startswith("lis r3,") and body[2] == "blr"
        for addr, name in pending:
            rows.append((fn, addr, "getter" if getter else "use", name))

    for line in open(ASM, encoding="utf-8"):
        if line.startswith(".fn "):
            if fn:
                flush()
            fn = line.split()[1].rstrip(",")
            body, pending, lis = [], [], {}
            continue
        m = ins_re.match(line)
        if not m:
            continue
        addr, ins = m.group(1), m.group(2).strip()
        body.append(ins)
        m = re.match(r"lis (r\d+), (0x[0-9a-f]+)$", ins)
        if m:
            lis[m.group(1)] = int(m.group(2), 16)
            continue
        m = re.match(r"(ori|addi) (r\d+), (r\d+), (-?0x[0-9a-f]+)$", ins)
        if m and m.group(3) in lis:
            hi, lo = lis[m.group(3)], int(m.group(4), 16)
            if m.group(1) == "ori":
                value = (hi << 16) | (lo & 0xFFFF)
            else:
                value = ((hi << 16) + lo) & 0xFFFFFFFF
            built += 1
            if value in names:
                pending.append((addr, names[value]))
    if fn:
        flush()

    if args.tsv:
        for r in rows:
            print("\t".join(r))
        return
    kinds = collections.Counter(r[2] for r in rows)
    print(f"{built} 32-bit constants built; {len(rows)} are djb2 of a DOL string "
          f"({kinds['getter']} in type-ID getters, {kinds['use']} elsewhere); "
          f"{len(set(r[3] for r in rows))} distinct names; {len(set(r[0] for r in rows))} functions")


if __name__ == "__main__":
    main()
