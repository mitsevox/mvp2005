# The progress page

https://mitsevox.github.io/mvp2005/ (once Settings > Pages > Source is set to "GitHub Actions").
The same page as tw2004's, pointed at GV4E69.

## How it is built

`.github/workflows/pages.yml` runs after every successful Build of a push to main:

1. it downloads that run's `GV4E69_report` artifact (objdiff's `report.json`, uploaded by
   `build.yml`);
2. `tools/dashboard/pages.py append` adds the commit's numbers (sha, date, exact functions,
   matched and linked code and data) to `history.json` on the data-only branch `pages-history`
   (created on the first run);
3. `tools/dashboard/server.py --export site` writes `index.html` (reads `progress.json`),
   `progress.json` and `history.json`;
4. the `deploy` job publishes `site/` with `actions/deploy-pages`.

It is kept apart from `build.yml` and needs neither the private build container nor any game file.
Only report.json numbers, file (unit) names, `symbols.txt` function counts and commit subjects are
published. `workflow_run` triggers fire only while `pages.yml` is on the default branch.

Running the workflow by hand (Actions > Pages > Run workflow) republishes from the latest
successful Build of main. Before any Build has produced a report, the page says there are no
numbers yet.

## Changing the page

Edit `PAGE` in `tools/dashboard/server.py`. The same page serves locally:
`python tools/dashboard/server.py` (http://localhost:8420, reads `build/GV4E69/report.json` after
`ninja`), and `python tools/dashboard/server.py --export site --report <report.json>` writes the
static copy to check before pushing.

"Functions exact" is objdiff's count of byte-matching functions. The project's stricter "exact"
(named and commented in the same commit) is not on the page yet; it waits until the pass tooling
defines "commented" (owner, 2026-09-29).

## decomp.dev

decomp.dev reads the `GV4E69_report` artifact of the latest CI run on main, the same as for
tw2004. Listing the project there is a separate step, not done yet.
