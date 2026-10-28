## Scope

Tier (A, B or C), task or issue, affected units or tools, dependencies, and unresolved work.

<!-- Where contributors are on, a line `Credits: @login, @login` names who made this PR's functions exact; without it the PR author is credited. -->

## Targets

One row per active target. A shared change is safe for a target only when its row is filled from a build of that target.

| Target | Byte-identical | Units touched (Matching state there) | Progress delta (`ninja ... progress`) | Evidence rows added |
| --- | --- | --- | --- | --- |
| GV4E69-rev0 | yes / no | | | |

## Evidence and validation

Evidence records and the test and build commands with their results, per target. Identify what was checked; a baseline relink does not validate reconstructed source. For a file with a new `#if VERSION_` block, the `python3 tools/versions.py diff` output was read.

## Review

- Reviewed revision: full commit SHA
- Accuracy record (tier A): link, or justified N/A
- Hostile record (tiers A and B): link and verdict

Request the owner's decision only after the records and required CI cover the final revision. New substantive changes require renewed review. Contributors do not merge.
