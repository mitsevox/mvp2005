#!/usr/bin/env python3
"""Check the contributor credits a merge will publish (CONTRIBUTING.md, "Credits"). It does
nothing unless config/site.json sets "contributors": true. Then it checks the PR body's
`Credits:` line (optional; without one the PR author is credited) and every target's
config/<target id>/credits.tsv, and confirms that each login named exists on GitHub, so a bad
credit fails here rather than in the publish step on main. The publish action applies the same
rules (mitsevox/mitsevox.github.io, .github/actions/publish/publish.py)."""
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
LOGIN = re.compile(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?')
LINE = re.compile(r'^Credits:[ \t]*(.*)$', re.M)
ADDRESS = re.compile(r'0x[0-9A-F]{8}')


class CreditError(Exception):
    pass


def credits_line(body):
    """The logins a PR body's `Credits:` line names, or None when it has none. `@` is optional."""
    match = LINE.search(body or '')
    if not match:
        return None
    logins = [name.strip().lstrip('@') for name in match.group(1).split(',') if name.strip()]
    if not logins:
        raise CreditError('the Credits line names nobody')
    if not all(LOGIN.fullmatch(login) for login in logins):
        raise CreditError('the Credits line names an invalid login: %s' % match.group(1))
    if len(set(logins)) != len(logins):
        raise CreditError('the Credits line names someone twice')
    return logins


def credits_tsv(path):
    """address, logins (comma-separated), reason; blank lines and # comments allowed."""
    result = {}
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip() or line.startswith('#'):
            continue
        where = '%s:%d' % (path, number)
        fields = line.split('\t')
        if len(fields) != 3:
            raise CreditError(where + ': expected address, logins and reason')
        address, logins, reason = fields
        if not ADDRESS.fullmatch(address):
            raise CreditError(where + ': address must be 0x plus eight upper-case hex digits')
        if address in result:
            raise CreditError('%s: %s is listed twice' % (where, address))
        names = [n.strip() for n in logins.split(',')]
        if not all(LOGIN.fullmatch(n) for n in names) or len(set(names)) != len(names):
            raise CreditError('%s: invalid logins %r' % (where, logins))
        if not reason.strip():
            raise CreditError(where + ': a reason is required')
        result[address] = names
    return result


def exists(login, token):
    request = urllib.request.Request('https://api.github.com/users/' + login, headers={
        'Accept': 'application/vnd.github+json', **({'Authorization': 'Bearer ' + token} if token else {})})
    try:
        with urllib.request.urlopen(request, timeout=30):
            return True
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return False
        raise


def main():
    site = json.loads((ROOT / 'config/site.json').read_text())
    if site.get('contributors') is not True:
        print('credits: off (config/site.json)');return 0
    sys.path.insert(0, str(ROOT / 'tools'))
    from targets import registry
    logins = set()
    try:
        for target in registry()['targets']:
            path = ROOT / 'config' / target['id'] / 'credits.tsv'
            if path.exists():
                for names in credits_tsv(path).values():
                    logins.update(names)
        named = None
        if os.environ.get('GITHUB_EVENT_NAME') == 'pull_request':
            pr = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())['pull_request']
            named = credits_line(pr.get('body'))
            logins.update(named or [pr['user']['login']])
    except CreditError as error:
        print('credits: ' + str(error));return 1
    token = os.environ.get('GH_TOKEN')
    missing = sorted(login for login in logins if not exists(login, token))
    if missing:
        print('credits: no GitHub account named %s' % ', '.join(missing));return 1
    if named is None and os.environ.get('GITHUB_EVENT_NAME') == 'pull_request':
        print('credits: no Credits line; this merge credits the PR author')
    print('credits: %d login(s) checked' % len(logins));return 0


if __name__ == '__main__':sys.exit(main())
