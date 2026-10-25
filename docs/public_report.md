# The shared-site report

MVP's progress is published on the shared site, https://mitsevox.github.io/games/mvp2005/, through
the site's report-v1 contract (the site repo `mitsevox/mitsevox.github.io`:
`docs/reporting/platform.md` and `contract-v1.md`; the handbook's
[Website chapter](https://mitsevox.github.io/wiki/website-integration/)). The older standalone page
(`docs/progress_page.md`) keeps running until the shared page carries everything it shows.

## How a report is made

Every run of `.github/workflows/build.yml` (job `build (GV4E69)`, also the required check on main):

1. **Build and verify main.dol**: a fresh build with no build cache. `ninja progress` depends on
   the `main.dol` hash check, so a non-identical build fails here. The step records the measurement
   time right after `ninja`.
2. **Export public report inputs**: `tools/public_report.py inputs` turns objdiff's `report.json`
   into `build/public-input/summary.json`, `map.json` and `timeline.json`; `tools/public_report.py metadata` writes the execution
   facts (commit, tree, the workflow file's Git blob, configure.py's pinned tool tags, run and
   attempt, measurement and publication times).
3. **Package and validate public report**: the site's own `tools/package_report.py`, checked out
   at a pinned site revision, builds `manifest.json` and `receipt.json` and validates the package
   against `config/GV4E69/producer.json`.
4. **Upload public report**: artifact `public-report`, public JSON only.

PR runs make the same artifact as evidence only. The site imports only successful `push` or
`workflow_dispatch` runs on main, authenticates the run, job, steps, workflow blob, tree and
artifact digest against its copy of the producer policy, and never runs anything from the package.

## What the numbers mean

| Field | From report.json |
|---|---|
| code / data `totalBytes` | `total_code` / `total_data` |
| `linkedBytes` | `complete_code` / `complete_data` (units linked from our source) |
| `matchedBytes` | `matched_code` / `matched_data` (bytes objdiff compares equal) |
| code `fuzzyEquivalentBytes` | sum over functions of size × fuzzy % (an exact function counts its whole size) |
| data `fuzzyEquivalentBytes` | `null`: objdiff measures no data similarity |
| `functions.total` / `exact` | every function in the report / those at 100% |
| `functions.named` | functions whose symbol is not an `fn_` address label |
| `files` | `null`: unit boundaries are not yet backed by original-boundary evidence for every unit |

`functions.exact` is objdiff's byte match, not this project's stricter "exact" (named and commented
in the same commit). The methodology is `objdiff-report-v1`, generation 1; change either in
`tools/public_report.py` when what a number means changes, so old rows keep their meaning.

## The map

`map.json` (map-v1) holds two trees over the same bytes, and the site checks that they cover
exactly the same addresses and add up to the summary:

- `files`, which the page draws: one code tile per unit, holding one leaf per function (its
  address and full size, so the site can count the 24k-function inventory and the exact ones),
  and one data tile per unit spanning all its data sections. Tiles are in address order.
- `sections`: the functions grouped by DOL code section (`.init`, `.text`), and the data tiles
  as one `Data sections` group. objdiff reports data matches per unit, not per section, so a
  unit's data cannot be split by section without inventing numbers.

A function leaf is linked when its unit is linked, matched when objdiff scores it 100%, and its
fuzzy bytes are size × fuzzy %, the same expression the summary sums.

## The timeline

`timeline.json` (timeline-v1) holds one row per successful main run: the revision, the
measurement time, and code/data total and linked bytes, the same numbers as that run's summary.
Each run restores the rows of the last successful main run before it (its `public-report`
artifact, checked against its manifest) and appends its own row with `measured` provenance. A
rerun of a revision the timeline already holds changes nothing. Main runs queue in `build.yml`'s
concurrency group, so a run never starts before the one ahead of it has published, and no row
the site may have imported is skipped. As a guard, every row the site holds as accepted (its
`report-data` and `main` locks) must come back unchanged, or the build fails before the site
would reject the package. If the previous run's artifact has expired, the site's accepted
timeline is the starting point.

The contributor module is not supplied; the manifest declares it unsupported.

### Old page history (migration record)

The first timeline starts from the old standalone page's history, `history.json` on the branch
`pages-history` (blob `3f6dff0632cdcb6eb11a76b9185d0d3e0b436f98` when the timeline was added),
under the handbook's legacy-import rules
([Existing projects](https://mitsevox.github.io/wiki/existing-projects/#import-legacy-history)).
The branch stays as the raw record.

- **Source.** `pages.yml` wrote one record per main build: the full commit SHA, the commit time
  (`git log --format=%ct`), and `total_code`, `complete_code`, `total_data`, `complete_data`
  copied from that build's own `report.json` artifact.
- **Mapping.** `revision` = `sha`; code/data `total` and `linked` = `total_*` and
  `complete_*` as recorded, each row with its own totals (they change across the history: code
  5,896,176 B at first, 5,896,192 B later); no value is carried, filled or interpolated.
- **Time.** `built_at` is the commit time, a proxy for the build time, so the rows are
  `reconstructed` and their provenance says so.
- **Checks.** At the import, all 55 records had full SHAs, unique revisions, and nondecreasing
  times, and every SHA was a commit in main's history (`git merge-base --is-ancestor`). Rows
  that are not ancestors of the commit being built are left out; a row for that commit itself is
  replaced by its measurement. Nothing was excluded on main.

## The producer policy

`config/GV4E69/producer.json` is the policy the site holds for this repo (`config/mvp2005-producer.json`
there). It names the workflow, job, required steps, artifact, target hash and tool tags. The two
copies must stay identical.

Changing `build.yml` changes its Git blob, so the packaging step fails until the new blob is added
to `workflowBlobs` here, and the site rejects the next import until the same blob is approved in
its copy. Bumping a tool tag in `configure.py` works the same way through `tools`. Both are policy
changes: they ship as a PR here and a matching PR on the site.

Get the blob with `git hash-object .github/workflows/build.yml`.
