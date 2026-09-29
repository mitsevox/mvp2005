# Leaked names (discovery step 5)

Status 2026-09-29: what the binary itself says about EA's names, how much of it there is, and what
each kind is good for. All of it is T1 evidence (EA's own text in the binary, `agents/pass.md`
"Evidence"). Counts are measured with dtk's asm (`ninja` first) and the DOL's strings.

## Summary

| Kind | Count | Names what |
|---|---|---|
| Source paths (`__FILE__` in asserts and errors) | 89 EA paths, 63 `.cpp` referenced from game code | the unit (file) a function belongs to |
| Class type IDs (djb2 of the class name) | 123 getters, 190 other uses, 126 names | a class's vtable, its `GetClassName`/type-ID getters, and type checks |
| Named attributes (EA's reflection) | about 1,800 registration calls, 2,950 CamelCase names | struct members (with offset and range), script and UI hooks |
| `Class::Method` in messages | 25 strings in 13 functions | the function that prints them |
| EAGL exported symbols | 176 `EAGL::` names | EAGL's enum values and globals |
| RTTI, mangled names, map or symbol files | none | |

## Source paths

EA's assert and error macros pass `__FILE__`: 89 paths under `C:/mvp2004/source/...` and
`C:/mvp2004/libraries/...`, plus two bare EA names (`rendercontext.cpp`, `tuningdefaults.h`) and five SDK
file names. 63 `.cpp` paths are referenced from game code
in 0x800034A0..0x80364000, covering database, frontend, script, ai (batter, fielder, pitcher, runner,
umpire, team, bench, bullpen), animation, assetmanager and geomlib (33 files).
Each fixes the unit of every function that references it. In `.text` the paths run roughly folder by
folder, so the link order follows the source tree. Most units have no path; step 7 fills the gaps from them.

## Class type IDs (the strongest source)

EA's classes carry a hand-rolled type system. A class has a virtual function returning its name and
another returning a 32-bit type ID, and the ID is the djb2 hash of the name (h = 5381; h = h*33 + c):

```
fn_802D720C:  lis r3, 0xB38E; ori r3, r3, 0x54D3; blr     # 0xB38E54D3 == djb2("cCameraBasic")
fn_802D7218:  lis r3, "cCameraBasic"@ha; addi ...; blr    # the name getter
fn_802D10A0:  passes "cCameraBasic" to the base constructor, then stores vtable 0x80664658
```

`tools/research/typeids.py` finds every 32-bit constant the code builds and checks it against the
djb2 of every string in the DOL: 313 of 3,672 match (a chance match is about 1 in 50 over the whole
run). 123 are type-ID getters, 123 of the 126 such getters in the DOL (3 hash names not in the
binary: `fn_802AC844`, `fn_802AC86C`, `fn_802ACAF0`). The other 190 are type checks (`IsA`) in 173
functions, which name the class being tested. Three hits are not class names ("BPPitchTypes",
"Throw_Meter", "Bos"), so each hit is read in context, not taken blindly.

What this gives the naming pass: for about 123 classes, EA's class name for the vtable, the
constructor that stores it, and the two getters, from one table.

## Named attributes (EA's reflection)

Many classes register their members by name with a family of helpers at 0x8037B3E8..0x8037B830
(our description, not EA's names): object, name string, address of the member, a range string, a
flag. For example `fn_800212C8` registers "GeneralHitSpecs", then members at offsets 0x4, 0x8, 0xC,
each with the range "1.0, 50.0, 2". The helpers are called about 1,800 times (660 for the most used
one) and the names include tunables ("MasterVolume", "PBPVolume%"), script hooks ("GetXYZFromCamera")
and frontend layout fields ("layoutname", "checkboxenabledcombo"). Code references 2,950 CamelCase
identifiers in all. A member registered this way gets EA's name, at a known offset: T1 names for
fields and struct layouts.

## Messages naming their function

25 strings name the function that prints them, in 13 functions (`cFEManager::Init()`,
`cGCFileReader::SkipTo()`, `cMapFile::GetLine()`, `SphereMapManager::SetupSphereMaps()`,
`RenderContext::SetSize()`, `VP6_CODEC_INTERNAL::GetFrameFromList()`, ...). EA's own typos are kept
as spelled ("SphereMapManaager", "RenderContest").

## EAGL exported symbols

EAGL has a dynamic loader (ELF `.o` models such as `models/ball.o`, loaded from the disc at run
time) and a symbol pool that exports 176 `EAGL::` names to them: render-state enums (`EAGL::PT_`,
`EAGL::GCBL_SRCALPHA`, ...) and globals (`EAGL::ViewPort::gpProjectionMatrix`, ...). The models
themselves are game data on the disc and are not in the repo.

## Not present

No GCC RTTI type names (built with `-fno-rtti`), no mangled symbols, no `__PRETTY_FUNCTION__`
strings, no map or symbol file in the DOL. Related builds that might carry them are step 6.
