#!/usr/bin/env python3

###
# Generates build files for the project.
# This file also includes the project configuration,
# such as compiler flags and the object matching status.
#
# Usage:
#   python3 configure.py
#   ninja
#
# Append --help to see available options.
###

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

from tools.project import (
    Object,
    ProgressCategory,
    ProjectConfig,
    calculate_progress,
    generate_build,
    is_windows,
)

# Game versions
DEFAULT_VERSION = 0
VERSIONS = [
    "GV4E69",  # 0: USA
]

parser = argparse.ArgumentParser()
parser.add_argument(
    "mode",
    choices=["configure", "progress"],
    default="configure",
    help="script mode (default: configure)",
    nargs="?",
)
parser.add_argument(
    "-v",
    "--version",
    choices=VERSIONS,
    type=str.upper,
    default=VERSIONS[DEFAULT_VERSION],
    help="version to build",
)
parser.add_argument(
    "--build-dir",
    metavar="DIR",
    type=Path,
    default=Path("build"),
    help="base build directory (default: build)",
)
parser.add_argument(
    "--binutils",
    metavar="BINARY",
    type=Path,
    help="path to binutils (optional)",
)
parser.add_argument(
    "--compilers",
    metavar="DIR",
    type=Path,
    help="path to compilers (optional)",
)
parser.add_argument(
    "--map",
    action="store_true",
    help="generate map file(s)",
)
parser.add_argument(
    "--debug",
    action="store_true",
    help="build with debug info (non-matching)",
)
if not is_windows():
    parser.add_argument(
        "--wrapper",
        metavar="BINARY",
        type=Path,
        help="path to wibo or wine (optional)",
    )
parser.add_argument(
    "--dtk",
    metavar="BINARY | DIR",
    type=Path,
    help="path to decomp-toolkit binary or source (optional)",
)
parser.add_argument(
    "--objdiff",
    metavar="BINARY | DIR",
    type=Path,
    help="path to objdiff-cli binary or source (optional)",
)
parser.add_argument(
    "--sjiswrap",
    metavar="EXE",
    type=Path,
    help="path to sjiswrap.exe (optional)",
)
parser.add_argument(
    "--ninja",
    metavar="BINARY",
    type=Path,
    help="path to ninja binary (optional)",
)
parser.add_argument(
    "--verbose",
    action="store_true",
    help="print verbose output",
)
parser.add_argument(
    "--non-matching",
    dest="non_matching",
    action="store_true",
    help="builds equivalent (but non-matching) or modded objects",
)
parser.add_argument(
    "--warn",
    dest="warn",
    type=str,
    choices=["all", "off", "error"],
    help="how to handle warnings",
)
parser.add_argument(
    "--no-progress",
    dest="progress",
    action="store_false",
    help="disable progress calculation",
)
args = parser.parse_args()

config = ProjectConfig()
config.version = str(args.version)
version_num = VERSIONS.index(config.version)

# Apply arguments
config.build_dir = args.build_dir
config.dtk_path = args.dtk
config.objdiff_path = args.objdiff
config.binutils_path = args.binutils
config.compilers_path = args.compilers
config.generate_map = args.map
config.non_matching = args.non_matching
config.sjiswrap_path = args.sjiswrap
config.ninja_path = args.ninja
config.progress = args.progress
if not is_windows():
    config.wrapper = args.wrapper
# Don't build asm unless we're --non-matching
if not config.non_matching:
    config.asm_dir = None

# Tool versions
config.binutils_tag = "2.42-2"
config.compilers_tag = "20251118"
config.dtk_tag = "v1.8.3"
config.objdiff_tag = "v3.6.1"
config.sjiswrap_tag = "v1.2.2"
config.wibo_tag = "1.0.3"

# Project
config.config_path = Path("config") / config.version / "config.yml"
config.check_sha_path = Path("config") / config.version / "build.sha1"
config.asflags = [
    "-mgekko",
    "--strip-local-absolute",
    "-I include",
    f"-I build/{config.version}/include",
    f"--defsym BUILD_VERSION={version_num}",
]
# The DOL was linked by SN Systems' ngcld, which reaches all small data (.sdata2 included) through
# r13; CodeWarrior's mwld cannot reproduce that (docs/compiler.md "Linker"). Every ngcld in the
# compilers package links the current objects to the exact DOL; 3.9.3's is the one that reads
# response files. The link script is config/<VERSION>/ldscript.tpl (a GNU-style script).
config.sn_linker = "ProDG/3.9.3"
config.ldflags = []

