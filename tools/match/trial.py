#!/usr/bin/env python3
"""Compile one variant of a unit and diff one function against the target.

The quick loop for matching one function: edit a copy of the unit's source in your scratch
folder, run this, read the diff, repeat. Nothing in src/ or the build is touched.

usage: python tools/match/trial.py <unit source> <symbol> [--src variant.cpp] [--version GV4E69]

  <unit source>  the unit as configure.py knows it, e.g. src/common/geomlib/geomcone.cpp; its
                 compile command (flags, compiler) comes from build.ninja
  <symbol>       the function's symbol as in symbols.txt, e.g. Clone__8GeomConePC6COORD4
  --src          the variant to compile instead of the unit's own source (default: the unit)

Needs a configured build (python configure.py && ninja, once). The target is dtk's split object
build/<version>/obj/<unit>.o. Instructions are compared with their addresses dropped and branch
targets made function-relative; relocations are listed with their symbols. Instructions only
count toward the score; a relocation naming a different symbol (for example a literal the target
names lbl_... and the compile names .rodata) is shown but not scored, so check those by eye.
Exit status 0 when the instructions are identical.
"""
import argparse
import difflib
import os
import re
import shlex
import subprocess
import sys

OBJDUMP = os.path.join("build", "binutils", "powerpc-eabi-objdump")


def compile_command(version, unit):
    # The unit's compile step: the last line ninja prints for its object, up to the first "&&"
    # (post-build steps such as strip_unused do not change a function's code).
    obj = os.path.join("build", version, "src", os.path.splitext(unit)[0] + ".o")
    out = subprocess.run(["ninja", "-t", "commands", obj], capture_output=True, text=True)
    lines = out.stdout.strip().splitlines()
    if out.returncode or not lines:
        sys.exit(f"trial.py: ninja knows no object {obj} (run python configure.py first)")
    return shlex.split(lines[-1].split("&&")[0])


def text_symbols(obj):
    # .text offset -> symbol, to name a call the compiler wrote as ".text+0x..." (a function in
    # the same object).
    out = subprocess.run([OBJDUMP, "-t", obj], capture_output=True, text=True).stdout
    names = {}
    for line in out.splitlines():
        f = line.split()
        if len(f) >= 6 and f[-3] == ".text" and "F" in f[1:-3]:
            names[int(f[0], 16)] = f[-1]
    return names


def reloc_target(sym, names):
    m = re.match(r"\.text\+0x([0-9a-f]+)$", sym)
    if m:
        # A call to a function in this object, or a branch inside one (SN's assembler keeps a
        # relocation on some local branches): written as objdump writes the target's branches.
        at = int(m.group(1), 16)
        starts = [s for s in names if s <= at]
        if starts:
            start = max(starts)
            return names[start] if at == start else f"<{names[start]}+{hex(at - start)}>"
    # Unnamed data (a literal pool entry, a string): the target calls it lbl_<address> or @n, a
    # compile calls it .rodata+0x...; the instruction still has to match, the name cannot.
    if re.match(r"(lbl_[0-9A-F]+|@\d+|\.(rodata|sdata2?|sbss2?|data|bss)(\+0x[0-9a-f]+)?)$", sym):
        return "<data>"
    return sym


def disassemble(obj, symbol):
    out = subprocess.run([OBJDUMP, "-dr", f"--disassemble={symbol}", obj],
                         capture_output=True, text=True)
    if out.returncode:
        sys.exit(f"trial.py: objdump failed on {obj}: {out.stderr.strip()}")
    names = text_symbols(obj)
    insns, lines = [], []
    for line in out.stdout.splitlines():
        m = re.match(r"\s*[0-9a-f]+:\t(?:[0-9a-f]{2} ){4}\t(.*)", line)
        r = re.match(r"\s*[0-9a-f]+: (R_PPC_\S+)\s+(\S+)", line)
        if m:
            # "b 40 <Foo+0x20>" -> "b <Foo+0x20>": the offset in .text differs between objects.
            text = re.sub(r"\b[0-9a-f]+ <", "<", " ".join(m.group(1).split()))
            insns.append(text)
            lines.append(text)
        elif r and insns:
            kind, sym = r.group(1), reloc_target(r.group(2), names)
            # The field a relocation fills holds the addend before linking, which differs between
            # objects: show the relocation's target in its place.
            text = insns[-1]
            if "REL24" in kind or "REL14" in kind:
                text = re.sub(r"\S+$", sym, text)
            else:
                text = re.sub(r"-?\w+(\(r\d+\))$", rf"{sym}\1", text)
                text = re.sub(r",-?\w+$", f",{sym}", text)
            insns[-1] = lines[-1] = text
    if not insns:
        sys.exit(f"trial.py: {symbol} not found in {obj}")
    return insns, lines


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("unit")
    ap.add_argument("symbol")
    ap.add_argument("--src")
    ap.add_argument("--version", default="GV4E69")
    args = ap.parse_args()

    unit = args.unit[len("src/"):] if args.unit.startswith("src/") else args.unit
    src = args.src or os.path.join("src", unit)
    cmd = compile_command(args.version, unit)
    trial_dir = os.path.join("build", "trial")
    os.makedirs(trial_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(src))[0]
    out = os.path.join(trial_dir, base + ".o")
    # Swap in the variant and a scratch output; the unit's own folder stays on the include path so
    # its local #includes still resolve from the scratch copy.
    for i, a in enumerate(cmd):
        if a == "-c":
            cmd[i + 1] = src
        elif a == "-o":
            cmd[i + 1] = out
        elif a == "--depfile":
            cmd[i + 1] = os.path.join(trial_dir, base + ".d")
    cmd[cmd.index("-c"):cmd.index("-c")] = ["-I", os.path.join("src", os.path.dirname(unit))]
    if subprocess.run(cmd).returncode:
        sys.exit("trial.py: compile failed")

    target = os.path.join("build", args.version, "obj", os.path.splitext(unit)[0] + ".o")
    t_insns, t_lines = disassemble(target, args.symbol)
    c_insns, c_lines = disassemble(out, args.symbol)
    score = difflib.SequenceMatcher(None, t_insns, c_insns, autojunk=False).ratio()
    same = t_insns == c_insns
    for line in difflib.unified_diff(t_lines, c_lines, "target", "trial", lineterm="", n=3):
        print(line)
    print(f"{args.symbol}: {len(c_insns)} instructions (target {len(t_insns)}), "
          f"{score * 100:.1f}% alike{', instructions identical' if same else ''}")
    if same and t_lines != c_lines:
        print("relocations differ: check the symbols above")
    sys.exit(0 if same else 1)


if __name__ == "__main__":
    main()
