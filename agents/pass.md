# The pass and its feedback loops

Owner decisions (2026-09-29): exact means named and commented in the same commit; accuracy over
speed; a small pilot, heavily scrutinized, before any scaling.

Why (from tw2004): there, matching lanes named and commented as they went with nothing checking the
words. About 7% of names and 1 in 5 comments turned out wrong. Names were then banned during
matching, which traded wrong names for missing ones and cost a full blind audit plus a second
readability pass. Tooling fixes also came late, after many lanes had already run. The byte match
proves code, never words; so the words get their own gate and their own measured check.

## The unit of work: one pass, asm to DONE

A lane takes one unit (one EA source file) and leaves it DONE. There is no second pass. DONE is
checked by a tool (to build: `tools/agents/done.py`), never self-reported:

1. Every function exact, the unit linked, its data in C.
2. Every function named, each name with an evidence row in `config/<VERSION>/name_sources.tsv`.
3. Every function commented (NONE only for a body of 3 lines or fewer whose name says it all), and
   every `fake match:`, `port:` and `EA bug:` label kept.
4. Locals read as words. Every struct field the unit touches is named in its header; every global
   it defines is named and commented.
5. The file header comment says what the file is and where its name comes from.
6. No `fn_`, `lbl_`, `unk`, `arg0`, `var_`, `temp_` left in the unit.
7. It meets `docs/fidelity.md` (from 2026-09-30): EA's types, no banned trick, every `// MATCH:`
   and `// fake match:` note counted and justified, consistent patterns.
8. The hostile review (`docs/review-checklist.md`) says SHIP, or every finding is fixed or answered
   in the PR.

## The per-file loop, pick to merge (owner, 2026-09-30)

1. **Pick** a unit whose callees are already DONE or library code (leaves first).
2. **Types first.** List every type the unit touches. Take each from the shared headers; if it is
   missing, build it there first from the reference DWARF (GoldenEye, MoH EA, nfsmw) and the
   FIFA/UEFA maps (`docs/reference-builds/`), with an evidence row. No local stand-ins.
3. **Match** each function in EA's form (CLAUDE.md fidelity order). A forced shape gets a
   `// MATCH:` or `// fake match:` note (`docs/fidelity.md` rule 4); banned tricks never.
   Try variants with the one-function trial tool, from a copy in your scratch folder:
   `python tools/match/trial.py src/<unit>.cpp <symbol> --src <scratch>/variant.cpp`. It compiles
   the variant with the unit's own flags and diffs that function against the target (exit 0 when
   the instructions are identical); `ninja` and the report stay the final word. Log every attempt
   on a function that is not exact yet in its tried-ledger (`agents/brief.md`).
4. **Name** every function, type and field, with a tier (T1..T4) and evidence row.
5. **Comment** every class and function: intent, never narration (rule 7).
6. **Self-check:** `ninja` ends with `main.dol: OK`; count the notes
   (`grep -cE '// (MATCH|fake match):'`); run the DONE list above.
7. **Blind naming review** (loop 2) on the stripped functions.
8. **Hostile review** with `docs/review-checklist.md`, verbatim. Round 1: a fresh agent that has
   not seen the lane's work. Every FAIL is fixed, or answered in the PR with evidence. Round 2 on:
   the same reviewer re-checks only its FAILs and what the fixes changed (the checklist says how).
   REDO sends the unit back to step 2.
9. **Merge** only on `main.dol: OK` in CI, the CI report (`report.json`) checked by the
   orchestrator (the unit's exact functions all exact, nothing else lost) **and** the hostile
   review's SHIP (owner, 2026-09-30). CI green alone never merges a game unit, partial units
   included. The PR lists the note count, the review verdict and the blind-review score.

**A partial unit** (some functions still not exact after a real effort) may land with its object
`NonMatching` in `configure.py`, so the asm stays linked. Steps 2 to 8 still apply to every
function whose C is committed, exact or not: named, commented, reviewed, no unlabelled
scaffolding (`docs/fidelity.md` "Partial units"). Each non-exact function has its tried-ledger
entry with its best score. The unit is not DONE until every function is exact and it is linked.
It merges only on the hostile review's SHIP, like any other unit (step 9).

**A rule change sweeps main** (owner, 2026-09-30). A PR that changes `docs/fidelity.md` or
`docs/review-checklist.md` also checks every game unit already on main that the change covers,
in the same PR, and fixes what it finds through the same review loop.

**Order:** leaves first by call graph, so a function is named after its callees are.

**No sweep files.** m2c drafts every function, but its output is scratch input for the lane that
owns the unit, never committed on its own. Units therefore need boundaries before bulk matching:
discovery produces the file map first (`docs/discovery.md`).

**Shared headers:** the lane that owns an area owns its headers' fields. Other lanes add, never
rename; a rename they need goes in their report.

## Evidence (every name, every behaviour comment)

- **T1/T2, EA's name:** EA's own text in the binary (assert, string), or EA's name from a related
  build that the code confirms. Spelled as EA did; the source is cited.
- **T3, read from the code:** what it does, in EA's style (`System_Verb`, the prefix the file or EA
  already uses). No address, no "maybe": the tier says how sure. A clear true name beats `fn_`.
- **T4, judgment:** the code does not settle it. The row says `guess`; the comment still says only
  what the code shows (`docs/fidelity.md` rule 1). Types and fields get rows too.
- A comment says what the code does in the game: units, ranges, what 0/NULL means, side effects.
  Never a claim the code does not show. An open question goes in the report, not the comment.

## Loop 1: the gate (every merge, automatic)

Nothing lands unless: `main.dol: OK`; no exact function lost; every newly exact function has a name
row, a comment and its labels; lint clean; no placeholder left in a unit marked DONE; for a game
unit, exact or partial, the hostile review's SHIP. All or nothing.
Tools come from tw2004's latest state (`merge.py`, `name.py`, `check_batches.py`, `replay_lane.sh`,
`lanediff.py`), ported after the compiler is identified.

## Loop 2: the accuracy check (every round)

A fresh reviewer that has never seen the lane's words reads a random sample of the round's
functions with names and comments stripped, and writes its own. A reconciler scores each function
against the code: name right / wrong, comment right / incomplete / wrong. Results go to
`agents/accuracy.tsv`.

- Sample: **100% during the pilot**, then about 10% per round.
- Thresholds (to confirm with the owner): names 3% wrong, comments 5% wrong or incomplete.
- Over threshold: that lane's round is re-reviewed in full, and the cause (prompt, rule, tool,
  missing evidence) is fixed before the next round.

## Loop 3: the process (every round, orchestrator)

Every slip, failure or hand workaround gets a row in `agents/friction.tsv`: what happened, its
cause, the fix, and the commit of the fix. The same hand workaround twice is a tool bug, fixed
before the next launch. A failure is fixed at its cause or put to the owner, never reported as minor.
Rule changes are dated where they are written.

## Loop 4: the pilot (once, before scaling)

One lane, one small section (criteria below), full pass, 100% blind review. Iterate until a round
has **zero friction rows and accuracy under threshold**. Then 2 lanes, then more, re-checking loops 2
and 3 at every step up.

Pilot section criteria (picked after discovery):
- about 20 to 40 functions, mostly leaves (math, memory, containers, checksums);
- EA code, not SDK (SDK comes from public decomps and tests nothing about naming);
- some outside name evidence (an assert path, a reference build), so both evidence tiers are tried;
- at least one struct and some owned data, so fields, globals and data linking are exercised.
