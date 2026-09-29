#!/usr/bin/env python3
"""The evidence file map (discovery step 7, docs/filemap.md).

Places functions in EA's source files only where the binary, or a related EA build, proves it.
Nothing here is a guess: a function with no evidence stays "unplaced", and matching places it
later (each file's constant pool has to line up, which proves its edges).

Evidence, strongest first:
  end    GCC 2.95 ends each file that has global objects with its static-init pair
         (_GLOBAL_$I, then _GLOBAL_$D when the file has destructors). Both are listed in
         .ctors/.dtors, so the function after them starts a new file: an exact edge.
  path   A function that references a `__FILE__` string ("C:/mvp2004/source/.../x.cpp") is in x.cpp.
         Header paths (.h) are left out: inline code from a header lands in many files.
  map    SN linker maps of FIFA 2005 and UEFA CL 2004-05 (EA Canada, same toolchain) name the
         object file of library functions that match ours byte for byte (--maps, from
         tools/research/refmatch.py --tsv). The name lists stay outside the repo.

Class evidence (docs/names.md) is not used: a class's constructor is inlined into other files and
its getters are emitted away from it (docs/filemap.md "What did not work").

A unit is a run of functions whose evidence agrees. The same file in two separate runs is
reported as a conflict, not resolved.

    python tools/research/filemap.py [--maps a.tsv b.tsv] [--tsv config/GV4E69/filemap.tsv]

Needs `ninja` to have run (reads build/GV4E69/asm and orig/GV4E69/sys/main.dol).
"""
import argparse
import collections
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ASM = ROOT / "build/GV4E69/asm"
TEXT = ASM / "auto_01_800034A0_text.s"
CTORDTOR = ASM / "auto_02_805A2BC0_ctordtor.s"
RODATA = ASM / "auto_03_805A2DA0_rodata.s"
DATA = ASM / "auto_04_8060F120_data.s"

# Blocks of .text (docs/sdk.md). The SDK and runtime block is imported from public decomps
# (docs/sdk.md, the "Import SDK and library code" work) and is left out here.
BLOCKS = [
    (0x800034A0, 0x80364000, "game"),
    (0x80364000, 0x80403F08, "ea-lib"),
    (0x8043F058, 0x805A2BC0, "game"),
]

INS = re.compile(r"^/\* ([0-9A-F]{8}) [^*]*\*/\t(.*)$")


def read_text():
    """Functions in address order: name, address, size, referenced labels, first instructions."""
    funcs, cur = [], None
    for line in open(TEXT, encoding="utf-8"):
        if line.startswith(".fn "):
            cur = {"name": line.split()[1].rstrip(","), "addr": None, "end": None,
                   "refs": set(), "body": []}
            funcs.append(cur)
            continue
        m = INS.match(line)
        if m and cur is not None:
            a = int(m.group(1), 16)
            if cur["addr"] is None:
                cur["addr"] = a
            cur["end"] = a + 4
            ins = m.group(2).strip()
            if len(cur["body"]) < 4:
                cur["body"].append(ins)
            cur["refs"].update(re.findall(r"\b(lbl_[0-9A-F]{8})@", ins))
    return funcs


def read_objects(path):
    """Label -> list of lines, for .obj blocks of a dtk data asm file."""
    objs, cur = {}, None
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^\.obj (\S+),", line)
        if m:
            cur = m.group(1)
            objs[cur] = []
        elif line.startswith(".endobj"):
            cur = None
        elif cur:
            objs[cur].append(line.strip())
    return objs


def static_init_ends(funcs):
    """Addresses after which a file ends: the last of each _GLOBAL_$I/$D pair."""
    lists, cur = [[]], None
    for line in read_objects(CTORDTOR).values():
        for item in line:
            m = re.match(r"\.4byte (fn_[0-9A-F]{8}|0x[0-9A-F]+)$", item)
            if not m:
                continue
            if m.group(1) == "0xFFFFFFFF":
                lists.append([])
            elif m.group(1).startswith("fn_"):
                lists[-1].append(int(m.group(1)[3:], 16))
    ctors, dtors = lists[1], lists[2] if len(lists) > 2 else []
    by_addr = {f["addr"]: i for i, f in enumerate(funcs)}
    ends = {}
    for a in ctors:
        i = by_addr[a]
        # The $D function directly follows $I when the file has one.
        if i + 1 < len(funcs) and funcs[i + 1]["addr"] in dtors:
            i += 1
        ends[funcs[i]["addr"]] = "static-init"
    return ends, len(ctors), len(dtors)


def path_anchors(funcs):
    strings = {}
    for label, lines in read_objects(RODATA).items():
        for item in lines:
            m = re.match(r'\.string "(.*)"$', item)
            if m:
                strings[label] = m.group(1)
                break
    anchors = {}
    for f in funcs:
        paths = {strings[r] for r in f["refs"] if r in strings
                 and re.search(r"[/\\][^/\\]+\.(cpp|c)$", strings[r], re.I)}
        if len(paths) == 1:
            p = paths.pop().replace("\\", "/")
            anchors[f["addr"]] = ("path", p.rsplit("/", 1)[1].lower(), p)
    return anchors