# Use for any additional files that should cause a re-configure when modified
config.reconfig_deps = []

# Optional numeric ID for decomp.me preset
# Can be overridden in libraries or objects
config.scratch_preset_id = None

# Base flags, common to most GC/Wii games.
# Generally leave untouched, with overrides added below.
cflags_base = [
    "-nodefaults",
    "-proc gekko",
    "-align powerpc",
    "-enum int",
    "-fp hardware",
    "-Cpp_exceptions off",
    "-O4,p",
    "-inline auto",
    '-pragma "cats off"',
    '-pragma "warn_notinlined off"',
    "-maxerrors 1",
    "-nosyspath",
    "-RTTI off",
    "-fp_contract on",
    "-str reuse",
    "-multibyte",  # For Wii compilers, replace with `-enc SJIS`
    "-i include",
    f"-i build/{config.version}/include",
    f"-DBUILD_VERSION={version_num}",
    f"-DVERSION_{config.version}",
]

# Debug flags
if args.debug:
    # Or -sym dwarf-2 for Wii compilers
    cflags_base.extend(["-sym on", "-DDEBUG=1"])
else:
    cflags_base.append("-DNDEBUG=1")

# Warning flags
if args.warn == "all":
    cflags_base.append("-W all")
elif args.warn == "off":
    cflags_base.append("-W off")
elif args.warn == "error":
    cflags_base.append("-W error")

# Metrowerks library flags
cflags_runtime = [
    *cflags_base,
    "-use_lmw_stmw on",
    "-str reuse,pool,readonly",
    "-gccinc",
    "-common off",
    "-inline auto",
]

# REL flags
cflags_rel = [
    *cflags_base,
    "-sdata 0",
    "-sdata2 0",
]

config.linker_version = "GC/1.3.2"


# Nintendo's Dolphin SDK libraries were prebuilt by Nintendo with CodeWarrior GC/1.2.5n; EA linked
# them with SN's ngcld. The DOL carries the 2004 SDK build strings with OS "May 21 2004" (Patch 1,
# SDK_REVISION 1; docs/sdk.md). Sources and flags come from emoose/re4, which took them from
# doldecomp/dolsdk2004 (its Makefile's release flags; see CREDITS.md). Headers: include/dolphin/,
# include/libc/, private ones in src/dolphin/.
SDK_MW_VERSION = "GC/1.2.5n"
cflags_sdk = [
    "-nodefaults",
    "-proc gekko",
    "-fp hard",
    "-Cpp_exceptions off",
    "-enum int",
    "-char unsigned",
    "-warn pragmas",
    "-requireprotos",
    "-pragma 'cats off'",
    "-O4,p",
    "-inline auto",
    "-I-",
    "-i include",
    "-i include/libc",
    "-i src/dolphin",
    "-D__GEKKO__",
    "-DSDK_REVISION=1",
]
# Per-unit deviations from cflags_sdk (the same as dolsdk2004's Makefile). Each replaces a base
# flag: MWCC keeps the first -O level it sees, so appending one would have no effect.
SDK_CFLAG_OVERRIDES: Dict[str, Dict[str, str]] = {
    **{
        f"dolphin/dvd/{name}.c": {"-char unsigned": "-char signed"}
        for name in ["dvdlow", "dvdfs", "dvd", "dvdqueue", "dvderror", "dvdidutils", "dvdFatal", "fstload"]
    },
    "dolphin/mtx/mtx.c": {"-char unsigned": "-char signed"},
    "dolphin/mtx/mtx44.c": {"-char unsigned": "-char signed"},
    "dolphin/card/CARDOpen.c": {"-char unsigned": "-char signed"},
    "dolphin/card/CARDRename.c": {"-char unsigned": "-char signed"},
    "dolphin/exi/EXIBios.c": {"-O4,p": "-O3,p"},
    "dolphin/os/__ppc_eabi_init.c": {"-O4,p": "-O4,p -opt nopeephole"},
}


def sdk_cflags(unit: str) -> List[str]:
    repl = SDK_CFLAG_OVERRIDES.get(unit, {})
    return [repl.get(flag, flag) for flag in cflags_sdk]


