# Target configuration and evidence records

`config/targets.json` lists every target (schema 1, the shape the progress site reads), `config/site.json`
holds the game's presentation and `config/ci-targets.json` maps changed paths to the targets they affect.
Each target's build inputs live in `config/<target id>/`: for a decomp-toolkit project these are
`config.yml`, `splits.txt`, `symbols.txt` and `build.sha1`. Symbol and split files are toolkit inputs, not
recovered names or source boundaries; claims about either belong in `evidence.tsv`.

## Evidence records

Each target keeps curated claims in `config/<target id>/evidence.tsv`. Record one claim per row and add
rows when they support a source or configuration change. Keep bulk tool output and experiment histories
outside public Git. `python3 tools/evidence.py check` enforces the format below.

What earns a row is a claim a person or agent made that a reviewer must be able to challenge: an
`inferred` name, a `unit` boundary, a `type` or `field` layout read from loads and stores, a `compiler`,
`source-form` or `linker` claim. Tool output (symbol extents, debug names, signature hits) is one row per
tool run, not one row per hit: kind `unit-anchor` or `name`, origin `related` or `signature`, the subject
names the tool with its inputs and revision, and the evidence is the path of the regenerable report.

| Column | Meaning |
| --- | --- |
| `kind` | `name`, `function`, `data`, `unit-anchor`, `unit`, `type`, `field`, `external`, `compiler`, `assembly`, `source-form` or `linker`. |
| `start`, `end` | Target virtual addresses as `0x` plus eight upper-case hex digits; range ends are exclusive. Use `-` for unknown or inapplicable addresses. |
| `subject` | Symbol, source path, type or field concerned. Neutral address labels do not claim original names. |
| `origin` | `target`, `signature`, `related` or `inferred`, as defined below. |
| `start_boundary`, `end_boundary` | Independent edge claims: `exact`, `provisional`, `open` or `-`. |
| `evidence` | A concise, reproducible locator and explanation of what it establishes and what remains unknown. |

`target` means the claim is directly present in the target's symbols, debug information, text or bytes.
`signature` means a named tool signature supplied it. `related` means it comes from another identified
build. `inferred` means interpretation of the code. A matching body from a related build does not by itself
establish the target's original name or source file.

For a `name` claim, `target` requires explicit target name evidence; behavior alone belongs under
`inferred`. Record the function's extent in a separate `function` row so a name claim cannot silently
establish its boundaries. Types and fields likewise need their own evidence.

Edge claims other than `-` belong to `function`, `data`, `unit`, `assembly` and `linker` rows. `exact` means evidence establishes that edge. `provisional` means a candidate edge still needs
confirmation. `open` marks an anchor with the true start at or before it, or the true end at or after it.
Use `-` where no edge is claimed. A `unit-anchor` identifies evidence of a source path, not a unit's extent
or ownership of neighboring functions.

Evidence must be usable by another contributor: identify target addresses and observations, or a
reference's revision/hash and symbol or record. Include a tool version and signature identifier for
signature claims. A local absolute path or an unexplained score is insufficient.

These records describe evidence, not matching progress or approval. Changes to executable symbols and unit
splits require corresponding evidence and the contribution review passes. Review findings, tested revisions
and the owner's acceptance remain in the PR.
