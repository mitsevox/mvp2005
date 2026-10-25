# The shared-site report

MVP's progress is published on the shared site, https://mitsevox.github.io/games/mvp2005/, through
the site's report-v1 contract (the site repo `mitsevox/mitsevox.github.io`:
`docs/reporting/platform.md` and `contract-v1.md`; the handbook's
[Website chapter](https://mitsevox.github.io/wiki/website-integration/)). The older standalone page
(`docs/progress_page.md`) keeps running until the shared page carries everything it shows.

## How a report is made

Every run of `.github/workflows/build.yml` (job `Build and measure GV4E69`):

1. **Build and verify main.dol**: a fresh build with no build cache. `ninja progress` depends on
   the `main.dol` hash check, so a non-identical build fails here. The step records the measurement
   time right after `ninja`.
2. **Export public report inputs**: `tools/public_report.py summary` turns objdiff's `report.json`
   into `build/public-input/summary.json`; `tools/public_report.py metadata` writes the execution
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

The map, timeline and contributor modules are not supplied yet; the manifest declares them
unsupported.

## The producer policy

`config/GV4E69/producer.json` is the policy the site holds for this repo (`config/mvp2005-producer.json`
there). It names the workflow, job, required steps, artifact, target hash and tool tags. The two
copies must stay identical.

Changing `build.yml` changes its Git blob, so the packaging step fails until the new blob is added
to `workflowBlobs` here, and the site rejects the next import until the same blob is approved in
its copy. Bumping a tool tag in `configure.py` works the same way through `tools`. Both are policy
changes: they ship as a PR here and a matching PR on the site.

Get the blob with `git hash-object .github/workflows/build.yml`.