# SN's linker dead-stripped the SDK objects symbol by symbol; tools/strip_unused.py removes the
# same symbols from ours, keeping what symbols.txt names inside the unit's split ranges.
def SdkObject(status: bool, unit: str) -> Object:
    return Object(
        status,
        unit,
        cflags=sdk_cflags(unit),
        post_build=[f"$python tools/strip_unused.py --unit {unit} {{out}}"],
        post_build_implicit=[
            Path("tools/strip_unused.py"),
            Path("config") / config.version / "splits.txt",
            Path("config") / config.version / "symbols.txt",
        ],
    )


def DolphinLib(lib_name: str, objects: List[Object], mw_version: str = SDK_MW_VERSION) -> Dict[str, Any]:
    return {
        "lib": lib_name,
        "mw_version": mw_version,
        "cflags": cflags_sdk,
        "mwcc_depflag": "-MD",  # with -I- the default -MMD records no header dependencies
        "progress_category": "sdk",
        "objects": objects,
    }


# EA's SND audio library (libsndgcz.a, "SND 9.02.04", Dec 2004), built by EA with SN ProDG as C++.
# Sources come from dbalatoni13/nfsmw (CC0), whose SND is a later build of the same library
# (rwaudiocore 2.09.00); its flags reproduce MVP's code unchanged. See CREDITS.md.
cflags_snd = [
    "-O2",
    "-G0",
    "-fno-strength-reduce",
    "-fno-strict-aliasing",
    "-ffast-math",
    "-mps-float",
    "-x c++",
    "-I include",
    "-I include/libc",
    "-I src",
    "-DEA_PLATFORM_GAMECUBE",
    "-DGEKKO",
]


def SndObject(status: bool, unit: str) -> Object:
    return Object(status, unit)


def SndLib(objects: List[Object]) -> Dict[str, Any]:
    return {
        "lib": "snd",
        "mw_version": PRODG_VERSION,
        "cflags": cflags_snd,
        "progress_category": "ealib",
        "objects": objects,
    }


# Helper function for REL script objects
def Rel(lib_name: str, objects: List[Object]) -> Dict[str, Any]:
    return {
        "lib": lib_name,
        "mw_version": "GC/1.3.2",
        "cflags": cflags_rel,
        "progress_category": "game",
        "objects": objects,
    }


# SN Systems ProDG (GCC 2.95) builds EA's game code and SN's runtime libraries (docs/compiler.md).
# Objects with this mw_version use the prodg_cc rule (ngccc.exe) in tools/project.py.
PRODG_VERSION = "ProDG/3.9.3"
# Game code flags, from the first exact matches (docs/compiler.md "ProDG version and flags").
cflags_game = ["-O2", "-G0", "-ffloat-store", "-fno-strength-reduce"]
# geomlib (the first game unit, 2026-09-30) needs -Os: at -O2 the register choices and a store
# order differ, and its loops are strength-reduced (ctr loops, pointer steps), so no
# -fno-strength-reduce. Which flags the rest of the game code uses is still open.
cflags_game_os = ["-Os", "-G0", "-ffloat-store"]


# EA's game code, C++ under C:/mvp2004/source/ (src/ mirrors the tree below source/). A class's
# vtable stays in the DOL's .data asm and the object links against it (tools/linkonce_data.py).
# GCC 2.95 also emits every inline member of a class in the file that holds its vtable; ngcld
# dropped the ones nothing calls, as it did in SN's libraries, so strip_unused --gcc runs too.
def GameObject(status: bool, unit: str) -> Object:
    return Object(
        status,
        unit,
        post_build=[
            f"$python tools/linkonce_data.py {{out}}",
            f"$python tools/strip_unused.py --gcc --unit {unit} {{out}}",
        ],
        post_build_implicit=[
            Path("tools/strip_unused.py"),
            Path("tools/linkonce_data.py"),
            Path("config") / config.version / "splits.txt",
            Path("config") / config.version / "symbols.txt",
        ],
    )


def GameLib(lib_name: str, objects: List[Object]) -> Dict[str, Any]:
    return {
        "lib": lib_name,
        "mw_version": PRODG_VERSION,
        "cflags": [*cflags_game_os, "-I src"],
        "progress_category": "game",
        "objects": objects,
    }


