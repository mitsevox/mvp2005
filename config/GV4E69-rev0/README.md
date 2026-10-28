# GV4E69-rev0

USA release, disc revision 0. `main.dol` SHA-1 `da6becdbea614d03c4b5eae9f8a0fb08e0a184dd`. What the disc holds: [docs/disc-inspection.md](../../docs/disc-inspection.md).

| File | Purpose |
| --- | --- |
| `config.yml` | decomp-toolkit project input: the original, its hash, the symbol and split files |
| `build.sha1` | Expected hash of the relinked executable |
| `symbols.txt`, `splits.txt` | Every symbol and unit boundary |
| `ldscript.tpl` | The link script for SN's `ngcld` |
| `filemap.tsv` | Where the original source files begin and end ([docs/filemap.md](../../docs/filemap.md)) |
| `name_sources.tsv` | The evidence behind every game name, one row per applied name (`docs/process/pass.md`, "Evidence") |
| `linked_names.tsv`, `imported_units.tsv`, `disc_types.tsv`, `refnames/` | Library names, the imported units with their upstream commits, disc types, and reference-build name matches |
| `evidence.tsv` | The standard evidence table ([format](../README.md)); empty here, because `name_sources.tsv` carries this project's evidence |
