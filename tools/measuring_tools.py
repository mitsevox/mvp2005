#!/usr/bin/env python3
"""Print the tools that measure each report, one name=identity per line, for the site's provenance:
the digest-pinned build image from the BUILD_IMAGE environment variable (validate.yml exports the
image it runs in) and the tool tags pinned in configure.py. validate.yml passes this output to the
publish action's `tools` input."""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIGURE = ROOT / 'configure.py'
IMAGE = re.compile(r'ghcr\.io/[^@\s]+@sha256:[0-9a-f]{64}')
# PARAMETER: the `config.<name> = "<version>"` lines of configure.py to report, as name=version.
TAGS = {'dtk': 'dtk_tag', 'objdiff': 'objdiff_tag'}


def tools(image=None, configure=None):
    image = image if image is not None else os.environ.get('BUILD_IMAGE', '')
    if not IMAGE.fullmatch(image):
        raise SystemExit('measuring_tools: BUILD_IMAGE is not a digest-pinned image reference')
    configure = configure if configure is not None else CONFIGURE.read_text()
    result = [('build-environment', image)]
    for name, tag in TAGS.items():
        m = re.search(r'^config\.%s = "([^"]+)"$' % tag, configure, re.M)
        if not m:
            raise SystemExit('measuring_tools: configure.py has no %s' % tag)
        result.append((name, m.group(1)))
    return result


if __name__ == '__main__':
    print('\n'.join('%s=%s' % pair for pair in tools()))
