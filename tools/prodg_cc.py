#!/usr/bin/env python3
"""Compile one C or C++ file with SN Systems ProDG (GCC 2.95 for GameCube).

Runs the three stages SN's driver ngccc.exe runs (cpp, cc1/cc1plus, NgcAs) with the same arguments
ngccc passes them (read from `ngccc -v`), instead of ngccc itself. ngccc writes its intermediate
files into the current directory under short random names (strXXXX.TMP, memXXXX.TMP), so parallel
compiles collide and hang; it also needs SN_NGC_PATH. Here the intermediates sit next to the object.

usage: prodg_cc.py [--wrapper wibo] --dir build/compilers/ProDG/3.9.3 [--depfile x.d]
                   [gcc flags] -c <source> -o <object>

Preprocessor flags (-I, -D, -U, -isystem, -include, -nostdinc, -Wp,...) go to cpp; the rest to cc1.
"""
import os
import subprocess
import sys

# What ngccc 3.9.3 passes to cpp besides the user's flags (ngccc -v).
CPP_COMMON = [
    "-D__GNUC__=2", "-D__GNUC_MINOR__=95", "-D__NOASMPP__",
]
CPP_TARGET = [
    "-DPPC", "-D__PPC__", "-D__PPC", "-Acpu(powerpc)", "-Amachine(powerpc)", "-D__CHAR_UNSIGNED__",
    "-D_BIG_ENDIAN", "-D__BIG_ENDIAN__", "-Amachine(bigendian)", "-D__PTRDIFF_TYPE__=int",
    "-D__SIZE_TYPE__=unsigned", "-D_CALL_SYSV", "-DSN_TARGET_NGC", "-D__SN__",
]
CPP_C = ["-lang-c"]
CPP_C_TAIL = ["-D_LANGUAGE_C", "-D__LANGUAGE_C", "-DLANGUAGE_C"]
CPP_CXX = ["-D__GNUG__=2", "-lang-c++", "-D__cplusplus"]
CPP_CXX_TAIL = ["-D_LANGUAGE_C_PLUS_PLUS", "-D__LANGUAGE_C_PLUS_PLUS"]

CPP_WITH_ARG = ("-I", "-D", "-U", "-isystem", "-include")


def run(cmd):
    r = subprocess.run(cmd)
    if r.returncode:
        sys.exit(r.returncode)


def main():
    args = sys.argv[1:]
    wrapper, cdir, depfile, src, out, lang = [], None, None, None, None, None
    cpp_flags, cc1_flags = [], []
    i = 0
    while i < len(args):
        a = args[i]
        nxt = args[i + 1] if i + 1 < len(args) else None
        if a == "--wrapper":
            wrapper = [nxt]; i += 2; continue
        if a == "--dir":
            cdir = nxt; i += 2; continue
        if a == "--depfile":
            depfile = nxt; i += 2; continue
        if a == "-c":
            src = nxt; i += 2; continue
        if a == "-o":
            out = nxt; i += 2; continue
        if a == "-x":  # the driver's language override (EA's SND compiles its .c files as C++)
            lang = nxt; i += 2; continue
        if a in CPP_WITH_ARG:
            cpp_flags += [a, nxt]; i += 2; continue
        if a.startswith(("-I", "-D", "-U")) or a == "-nostdinc":
            cpp_flags.append(a); i += 1; continue
        if a.startswith("-Wp,"):
            cpp_flags += a[4:].split(","); i += 1; continue
        cc1_flags.append(a); i += 1
    if not (cdir and src and out):
        sys.exit(__doc__)
    if lang:
        cxx = lang == "c++"
    else:
        cxx = os.path.splitext(src)[1].lower() in (".cpp", ".cc", ".cxx", ".cp")
    optimize = any(f.startswith("-O") and f != "-O0" for f in cc1_flags)
    base = os.path.splitext(out)[0]
    i_file, s_file = base + ".i", base + ".s"
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)

    cpp = [*wrapper, os.path.join(cdir, "CPP.exe")]
    cpp += (["-D__OPTIMIZE__"] if optimize else []) + CPP_COMMON
    cpp += (CPP_CXX if cxx else CPP_C) + CPP_TARGET + (CPP_CXX_TAIL if cxx else CPP_C_TAIL)
    if depfile:
        cpp += ["-MMD", depfile]
    cpp += cpp_flags + [src, "-o", i_file]
    run(cpp)
    run([*wrapper, os.path.join(cdir, "cc1plus.exe" if cxx else "cc1.exe"), *cc1_flags, "-quiet", i_file, "-o", s_file])
    run([*wrapper, os.path.join(cdir, "NgcAs.exe"), s_file, "-o", out])


if __name__ == "__main__":
    main()
