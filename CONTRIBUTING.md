# Contributing

Recover plausible original source, supported by evidence. A byte match establishes compiler equivalence; it does not establish correct names, types, source boundaries or intent. The [README](README.md) identifies the targets, the project owner and the build setup.

## Authority and tiers

Contributions contain source, tools and reviewed metadata. Do not publish original game binaries, disc images or assets. Keep experiments and bulk research out of public Git. Clone the repository and follow the [build setup](README.md#building); use your own checkout and a dedicated branch (`git switch -c your-task`). Contribution branches, PRs, reviews and required CI checks belong in this repository: CI builds only branches of this repository, and a fork's pull request is rejected before any private input is used. Use the owner-approved build environment at its pinned digest; report missing inputs or tooling problems in an issue for the owner's decision rather than changing a dependency.

**Only the project owner ([mitsevox](https://github.com/mitsevox)) authorizes and performs merges into `main`.** Contributors and agents prepare branches, submit PRs and review changes. A reviewer verdict or passing CI never grants merge authority. Nobody pushes to `main`, enables automatic merging, or changes branch rules, repository settings or the build image.

What protects matching integrity, in order: CI proves the complete executable of every affected target is byte-identical and measures each unit per target; the matching-integrity rules below; a reviewer who did not write the code reads reconstructed source against the disassembly and the evidence before an inferred name or boundary is published; the owner decides what merges. Everything else is proportionate to what a PR touches. State the tier in the PR's Scope line (`Tier A`, `Tier B` or `Tier C`). CI's `Check the declared tier` step fails a PR that claims less than its diff needs: `splits.txt`, `symbols.txt`, an `inferred` evidence row or a compiler or linker profile means at least A, other source means at least B. The floor is a minimum; reviewers and the owner raise the tier when the change calls for it.

| Tier | Touches | Required before merge |
| --- | --- | --- |
| A | `src/` or `include/` with new or changed inferred names, types, fields or unit boundaries; `splits.txt`; `symbols.txt`; compiler profiles | CI green, one blind accuracy record, one hostile record |
| B | `src/` or `include/` where every name and layout is `target`, `signature` or `related` (library imports, already-named code); promotions from `NonMatching` to `Matching` | CI green, one hostile record |
| C | `tools/`, `tests/`, `docs/`, `references/`, workflows, `config/*.json`, root documents | CI green |

## The task loop

1. **Claim.** Check open PRs and branches. Open a draft PR early with the unit names and target ids in its title; that is the reservation, and it ends when the PR closes.
2. **Establish boundaries and types.** Inspect the target and the reference evidence before reconstructing. Search existing headers and accepted units before declaring a shared address. A related build is corroboration, not proof of the target layout.
3. **Reconstruct and match.** Recover source in the original codebase's style. Compile, compare instructions and data with objdiff, and investigate the remaining uncertainty with controlled experiments. Keep discarded variants local; retain useful partial reconstruction as a `NonMatching` object so CI measures it. Promotion to `Matching` does not move the source file.
4. **Name and explain.** Record provenance for recovered names, types, fields and boundaries in `config/<target id>/evidence.tsv` using the [evidence format](config/README.md). Cite the actual loads, stores and caller or callee behavior for inferred widths and signatures. Keep readable names distinct from claims of original names; unresolved functions keep the tool's address label. Comments explain intent and invariants, never scores, compiler notes or process.
5. **Check every target.** Build every active target and confirm `build.sha1` on each; run objdiff per target for each touched unit; run `python3 tools/versions.py diff` on every file you added a version block to; add evidence rows to each affected target's `evidence.tsv`. Fill the Targets table of the PR template from these results.
6. **Review.** Tier A: an independent reviewer interprets the scoped functions with the proposed names and comments withheld, reconciles that interpretation with the submission and posts an `Accuracy:` record; then a fresh reviewer applies the hostile checklist and posts a `Hostile:` record. Tier B: the hostile record only. Tier C: none. Resolve every finding by fixing it or providing evidence.
7. **Submit for the owner's decision.** Required CI passes on the final revision with no unexplained regression; the records cover that revision and name the targets they checked.

Partial reconstructed functions may be committed, submitted and merged before reaching 100% byte equality. A measured mismatch alone is not a review failure. Review source fidelity, evidence and comparison integrity separately from completeness; document mismatches and open questions.

A version difference lives in the shared file under `#if VERSION_<DEFINE>` (`include/version.h` states the rule). When a function would carry three or more blocks, or more than about a third of its lines inside blocks, write the whole function once per variant under one function-level `#if`, in the same file. A unit that matches on some targets only is `Object(MatchingFor("<id>"), ...)`; a unit absent from a target is absent from that target's `splits.txt`.

## Matching integrity

Do not manufacture a match through unsupported compiler or comparison manipulation:

- No per-function flags, optimization pragmas or compiler attributes introduced to force code generation.
- No inline assembly, embedded instruction bytes or patched compiler output substituting for originally compiled source.
- No invented helpers, casts, volatile qualifiers, padding or control flow whose only justification is obtaining matching bytes.
- No altered symbol boundaries, excluded comparisons or progress categories that conceal mismatches.
- No behavioral changes made to satisfy the compiler.

Compiler versions and flags need evidence at the original compilation-unit or library level. A function-specific exception requires evidence that the original used it and the project owner's explicit approval. Originally handwritten assembly likewise requires provenance.

A suspected fake match remains a local experiment, outside accepted source, unless the project owner explicitly authorizes a documented exception. A `fake match` label is not permission. Otherwise leave the original assembly linked and the recovery unresolved.

Put compiler reasoning, exception evidence and matching experiments in metadata or the PR, not explanatory matching comments in reconstructed source. Preserve original assertions and diagnostics when the target requires them.

## Evidence

Each target keeps its claims in `config/<target id>/evidence.tsv`; [config/README.md](config/README.md) defines the columns, kinds and origins, and `python3 tools/evidence.py check` enforces the format in CI. A row is a claim a reviewer can challenge: an inferred name, a unit boundary, a type or field layout, a compiler profile. Tool output is one row per tool run, naming the tool, its inputs and revision and the regenerable report, not one row per hit.

## Hostile-review checklist

The first reviewer must be independent of the reconstruction and its prior reasoning. Supply the scoped source and headers, target disassembly and relevant data, provenance records, unit boundaries, compiler settings, comparison configuration and validation results for an identified revision. References must be accessible to the reviewer; absent essential evidence is a blocked check, not permission to assume correctness.

Review all submitted reconstructed functions, including partial ones:

| Check | Required result |
| --- | --- |
| Source fidelity | Behavior and source structure are supported by the target and references; no unsupported matching tricks. |
| Compiler settings | Compiler and flags have evidence at the appropriate scope. Inspect per-function overrides and verify evidence and owner approval for any exception. |
| Types and layouts | Declarations reflect available evidence, including sizes, offsets, signatures and shared ownership. Unknowns are explicit; no fabricated layouts or match-only substitutes. |
| Provenance and licence | Imported code names its source repository, pinned commit and licence in `CREDITS.md` ("no licence" is stated, not omitted); a licence that requires its text has it under `licenses/`; copyright and licence notices in imported files are intact. Check the source repository itself, not only the PR's claim. |
| Names | Provenance supports original-name claims. Inferred names describe what the code establishes without presenting guesses as recovered facts. |
| Comments | Comments clarify meaning and readability without obvious narration, speculation, compiler explanations or process notes. Absence of an unnecessary comment is not a failure. |
| Unit boundaries | Splits and code/data ownership have evidence. Provisional boundaries are identified; no artificial fragmentation or grouping to inflate progress. |
| Comparison integrity | No patched output, excluded comparisons, altered symbol ranges or misleading categories conceal mismatches. Partial and linked results remain distinct. |
| Validation | Required checks cover the reviewed revision, complete target output, unit code/data and regressions against the base revision. No substituted scores or unverified success claims. |

Report `PASS`, `FAIL`, `BLOCKED` or a justified `N/A` for each check. Findings identify the file/line or configuration location, supporting evidence, and required correction or missing information. Do not invent what the original author would have written or treat stylistic preference as evidence.

End with the reviewed revision and one verdict: `SHIP` (no unresolved failures or blocked checks), `FIX` (localized corrections), `REDO` (unsupported tricks or fundamental reconstruction problems) or `BLOCKED` (essential evidence or validation unavailable). A verdict does not authorize merging.

After fixes, apply the delta recheck rules above. In the final record, cite the earlier review, list the checked changes and finding resolutions, and identify carried-forward coverage. Newly discovered defects may still be reported on unchanged code. Additional changes require coverage and validation for the resulting revision; an old verdict alone does not cover new changes.

## Review records

Post each pass as a separate PR comment. The first line is `Revision: FULL_COMMIT_SHA`, the second `Targets: <ids checked>`, the third the verdict: `Accuracy: PASS` or `Accuracy: N/A - <reason>` for the accuracy pass, `Hostile: SHIP`, `Hostile: FIX`, `Hostile: REDO` or `Hostile: BLOCKED` for the hostile pass. Each header occurs once, outside quotes and code fences. Then the reviewer's identity and prior involvement, the scope, the evidence used, the findings and their resolution. A record covering one target never reads as covering another. Do not write a successful record before the review happens.

**Rechecks.** After fixes, the reviewer checks each prior finding, the correction and its affected behavior, declarations, callers, boundaries and evidence, and carries unchanged coverage forward by linking the earlier record and its revision. A replacement reviewer may continue from that record. A full restart needs a concrete reason that invalidates coverage across the PR; a localized defect is not one.

**Refreshes.** After refreshing from `main`, verify the diff, conflict resolutions and affected shared declarations, then post final-revision records that cite the earlier ones and name the checked delta. An earlier verdict alone does not cover the new head. When source or build inputs change, earlier CI cannot substitute for final-revision validation.

**Batches.** Compatible bounded contributions may be integrated in one PR with each original PR, author revision and review coverage identified. Review the combined delta and affected dependencies and require final-revision records and CI. Compiler-profile and comparison changes get their own review and never ride along in unrelated work.

## Feedback

Use PR discussions for review findings and issues for unresolved research or recurring tool problems. Keep detailed failed experiments in private research. Correct recurring failures at their cause instead of repeating workarounds. Change permanent instructions through a focused PR when the agreed process needs correction; do not rewrite the rules to justify the current patch.