# SN ProDG's libgcc.a: GCC 2.95.3 libgcc2.c, one L_* section per object (src/libgcc/, from
# emoose/re4). __clz_tab sits in .sdata2 in each division object, hence the large -G.
cflags_libgcc = ["-O2", "-G 1024", "-I src/libgcc"]
# __main is built with SN's crt, without small data: `initialized` is plain .bss reached with
# lis/lwz (as in re4).
cflags_crt = ["-O2", "-G 0", "-I src/libgcc"]


# SN ProDG's libc.a: newlib 1.8.2 with SN's changes (src/libc/, from emoose/re4). As in re4:
# -fno-common, and <stdarg.h> from ProDG's own include directory (include/prodg/).
cflags_libc = ["-O2", "-fno-common", "-isystem include/prodg"]


# SN ProDG's libsn.a, the C parts (src/libsn/, from emoose/re4): no small data and no common
# symbols, so FSasync's uninitialised globals sit in its own .bss in declaration order.
cflags_libsn = ["-O2", "-G 0", "-fno-common"]


# SN ProDG's libm.a: newlib 1.8.2's fdlibm (src/libm/), each source compiled through a one-line
# wrapper: re4's files as C++ (.cpp), the five re4 lacks as C (.c), which keeps their unreferenced
# constants in .sdata2 as SN's own C build did (docs/sdk.md). Flags as re4 found them: literal pools in .sdata (-msafe-sda),
# tables up to two_over_pi in small data (-G), fabs() a real call (-fno-builtin), and
# -mstrict-align for the float trig functions' indexed loads.
cflags_libm = ["-O2", "-mfast-cast", "-msafe-sda", "-G 1024", "-fno-builtin", "-mstrict-align"]


# ngcld dead-stripped SN's library objects like the SDK's; strip_unused --gcc keeps what
# symbols.txt names inside the unit's split ranges.
def SnObject(status: bool, unit: str, **options: Any) -> Object:
    return Object(
        status,
        unit,
        **options,
        post_build=[f"$python tools/strip_unused.py --gcc --unit {unit} {{out}}"],
        post_build_implicit=[
            Path("tools/strip_unused.py"),
            Path("config") / config.version / "splits.txt",
            Path("config") / config.version / "symbols.txt",
        ],
    )


def SnLib(lib_name: str, cflags: List[str], objects: List[Object]) -> Dict[str, Any]:
    return {
        "lib": lib_name,
        "mw_version": PRODG_VERSION,
        "cflags": cflags,
        "progress_category": "sdk",
        "objects": objects,
    }


Matching = True                   # Object matches and should be linked
NonMatching = False               # Object does not match and should not be linked
Equivalent = config.non_matching  # Object should be linked when configured with --non-matching


# Object is only matching for specific versions
def MatchingFor(*versions):
    return config.version in versions


