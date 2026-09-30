# Retained disc debug metadata

Exported from the owner's GV4E69 retail disc on 2026-09-30. This preserves
all retained debug metadata found in the audited ELF/archive objects, not
just viewport types. It is not source code or a map of the whole executable.

`manifest.json` records source/member identities and hashes, section
descriptors/hashes, output hashes, scan results and counts. The manifest
maps each `object-NNN.jsonl` to its original member. Objects 000 through
024 are all 25 `libmatd.a` members. The other 41 objects have no debug
sections; their symbols/descriptors document the disc-wide audit.

| Metadata | Exported |
| --- | ---: |
| Valid ELF objects | 66 |
| Objects retaining debug information | 25 |
| Debug/line sections | 150 |
| DWARF1 records including padding | 132,461 |
| Non-padding DWARF1 records | 108,382 |
| Ordered attributes | 394,841 |
| ELF symbols | 10,775 |
| Debug/line relocations | 188,842 |
| Records with unsupported attribute forms | 0 |

All 25 `.debug` sections are structurally decoded into records and ordered
attributes. Names, strings and numeric forms are decoded. Block expressions
(locations, enumeration lists, modified types, array bounds and others)
retain exact hex encodings; their semantics are not all interpreted.
Unknown attribute codes stay numeric and are counted per object. Nothing
is filtered by type name, source path or SDK origin.

The other 125 sections (`.debug_aranges`, `.debug_pubnames`, `.debug_sfnames`,
`.debug_srcinfo`, `.line`) retain their complete encoding as explicitly
uninterpreted metadata hex. This preserves source/line/address metadata,
without claiming a decoded source-line catalogue. Relocations stay separate:
record values are unrelocated, not resolved addresses in `main.dol`.
Repeated declarations retain each translation unit's own provenance.

## JSONL format

Each line is an object identified by `kind`:

- `object`: source identity, ELF header summary, section descriptors/hashes.
  Non-debug section contents are never exported.
- `symbol`: table/index, original name and string-table offset, value, size,
  info, other byte and section index. Mangled names remain unchanged.
- `debug_section`: section index, size/hash and encoding. Auxiliary sections
  preserve the complete metadata encoding in `payload_hex`.
- `debug`: original offset/length/tag, optional name and ordered `attributes`.
  Each attribute is `[original_code, value]`: form is `code & 15`, identity
  is `code & ~15`. Forms 1/2/5/6/7 are fixed-width integers, 3/4 block hex with
  16/32-bit length prefixes, and 8 Latin-1 strings (ASCII-escaped in JSON).
  Duplicate attributes survive. Null/padding records retain `padding_hex`.
  Future unsupported forms preserve `unparsed_tail_hex` instead of dropping it.
- `debug_relocation`: compact `fields` array, with its order in the manifest:
  section, entry index, target section, offset, type, symbol table, symbol
  index, signed addend for RELA. Resolve symbols through the same object's
  `symbol` rows.

Offsets/lengths/indexes are decimal integers. DWARF references and relocatable
symbol values are section-relative. Attribute/tag names in the manifest are
convenience labels; original numeric codes and encodings are authoritative.

## Reproduction and verification

```
python3 tools/research/disc_debug_full.py <extracted-disc> \
    --output config/GV4E69/disc-debug
python3 tools/research/disc_debug_full.py --verify config/GV4E69/disc-debug
```

The input directory contains `files/` and `sys/`. Export checks bounds and
reconstructs exported metadata sections against original bytes before writing.
`--verify` reads the saved JSON and reconstructs 340 debug/symbol/relocation
sections against their hashes without requiring game files. Regeneration
into a separate directory produced byte-identical JSONL and manifest files.
These checks verify preservation, not all semantic interpretations or layout
compatibility with the main executable. No code/assets, complete object/
archive/executable files, or source/header contents are included.

## Audit limits

The scan examines magic in all 410 loose extracted files (405 under `files/`,
five under `sys/`) and 38,659 standard BIGF/BIG4 entries. Two material archives
provide 50 valid ELF objects; 15 runtime models and the stripped `mvp.elf`
provide 16 more. None beyond `libmatd.a` retains debug sections.

The manifest records 243 animation `.ord` entries with ELF signatures whose
declared section-header tables extend past their entry lengths, including
hashes, sizes and exact parse failures as `unparsed_candidates`. They are not
certified debug-free. Sixteen nonstandard audio BIG files remain unindexed.
No general decompression or recursive search of embedded/nested assets was
performed. “Full” means all retained debug metadata in successfully audited
objects, not proof that every asset container lacks embedded information.
