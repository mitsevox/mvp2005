#!/usr/bin/env python3
"""Print the tools that measure each report, one name=identity per line, for the site's provenance:
the digest-pinned build image from the BUILD_IMAGE environment variable (validate.yml exports the
image it runs in) and the tool versions the repository pins: the tags in configure.py, or, for a
build without configure.py, the `version` fields of the JSON pin files named in PINS. validate.yml
passes this output to the publish action's `tools` input.

    python3 tools/measuring_tools.py            the lines
    python3 tools/measuring_tools.py --verify   first run each VERIFY command inside the image and
                                                require the pinned version in its output

The versions come from the pins, not from the image; --verify is what ties the two together, so a
tool the image carries at another version than the repository pins never publishes as the pin.
Only the version word is verified, as a whole token: a pin `v1.8.3` needs `1.8.3` in the output,
not `1.8.30` and not a `1.8` pin against it. Anything after the version in a pin (a local patch
named by its hash) is not verified, since a patched tool prints its stock version."""
import argparse
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIGURE = ROOT / 'configure.py'
IMAGE = re.compile(r'ghcr\.io/[^@\s]+@sha256:[0-9a-f]{64}')
# PARAMETER: the `config.<name> = "<version>"` lines of configure.py to report, as name=version.
TAGS = {'dtk': 'dtk_tag', 'objdiff': 'objdiff_tag'}
# PARAMETER: for a build without configure.py, the JSON files that pin its tools, each
# {"<name>": {"version": "<version>", ...}, ...}; every entry is reported. Empty for dtk-template.
PINS = []
# PARAMETER: for --verify, how each reported tool prints its version inside the build image. The
# reported version's first word, without a leading `v`, must appear in the output as a whole token
# and the command must exit 0. List every tool whose --version prints the pinned version that way;
# a tool whose pin is not what it prints (binutils pinned as 2.42-2 prints 2.42) cannot be listed.
# dtk-template downloads objdiff at the pinned tag during the build, so only dtk, which the image
# builds, is listed, at the path validate.yml passes to configure.py.
VERIFY = {'dtk': ['/usr/local/bin/dtk', '--version']}


def tools(image=None, configure=None, pins=None):
    image = image if image is not None else os.environ.get('BUILD_IMAGE', '')
    if not IMAGE.fullmatch(image):
        raise SystemExit('measuring_tools: BUILD_IMAGE is not a digest-pinned image reference')
    result = [('build-environment', image)]
    pins = pins if pins is not None else [json.loads((ROOT / path).read_text()) for path in PINS]
    if pins:
        for document in pins:
            for name, pin in document.items():
                if not isinstance(pin, dict) or not isinstance(pin.get('version'), str) or not pin['version']:
                    raise SystemExit('measuring_tools: %s has no version' % name)
                result.append((name, pin['version']))
        return result
    configure = configure if configure is not None else CONFIGURE.read_text()
    for name, tag in TAGS.items():
        m = re.search(r'^config\.%s = "([^"]+)"$' % tag, configure, re.M)
        if not m:
            raise SystemExit('measuring_tools: configure.py has no %s' % tag)
        result.append((name, m.group(1)))
    return result


def verify(result, commands=None):
    """Run each command of `commands` (VERIFY by default) and require the reported version of that
    tool in its output. Returns `result` unchanged; raises SystemExit on the first disagreement."""
    commands = VERIFY if commands is None else commands
    reported = dict(result)
    for name, command in commands.items():
        if name not in reported:
            raise SystemExit('measuring_tools: VERIFY names %s, which is not a reported tool' % name)
        version = reported[name].split()[0].lstrip('v')
        try:
            run = subprocess.run(command, capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise SystemExit('measuring_tools: cannot run %s to verify %s: %s' % (' '.join(command), name, error))
        text = (run.stdout + run.stderr).strip()
        # A whole token: `1.8.3` is not found in `1.8.30`, and `1.8` is not found in `1.8.3`.
        if run.returncode != 0 or not re.search(r'(?<![\w.])v?%s(?![\w.])' % re.escape(version), text):
            raise SystemExit('measuring_tools: %s reports %r (exit %d); the repository pins %s'
                             % (name, text.splitlines()[0] if text else '', run.returncode, reported[name]))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--verify', action='store_true', help='require the pinned versions from the VERIFY commands')
    args = parser.parse_args()
    found = tools()
    if args.verify:
        verify(found)
    print('\n'.join('%s=%s' % pair for pair in found))
