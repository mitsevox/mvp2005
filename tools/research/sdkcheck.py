#!/usr/bin/env python3
"""Compile one C file with the SDK flags and compare named functions with the DOL.

Relocated fields are masked (as in libmatch.py), so a function that prints OK matches byte for
byte once linked. Use it to test an upstream source, or an edit to one, before importing it.

usage: sdkcheck.py file.c NAME=0xADDR [NAME=0xADDR ...] [--sub "OLD>NEW;OLD>NEW"]
       --sub swaps single flag tokens, e.g. --sub "unsigned>signed" for -char signed.
"""
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from libmatch import Dol, obj_functions  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VER = os.environ.get("MVP_VERSION", "GV4E69")
FLAGS = (
    "-nodefaults -proc gekko -fp hard -Cpp_exceptions off -enum int -char unsigned -warn pragmas "
    "-requireprotos -pragma".split()
    + ["cats off"]
    + "-O4,p -inline auto -I- -i include -i include/libc -i src/dolphin -D__GEKKO__ "
    "-DSDK_REVISION=1 -lang=c".split()
)


def main():
    args = sys.argv[1:]
    subs = []
    if "--sub" in args:
        i = args.index("--sub")
        subs = [s.split(">") for s in args[i + 1].split(";")]
        del args[i : i + 2]
    src = os.path.abspath(args[0])
    flags = list(FLAGS)
    for old, new in subs:
        flags = [new if f == old else f for f in flags]
    out = os.path.join(tempfile.mkdtemp(), "sdkcheck.o")
    cmd = ["build/tools/wibo", "build/tools/sjiswrap.exe", f"build/compilers/GC/{os.environ.get('SDK_MW', '1.2.5n')}/mwcceppc.exe"]
    r = subprocess.run(cmd + flags + ["-c", src, "-o", out], cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stdout[-3000:] + r.stderr[-2000:])
    dol = Dol(os.path.join(ROOT, "orig", VER, "sys", "main.dol"))
    funcs = {f[0]: f for f in obj_functions(out)}
    for pair in args[1:]:
        name, addr = pair.split("=")
        addr = int(addr, 16)
        if name not in funcs:
            print(f"{name}: not in the object")
            continue
        _, _, n, words, masks, _ = funcs[name]
        bad = [i for i, (w, m) in enumerate(zip(words, masks)) if (w & ~m) != (dol.word(addr + 4 * i) & ~m)]
        print(f"{name}: size {n:#x}, " + (f"{len(bad)} words differ, first at +{bad[0] * 4:#x}" if bad else "OK"))
        for i in bad[:6]:
            print(f"   +{i * 4:#x} ours {words[i]:08x} dol {dol.word(addr + 4 * i):08x}")


if __name__ == "__main__":
    main()