def map_anchors(tsvs):
    anchors = {}
    for tsv in tsvs:
        for line in open(tsv, encoding="latin-1"):
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4 or not parts[3]:
                continue
            obj = parts[3]
            m = re.search(r"\(([^()]+)\)$", obj)
            unit = (m.group(1) if m else obj.replace("\\", "/").rsplit("/", 1)[-1])
            unit = re.sub(r"\.(cpp|c)\.obj$", r".\1", unit.lower())
            lib = re.search(r"([^/\\]+\.a)\(", obj)
            lib = lib.group(1).lower() if lib else ""
            addr = int(parts[0], 16)
            # Only the EA library block: map hits in game code are look-alikes
            # (docs/reference-builds/README.md "How overlap was measured").
            if any(lo <= addr < hi and block == "ea-lib" for lo, hi, block in BLOCKS):
                # The key carries the library: two libraries can both have a state.o.
                # The source column names the evidence, not the other game's build paths.
                anchors.setdefault(addr, ("map", f"{lib}({unit})" if lib else unit, "SN map: " + tsv.stem))
    return anchors


def build(funcs, ends, anchors):
    """Units per block: runs of agreeing anchors, split at static-init ends.

    Any change of key starts a new run. The same file key in separate runs is a conflict:
    reported, not resolved.
    """
    units = []
    for lo, hi, block in BLOCKS:
        fs = [f for f in funcs if lo <= f["addr"] < hi]
        runs, cur, start_exact = [], None, True  # the block start is an exact edge
        for f in fs:
            a = anchors.get(f["addr"])
            if a:
                key = (a[0], a[1])
                if cur and cur["key"] != key:
                    runs.append(cur)
                    cur = None
                if cur is None:
                    cur = {"key": key, "src": a[2], "block": block, "first": f, "last": f,
                           "n": 0, "start_exact": start_exact, "end_exact": False}
                cur["last"] = f
                cur["n"] += 1
            start_exact = False
            if f["addr"] in ends:
                # The file ending here is the open run's only when the static-init pair is
                # its own anchor; otherwise another file may sit between, so the run stays
                # open-ended and the end is recorded on its own.
                if cur is not None and cur["last"] is f:
                    cur["end_exact"] = True
                    runs.append(cur)
                else:
                    if cur is not None:
                        runs.append(cur)
                    runs.append({"key": ("end", ""), "src": "", "block": block, "first": None,
                                 "last": f, "n": 0, "start_exact": False, "end_exact": True})
                cur = None
                start_exact = True
        if cur:
            runs.append(cur)
        units.extend(runs)
    seen = collections.defaultdict(list)
    for u in units:
        if u["key"][0] in ("path", "map"):
            seen[u["key"]].append(u)
    conflicts = [(k, [u["first"]["addr"] for u in us]) for k, us in seen.items() if len(us) > 1]
    return units, conflicts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--maps", nargs="*", type=Path, default=[])
    ap.add_argument("--tsv", type=Path)
    args = ap.parse_args()

    funcs = read_text()
    ends, n_ctors, n_dtors = static_init_ends(funcs)
    anchors = {}
    for source in (map_anchors(args.maps), path_anchors(funcs)):
        anchors.update(source)
    units, conflicts = build(funcs, ends, anchors)

    kinds = collections.Counter(v[0] for v in anchors.values())
    print(f"static-init ends: {len(ends)} ({n_ctors} ctors, {n_dtors} dtors)")
    print("anchored functions:", dict(kinds))
    for lo, hi, block in BLOCKS:
        total = sum(1 for f in funcs if lo <= f["addr"] < hi)
        bu = [u for u in units if u["block"] == block and lo <= u["last"]["addr"] < hi]
        named = [u for u in bu if u["key"][0] != "end"]
        exact = sum(1 for u in bu if u["start_exact"] and u["end_exact"])
        placed = sum(1 for f in funcs if lo <= f["addr"] < hi and any(
            u["first"] and u["first"]["addr"] <= f["addr"] <= u["last"]["addr"] for u in named))
        print(f"{block} {lo:08X}..{hi:08X}: {total} functions, {len(named)} named units "
              f"placing {placed} functions ({placed / total:.1%}), "
              f"{len(bu) - len(named)} unnamed exact-end files, {exact} with both edges exact")
    print(f"conflicts (same key in separate runs): {len(conflicts)}")
    for key, addrs in conflicts[:15]:
        print("  ", key, " ".join(f"{a:08X}" for a in addrs))

    if args.tsv:
        with open(args.tsv, "w") as out:
            out.write("# Evidence file map (tools/research/filemap.py, docs/filemap.md). One row per unit.\n")
            out.write("# first/last: the first and last function the evidence places in the unit;\n")
            out.write("# start/end 'exact' when the edge is proven; 'open' means the true edge is at first/last or beyond.\n")
            out.write("block\tunit\tkind\tsource\tfirst\tlast\tstart\tend\tanchors\n")
            for u in units:
                first = f"{u['first']['addr']:08X}" if u["first"] else "-"
                out.write("\t".join([
                    u["block"], u["key"][1] or "-", u["key"][0], u["src"] or "-", first,
                    f"{u['last']['addr']:08X}",
                    "exact" if u["start_exact"] else "open",
                    "exact" if u["end_exact"] else "open", str(u["n"])]) + "\n")


if __name__ == "__main__":
    main()