config.warn_missing_config = True
config.warn_missing_source = False
config.libs = [
    GameLib(
        "geomlib",
        [
            GameObject(NonMatching, "common/geomlib/geomcone.cpp"),
            GameObject(Matching, "common/geomlib/geomgroup.cpp"),
        ],
    ),
    DolphinLib(
        "ai",
        [
            SdkObject(Matching, "dolphin/ai/ai.c"),
        ],
    ),
    DolphinLib(
        "amcstubs",
        [
            SdkObject(Matching, "dolphin/amcstubs/AmcExi2Stubs.c"),
        ],
    ),
    DolphinLib(
        "ar",
        [
            SdkObject(Matching, "dolphin/ar/ar.c"),
            SdkObject(Matching, "dolphin/ar/arq.c"),
        ],
    ),
    DolphinLib(
        "ax",
        [
            SdkObject(Matching, "dolphin/ax/AX.c"),
            SdkObject(Matching, "dolphin/ax/AXAlloc.c"),
            SdkObject(Matching, "dolphin/ax/AXAux.c"),
            SdkObject(Matching, "dolphin/ax/AXCL.c"),
            SdkObject(Matching, "dolphin/ax/AXOut.c"),
            SdkObject(Matching, "dolphin/ax/AXSPB.c"),
            SdkObject(Matching, "dolphin/ax/AXVPB.c"),
            SdkObject(Matching, "dolphin/ax/AXProf.c"),
            SdkObject(Matching, "dolphin/ax/AXComp.c"),
            SdkObject(Matching, "dolphin/ax/DSPCode.c"),
        ],
    ),
    DolphinLib(
        "base",
        [
            SdkObject(Matching, "dolphin/base/PPCArch.c"),
        ],
    ),
    DolphinLib(
        "card",
        [
            SdkObject(Matching, "dolphin/card/CARDBios.c"),
            SdkObject(Matching, "dolphin/card/CARDBlock.c"),
            SdkObject(Matching, "dolphin/card/CARDDir.c"),
            SdkObject(Matching, "dolphin/card/CARDCheck.c"),
            SdkObject(Matching, "dolphin/card/CARDMount.c"),
            SdkObject(Matching, "dolphin/card/CARDFormat.c"),
            SdkObject(Matching, "dolphin/card/CARDOpen.c"),
            SdkObject(Matching, "dolphin/card/CARDCreate.c"),
            SdkObject(Matching, "dolphin/card/CARDRead.c"),
            SdkObject(Matching, "dolphin/card/CARDWrite.c"),
            SdkObject(Matching, "dolphin/card/CARDDelete.c"),
            SdkObject(Matching, "dolphin/card/CARDStat.c"),
            SdkObject(Matching, "dolphin/card/CARDRename.c"),
            SdkObject(Matching, "dolphin/card/CARDNet.c"),
            SdkObject(Matching, "dolphin/card/CARDUnlock.c"),
            SdkObject(Matching, "dolphin/card/CARDRdwr.c"),
            SdkObject(Matching, "dolphin/card/CARDStatEx.c"),
        ],
    ),
    DolphinLib(
        "db",
        [
            SdkObject(Matching, "dolphin/db/db.c"),
        ],
    ),
    DolphinLib(
        "dsp",
        [
            SdkObject(Matching, "dolphin/dsp/dsp.c"),
            SdkObject(Matching, "dolphin/dsp/dsp_debug.c"),
            SdkObject(Matching, "dolphin/dsp/dsp_task.c"),
        ],
    ),
    DolphinLib(
        "dvd",
        [
            SdkObject(Matching, "dolphin/dvd/dvdfs.c"),
            SdkObject(Matching, "dolphin/dvd/dvd.c"),
            SdkObject(Matching, "dolphin/dvd/dvdqueue.c"),
            SdkObject(Matching, "dolphin/dvd/dvderror.c"),
            SdkObject(Matching, "dolphin/dvd/dvdidutils.c"),
            SdkObject(Matching, "dolphin/dvd/dvdFatal.c"),
            SdkObject(Matching, "dolphin/dvd/fstload.c"),
            SdkObject(Matching, "dolphin/dvd/dvdlow.c"),
        ],
    ),
    DolphinLib(
        "exi",
        [
            SdkObject(Matching, "dolphin/exi/EXIBios.c"),
            SdkObject(Matching, "dolphin/exi/EXIUart.c"),
        ],
    ),
    DolphinLib(
        "gx",
        [
            SdkObject(Matching, "dolphin/gx/GXInit.c"),
            SdkObject(Matching, "dolphin/gx/GXFifo.c"),
            SdkObject(Matching, "dolphin/gx/GXAttr.c"),
            SdkObject(Matching, "dolphin/gx/GXMisc.c"),
            SdkObject(Matching, "dolphin/gx/GXGeometry.c"),
            SdkObject(Matching, "dolphin/gx/GXFrameBuf.c"),
            SdkObject(Matching, "dolphin/gx/GXLight.c"),
            SdkObject(Matching, "dolphin/gx/GXTexture.c"),
            SdkObject(Matching, "dolphin/gx/GXBump.c"),
            SdkObject(Matching, "dolphin/gx/GXTev.c"),
            SdkObject(Matching, "dolphin/gx/GXPixel.c"),
            SdkObject(Matching, "dolphin/gx/GXDisplayList.c"),
            SdkObject(Matching, "dolphin/gx/GXTransform.c"),
            SdkObject(Matching, "dolphin/gx/GXPerf.c"),
        ],
    ),
    DolphinLib(
        "mtx",
        [
            SdkObject(Matching, "dolphin/mtx/mtx.c"),
            SdkObject(Matching, "dolphin/mtx/mtxvec.c"),
            SdkObject(Matching, "dolphin/mtx/mtx44.c"),
        ],
    ),
    DolphinLib(
        "os",
        [
            SdkObject(Matching, "dolphin/os/OS.c"),
            SdkObject(Matching, "dolphin/os/OSAlarm.c"),
            SdkObject(Matching, "dolphin/os/OSAlloc.c"),
            SdkObject(Matching, "dolphin/os/OSArena.c"),
            SdkObject(Matching, "dolphin/os/OSAudioSystem.c"),
            SdkObject(Matching, "dolphin/os/OSCache.c"),
            SdkObject(Matching, "dolphin/os/OSContext.c"),
            SdkObject(Matching, "dolphin/os/OSError.c"),
            SdkObject(Matching, "dolphin/os/OSExec.c"),
            SdkObject(Matching, "dolphin/os/OSFont.c"),
            SdkObject(Matching, "dolphin/os/OSInterrupt.c"),
            SdkObject(Matching, "dolphin/os/OSLink.c"),
            SdkObject(Matching, "dolphin/os/OSMessage.c"),
            SdkObject(Matching, "dolphin/os/OSMemory.c"),
            SdkObject(Matching, "dolphin/os/OSMutex.c"),
            SdkObject(Matching, "dolphin/os/OSReboot.c"),
            SdkObject(Matching, "dolphin/os/OSReset.c"),
            SdkObject(Matching, "dolphin/os/OSResetSW.c"),
            SdkObject(Matching, "dolphin/os/OSRtc.c"),
            SdkObject(Matching, "dolphin/os/OSSync.c"),
            SdkObject(Matching, "dolphin/os/OSThread.c"),
            SdkObject(Matching, "dolphin/os/OSTime.c"),
            SdkObject(Matching, "dolphin/os/__ppc_eabi_init.c"),
        ],
    ),
    DolphinLib(
        "pad",
        [
            SdkObject(Matching, "dolphin/pad/Padclamp.c"),
            SdkObject(Matching, "dolphin/pad/Pad.c"),
        ],
    ),
    DolphinLib(
        "si",
        [
            SdkObject(Matching, "dolphin/si/SIBios.c"),
            SdkObject(Matching, "dolphin/si/SISamplingRate.c"),
        ],
    ),
    DolphinLib(
        "vi",
        [
            SdkObject(Matching, "dolphin/vi/vi.c"),
        ],
    ),
    # The VM library was built with a newer CodeWarrior than the rest of the SDK: its prologues
    # save LR after the stack update. GC/1.3 to 2.7 all give the same code; 2.0 is used.
    DolphinLib(
        "vm",
        [
            SdkObject(Matching, "dolphin/vm/VM.c"),
            SdkObject(Matching, "dolphin/vm/VMPageReplacement.c"),
            SdkObject(Matching, "dolphin/vm/VMMapping.c"),
        ],
        mw_version="GC/2.0",
    ),
    DolphinLib(
        "vmbase",
        [
            SdkObject(Matching, "dolphin/vmbase/VMBase.c"),
        ],
        mw_version="GC/2.0",
    ),
    DolphinLib(
        "odemustubs",
        [
            SdkObject(Matching, "dolphin/odemustubs/DebuggerDriver.c"),
        ],
    ),
    SndLib(
        [
            SndObject(Matching, "snd/cmn/saems.c"),
            SndObject(Matching, "snd/cmn/salloc.c"),
            SndObject(Matching, "snd/cmn/sballoc.c"),
            SndObject(Matching, "snd/cmn/sbhdrcpy.c"),
            SndObject(Matching, "snd/cmn/sbhdrsze.c"),
            SndObject(Matching, "snd/cmn/sbplay.c"),
            SndObject(Matching, "snd/cmn/sbvalid.c"),
            SndObject(Matching, "snd/cmn/scheckpo.c"),
            SndObject(Matching, "snd/cmn/smemcpy.c"),
            SndObject(Matching, "snd/cmn/smemman.c"),
            SndObject(Matching, "snd/cmn/spitch.c"),
            SndObject(Matching, "snd/cmn/sstgetpv.c"),
            SndObject(Matching, "snd/cmn/sctrldry.cpp"),
            SndObject(Matching, "snd/cmn/sgetpvol.c"),
            SndObject(Matching, "snd/cmn/spatkey.c"),
            SndObject(Matching, "snd/cmn/sattrdef.c"),
        ]
    ),
    SnLib(
        "libsn",
        cflags_libsn,
        [
            Object(Matching, "libsn/FSasync.c"),
            Object(Matching, "libsn/sndvd.c"),
            Object(Matching, "libsn/dummy.c"),
        ],
    ),
    SnLib(
        "libc",
        cflags_libc,
        [
            SnObject(Matching, "libc/fclose.c"),
            SnObject(Matching, "libc/fflush.c"),
            SnObject(Matching, "libc/fopen.c"),
            SnObject(Matching, "libc/fprintf.c"),
            SnObject(Matching, "libc/fseek.c"),
            SnObject(Matching, "libc/fwalk.c"),
            SnObject(Matching, "libc/makebuf.c"),
            SnObject(Matching, "libc/printf.c"),
            SnObject(Matching, "libc/refill.c"),
            SnObject(Matching, "libc/sprintf.c"),
            SnObject(Matching, "libc/sscanf.c"),
            SnObject(Matching, "libc/stdio.c"),
            SnObject(Matching, "libc/vfscanf.c"),
            SnObject(Matching, "libc/vprintf.c"),
            SnObject(Matching, "libc/vsprintf.c"),
            SnObject(Matching, "libc/assert.c"),
            SnObject(Matching, "libc/atexit.c"),
            SnObject(Matching, "libc/atof.c"),
            SnObject(Matching, "libc/atoi.c"),
            SnObject(Matching, "libc/bsearch.c"),
            SnObject(Matching, "libc/exit.c"),
            SnObject(Matching, "libc/mbtowc_r.c"),
            SnObject(Matching, "libc/qsort.c"),
            SnObject(Matching, "libc/rand.c"),
            SnObject(Matching, "libc/sn_malloc.c"),
            SnObject(Matching, "libc/strtod2.c"),
            SnObject(Matching, "libc/strtoul.c"),
            SnObject(Matching, "libc/memcmp.c"),
            SnObject(Matching, "libc/memcpy.c"),
            SnObject(Matching, "libc/memmove.c"),
            SnObject(Matching, "libc/memset.c"),
            SnObject(Matching, "libc/strcasecmp.c"),
            SnObject(Matching, "libc/strcat.c"),
            SnObject(Matching, "libc/strchr.c"),
            SnObject(Matching, "libc/strcmp.c"),
            SnObject(Matching, "libc/strcpy.c"),
            SnObject(Matching, "libc/strlen.c"),
            SnObject(Matching, "libc/strlwr.c"),
            SnObject(Matching, "libc/strncmp.c"),
            SnObject(Matching, "libc/strncpy.c"),
            SnObject(Matching, "libc/strrchr.c"),
            SnObject(Matching, "libc/strstr.c"),
            SnObject(Matching, "libc/strtok.c"),
            SnObject(Matching, "libc/strtok_r.c"),
            SnObject(Matching, "libc/vfprintf.c"),
            SnObject(Matching, "libc/vfiprintf.c"),
            SnObject(Matching, "libc/strtol.c"),
            SnObject(Matching, "libc/isdigit.c"),
            SnObject(Matching, "libc/isspace.c"),
            # errno.c's `int errno` is a common symbol: the linker puts it last in .sbss.
            SnObject(Matching, "libc/errno.c", cflags=["-O2", "-isystem include/prodg"]),
            SnObject(Matching, "libc/locale.c"),
            SnObject(Matching, "libc/math_support.c"),
            SnObject(Matching, "libc/closer.c"),
            SnObject(Matching, "libc/fstatr.c"),
            SnObject(Matching, "libc/lseekr.c"),
            SnObject(Matching, "libc/openr.c"),
            SnObject(Matching, "libc/readr.c"),
            SnObject(Matching, "libc/writer.c"),
            SnObject(Matching, "libc/fiprintf.c"),
            SnObject(Matching, "libc/flags.c"),
            SnObject(Matching, "libc/fread.c"),
            SnObject(Matching, "libc/ungetc.c"),
            SnObject(Matching, "libc/abort.c"),
            SnObject(Matching, "libc/memchr.c"),
            SnObject(Matching, "libc/tolower.c"),
        ],
    ),
    SnLib(
        "libm",
        cflags_libm,
        [
            Object(Matching, "libm/e_exp.c"),
            Object(Matching, "libm/e_log.cpp"),
            Object(Matching, "libm/e_sqrt.cpp"),
            Object(Matching, "libm/s_ceil.c"),
            Object(Matching, "libm/s_cos.cpp"),
            Object(Matching, "libm/s_fabs.cpp"),
            Object(Matching, "libm/s_floor.cpp"),
            Object(Matching, "libm/s_sin.c"),
            Object(Matching, "libm/ef_acos.cpp"),
            Object(Matching, "libm/ef_asin.cpp"),
            Object(Matching, "libm/ef_atan2.cpp"),
            Object(Matching, "libm/ef_log.c"),
            Object(Matching, "libm/ef_sqrt.cpp"),
            Object(Matching, "libm/sf_atan.cpp"),
            Object(Matching, "libm/sf_ceil.c"),
            Object(Matching, "libm/sf_cos.cpp"),
            Object(Matching, "libm/sf_fabs.cpp"),
            Object(Matching, "libm/sf_floor.cpp"),
            Object(Matching, "libm/sf_sin.cpp"),
            Object(Matching, "libm/sf_tan.cpp"),
            Object(Matching, "libm/k_cos.cpp"),
            Object(Matching, "libm/k_sin.cpp"),
            Object(Matching, "libm/e_rem_pio2.cpp"),
            Object(Matching, "libm/kf_cos.cpp"),
            Object(Matching, "libm/kf_sin.cpp"),
            Object(Matching, "libm/kf_tan.cpp"),
            Object(Matching, "libm/ef_rem_pio2.cpp"),
            Object(Matching, "libm/k_rem_pio2.cpp"),
            Object(Matching, "libm/kf_rem_pio2.cpp"),
            Object(Matching, "libm/s_scalbn.cpp"),
            Object(Matching, "libm/sf_scalbn.cpp"),
            Object(Matching, "libm/s_copysign.cpp"),
            Object(Matching, "libm/sf_copysign.cpp"),
        ],
    ),
    SnLib(
        "libgcc",
        cflags_libgcc,
        [
            Object(Matching, "libgcc/__main.c", cflags=cflags_crt),
            Object(Matching, "libgcc/_ashldi3.c"),
            Object(Matching, "libgcc/_ashrdi3.c"),
            Object(Matching, "libgcc/_divdi3.c"),
            SnObject(Matching, "libgcc/_eh.c", cflags=cflags_crt),
            Object(Matching, "libgcc/_exit.c"),
            Object(Matching, "libgcc/_lshrdi3.c"),
            Object(Matching, "libgcc/_moddi3.c"),
            Object(Matching, "libgcc/_pure.c"),
            Object(Matching, "libgcc/_udivdi3.c"),
            Object(Matching, "libgcc/_umoddi3.c"),
            # Hand-written assembly in GCC's source; assembled, not compiled.
            Object(Matching, "libgcc/eabi.s"),
        ],
    ),
]


