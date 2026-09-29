#!/usr/bin/env bash
# One-time setup of a cloud (Linux) session for this repo. Run from the repo root:
#     bash tools/cloud/setup.sh [VERSION]
# Needs the owner's secret MVP_BUILD_TOKEN in the environment (tools/cloud/README.md).
# Fetches: main.dol from the private build container; the compilers/tools (configure.py downloads
# them, as in CI); decomp-permuter and m2c (public GitHub) beside the repo.
# Taken from tw2004's tools/cloud/setup.sh.
set -euo pipefail
cd "$(dirname "$0")/../.."
PARENT="$(cd .. && pwd)"

command -v ninja >/dev/null || { echo "installing ninja"; pip install --quiet ninja; }
python3 -m pip install --quiet pycparser toml Levenshtein cxxfilt 2>/dev/null || true   # permuter deps

if ! ls orig/*/sys/main.dol >/dev/null 2>&1; then
    python3 tools/cloud/fetch_orig.py "$@"
fi

mkdir -p "$PARENT/tools" "$PARENT/scratch/mvp/agents" "$PARENT/mvp2005-agents"
[ -d "$PARENT/tools/decomp-permuter" ] || git clone --quiet --depth 1 https://github.com/simonlindholm/decomp-permuter "$PARENT/tools/decomp-permuter"
[ -d "$PARENT/tools/m2c" ] || git clone --quiet --depth 1 https://github.com/matt-kempster/m2c "$PARENT/tools/m2c"

python3 configure.py
ninja >/dev/null || ninja                         # on failure, show why
sha1sum -c config/*/build.sha1                    # must print: build/<VERSION>/main.dol: OK
