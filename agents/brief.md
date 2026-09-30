# Agent brief (every lane reads this first)

You are one of several agents on the MVP Baseball 2005 (GameCube) matching decomp. An orchestrator
reviews your work, merges it into `main` and pushes it. Every agent writes as if one author wrote
everything: experienced decomp people will read this code. The hard rules in `../CLAUDE.md` apply
to you. Then read `agents/pass.md`: it defines the unit of work and the checks your work goes through.
Then `docs/fidelity.md`: how the code must read, and `docs/review-checklist.md`: the hostile review
your unit must pass before it merges. Byte-exact is the floor, not the goal.

## Your job: one unit, one pass, DONE

Your prompt gives your unit(s) and a stop time. For each function, leaves first:
1. Make it exact in EA's form (fidelity order in CLAUDE.md).
2. In the same commit: its name (with tier, evidence and purpose), its comment, readable locals,
   and the fields and globals it touches. Labels (`fake match:`, `port:`, `EA bug:`) where they apply.
3. A function you cannot make exact after a real effort stays at its best score, clean and readable,
   and every attempt goes in its tried-ledger entry (see below). It is not named until it is exact.

Your words will be checked blind (loop 2 in pass.md). Write only what the code shows. Put an open
question in your report, never in a comment.

## Your environment

- Your checkout is a git worktree (in your prompt) on branch `agent/<lane>`. Run every command from
  it. Never touch the main checkout or another lane's worktree.
- Your scratch folder (in your prompt) holds m2c output, trial scripts and notes. Nothing from
  scratch goes into the repo.
- Start: `date`; `git merge main`; `python configure.py && ninja` (`main.dol: OK`).
- Never `git stash`, never check out another branch, never push, merge into main or rebase.
- Before you stop, make sure nothing you started is still running.

## Hard rules for lanes

- **Commit in your branch only**, plain messages (`Unit.c: Foo_Bar, Foo_Baz exact and named (12/30)`),
  never a Co-Authored-By line or AI footer.
- **Never delete any file** (no `rm`, not even scratch temp files). `git checkout -- <file>` to undo
  your own edit is fine.
- **Edit C and headers only with the editor tools.** A repeated edit is a saved Python script; read
  the whole `git diff` after running it and name it in your report.
- **Float constants: EA's exact expression** (`1.0f/72.0f`), never a rounded decimal.
- **Shared files:** headers: add fields (offset order, `// 0xOFFSET` comment) and prototypes; change
  an existing one only with proof, and list it. Build config and splits: only through the tools, or
  by hand for a unit's data ranges (say so). No `extern` or `typedef` in a .c file.
- **Do not edit `docs/` or `agents/`.** Report findings instead.
- **Friction is a finding.** Any tool that failed, any step you had to work around by hand, any rule
  that was unclear: report it (the orchestrator logs it in `agents/friction.tsv` and fixes the cause).

## Tried-ledger

Every function not yet exact has `agents/tried/<fn>.md`: every attempt from every lane, with scores.
Read it before you start on that function. Never repeat a listed attempt unless you combine it with
something new. Add your attempts before you stop, matched or not.

## Reporting (short; the orchestrator re-runs every check)

At most 8 lines: functions made exact and named; the names you are least sure of, and why; functions
left non-exact with best score; shared-file edits; friction (tools, rules, workarounds); at most one
verified finding. Facts only: if something failed or was skipped, say so.
