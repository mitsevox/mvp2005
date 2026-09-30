# USA GameCube disc inspection

Inspected 2026-09-30, before starting the viewport/frustum matching work.

## Input and identity

The Downloads file is `MVP Baseball 2005 (USA).7z`, containing
`MVP Baseball 2005 (USA).ciso`. A copy was unpacked under
`scratch/disc-inspection/`; the Downloads archive was not changed.

decomp-toolkit reports CISO, Game ID `GV4E69`, Disc 1, Revision 0.
The extracted `sys/main.dol` has SHA-1
`da6becdbea614d03c4b5eae9f8a0fb08e0a184dd`, exactly the project's target.
`files/version.txt` says `TP GC Build Number 2004-12-24_1`.

## Main executable

The disc includes `files/mvp.elf`: a stripped, big-endian ELF32 PowerPC
executable, entry point `0x80003100`. There is no symbol table or debug section
in this ELF. Its 10 nonempty allocated PROGBITS sections (6,837,290 payload
bytes) were compared by load address against the disc DOL and are identical.
Converting the ELF with dtk produces a different whole-file DOL hash because
the file layout/padding differs; this is not a different code revision.

The ELF preserves original section names that the DOL lacks, including
`.frontend_codeoverlay` and `.database_codeoverlay`. It also preserves
separate `.ctors` and `.dtors`, while the project's DOL configuration groups
that region under `.ctordtor`.

## Useful debug information: libmatd.a

`files/data/libmatd.a` is a 25-member rendering/material object archive.
Every member has a symbol table and an old-style `.debug` section, with
associated source-file and address metadata. `libmatz.a` has the same 25
member names and symbol tables, but no `.debug` sections.

Hashes:

- `libmatd.a`: `91b461b8382ab3309cbf5b6687f95622a02edaa2`
- `libmatz.a`: `a087a7e7b9e90aceb852a128ebdf612f2efdbd90`
- `libmatd.a(InstanceCrowd.o)`: `701409112e42a34a49a7c3bfa2cffee5e8ce3c20`

The `InstanceCrowd.o` compile-unit metadata identifies
`C:/mvp2004/source/GC/rendermethods/compile/objrms.gcSN/InstanceCrowd.cpp` and
`GNU C++ 2.95.3 SN BUILD v1.76 for Nintendo Gamecube`.

A scratch parser read all 4,327 old-style debug entries in that member,
checking each entry's length and attribute forms. It recovered EAGL's
viewport declarations. The archive is not the whole game's source or a
debug build of the main executable: these renderer objects retain the
shared types their compilation included.

### Verified viewport/frustum layouts

Debug metadata gives `ViewPort` size `0x1AC`, its `mPrivate` member at `0x0C`,
and `ViewPortPrivate` size `0x1A0`. Relative to `ViewPortPrivate`:

| Field | Offset | Corresponding ViewPort offset in the traced code |
| --- | --- | --- |
| `mProjectionType` | `0x04` | `0x10` |
| `mFrustum` (`VPFrustum`) | `0xE4` | `0xF0` |
| `mCullData` (`VPCullData`) | `0x10C` | `0x118` |
| `mProjection` | `0x14C` | `0x158` |

`VPFrustum` is 16 bytes: `mFOV` at 0, `mAspect` at 4, `mNearPlane` at 8,
`mFarPlane` at 12. These agree with the four stores and reloads in
`fn_803E0DD0` and `fn_803E0ACC`.

`VPCullData` is 48 bytes, with float members in this order:
`mLeftTan`, `mLeftSin`, `mRightTan`, `mRightSin`, `mTopTan`, `mTopSin`,
`mBottomTan`, `mBottomSin`, `mLeftScale`, `mRightScale`, `mTopScale`,
`mBottomScale`. Adding `0x0C + 0x10C` gives the exact `0x118..0x144`
offsets read/written by the projection and sphere-culling functions.

This establishes EA's field names and compatible layouts for the functions
in `docs/camera-widescreen.md`. It does not yet establish those functions'
original method names. Additional math/rendering type names also occur in
the debug metadata and should be decoded before inventing shared types.