# Optional callback to adjust link order. This can be used to add, remove, or reorder objects.
# This is called once per module, with the module ID and the current link order.
#
# For example, this adds "dummy.c" to the end of the DOL link order if configured with --non-matching.
# "dummy.c" *must* be configured as a Matching (or Equivalent) object in order to be linked.
def link_order_callback(module_id: int, objects: List[str]) -> List[str]:
    # Don't modify the link order for matching builds
    if not config.non_matching:
        return objects
    if module_id == 0:  # DOL
        return objects + ["dummy.c"]
    return objects


# Uncomment to enable the link order callback.
# config.link_order_callback = link_order_callback


# Optional extra categories for progress tracking
# Adjust as desired for your project
config.progress_categories = [
    ProgressCategory("game", "Game Code"),
    ProgressCategory("sdk", "SDK Code"),
    ProgressCategory("ealib", "EA Libraries"),
]
config.progress_each_module = args.verbose
# Optional extra arguments to `objdiff-cli report generate`
config.progress_report_args = [
    # Marks relocations as mismatching if the target value is different
    # Default is "functionRelocDiffs=none", which is most lenient
    # "--config functionRelocDiffs=data_value",
]

if args.mode == "configure":
    # Write build.ninja and objdiff.json
    generate_build(config)
elif args.mode == "progress":
    # Print progress information
    calculate_progress(config)
else:
    sys.exit("Unknown mode: " + args.mode)
