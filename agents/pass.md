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
- A comment says what the code does in the game: units, ranges, what 0/NULL means, side effects.
  Never a claim the code does not show. An open question goes in the report, not the comment.

## Loop 1: the gate (every merge, automatic)

Nothing lands unless: `main.dol: OK`; no exact function lost; every newly exact function has a name
row, a comment and its labels; lint clean; no placeholder left in a unit marked DONE. All or nothing.
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