## Other contents

The extracted disc contains 405 files under `files/`, plus five under `sys/`.
The standard BIGF/BIG4 archive
directories were indexed without unpacking every asset: 38,659 entries.
Neither the loose file-name inventory nor those indexed names contained
`.map`, `.pdb`, `.sym`, `.dbg`, or C/C++ source/header files. Sixteen audio
files with a `.big` suffix use other formats and were not indexed by that
parser; nested assets were not recursively searched for embedded debug data.

`mvp.ini` contains documented development switches for AI, simulation,
collision, camera, goals, performance and rendering. Its opening comment
says the file is disabled in shipping builds. Their presence is useful
vocabulary/evidence, not proof that changing the INI activates them.
`mvporide.ini` is a mostly empty override template.

The disc also contains 15 loose runtime model `.o` files with symbol tables. These
can provide references to EAGL's interfaces, even though they are not the
game's AI or physics source.

## Next use

The initial machine-readable catalogue is
`config/GV4E69/disc_types.tsv`: 9 selected EA rendering/viewport types and
54 members, exported from `libmatd.a(InstanceCrowd.o)`. Each row records the
archive/member hashes, original debug-record offset, name, size/member offset
and type reference. Offsets in this catalogue are debug-section offsets or
member offsets, not function addresses. It is a declaration-evidence catalogue,
not a map of the whole game and not a replacement for `name_sources.tsv` when
a name is applied to matched source. The full retained debug metadata is
now exported separately below; this remains a convenient viewport index.

Reproduce it with the owner's extracted archive:

```
python3 tools/research/disc_debug.py <path-to-libmatd.a> \
    --output config/GV4E69/disc_types.tsv
```

The exporter reads the archive directly and emits selected metadata only.
The same 9 sizes and 54 member names/offsets were independently exported from
`Texture.o` and compared: all agree. Cross-object agreement validates this
initial catalogue; use main-executable accesses to validate each layout before
applying it to a matched function. Modified/fundamental type references remain
raw encodings where the exporter does not interpret their exact C++ spelling.

Use the disc's debug archive to establish EAGL's viewport, transform and
frustum types before matching the culling functions. Preserve provenance
per recovered name/layout and check it against the main executable.
The complete disc copy is also available locally for a future Dolphin
runtime experiment. All game binaries/assets remain in ignored scratch.

## Full retained-debug export (2026-09-30)

`config/GV4E69/disc-debug/` preserves every record and attribute from all
25 `libmatd.a` members without filtering to viewport types: 132,461 records
(108,382 non-padding), 394,841 ordered attributes, 150 debug/line sections,
and 188,842 debug relocations. Symbols and section descriptors from all
66 valid ELF objects found in the audit are also exported (10,775 symbols).
The main ELF, 25 `libmatz.a` members and 15 runtime models have no debug sections.

`.debug` records, strings and numeric forms are decoded. Block expressions
and unknown attribute semantics preserve exact encodings. The remaining
125 debug/source/line sections are explicitly uninterpreted metadata hex.
Hashes, original offsets and separate debug relocations retain provenance.
No executable-code payloads, game assets, complete ELF/object/archive files,
or source/header contents are included.

```
python3 tools/research/disc_debug_full.py <extracted-disc> \
    --output config/GV4E69/disc-debug
python3 tools/research/disc_debug_full.py --verify config/GV4E69/disc-debug
```

The saved JSON reconstructs 340 metadata sections exactly against their hashes.
A separate-directory regeneration is byte-identical. The catalogue README
documents the format and count definitions.

The expanded scan examines every loose file and every standard BIG entry by
ELF/archive magic. It identifies 243 animation `.ord` entries with ELF
signatures but out-of-bounds declared section-header tables, recording
hashes and failures rather than certifying them debug-free. The 16 nonstandard
audio BIG files remain unindexed; nested/compressed assets were not recursively
searched. This preserves all retained debug data in successfully audited
objects; it does not claim to map the entire game.
