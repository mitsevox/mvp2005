#!/usr/bin/env python3
"""Public report-v1 inputs for the shared site (https://mitsevox.github.io/games/mvp2005/).

inputs    objdiff's report.json -> summary.json (the measured code/data bytes and the function
          inventory), map.json (every function as a tile, by unit and by section) and
          timeline.json (the earlier main runs' rows plus this one), the site's report-v1 inputs
          (docs/public_report.md).
metadata  the execution facts the site's packager binds the report to: this checkout's commit
          and tree, the workflow file's Git blob, the pinned tools in configure.py, the Actions
          run and attempt, and the measurement and publication times.

Reads only public outputs (this repo's and the site's published reports); writes no game bytes. Standard library only.
"""
import argparse
import datetime
import hashlib
import io
import json
import math
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = 'mvp2005'
CONSOLE = 'GameCube'
WORKFLOW = '.github/workflows/build.yml'
# Bump when what a number means changes (the site keeps old rows under their own methodology).
METHODOLOGY = 'objdiff-report-v1'
GENERATION = 1
FUNCTION_BASIS = 'objdiff-functions; named = symbol name other than an fn_ address label'
FILE_BASIS = ('objdiff-units, provisional boundaries (not yet checked against EA objects); '
              'named = not a dtk auto-generated address range; exact = named, all code and data bytes matched')
# configure.py's pinned tool tags, in the order the site's producer policy lists them.
TOOL_TAGS = ('binutils_tag', 'compilers_tag', 'dtk_tag', 'objdiff_tag', 'sjiswrap_tag', 'wibo_tag')


def fail(message):
    sys.exit('public_report: ' + message)


def num(value):
    # objdiff writes 64-bit counts as strings and leaves out any measure that is zero.
    return int(value) if value is not None else 0


def fuzzy_bytes(function):
    # Size-weighted similarity; the summary and the map use this same expression so they agree.
    return num(function.get('size')) * min(function.get('fuzzy_match_percent', 0), 100) / 100


def summary(report):
    m = report.get('measures', {})
    total_code, total_data = num(m.get('total_code')), num(m.get('total_data'))
    functions = [f for u in report.get('units', []) for f in u.get('functions', [])]
    if len(functions) != num(m.get('total_functions')):
        fail('report lists %d functions, its measures say %s' % (len(functions), m.get('total_functions')))
    exact = sum(1 for f in functions if f.get('fuzzy_match_percent', 0) >= 100)
    if exact != num(m.get('matched_functions')):
        fail('report has %d exact functions, its measures say %s' % (exact, m.get('matched_functions')))
    named = sum(1 for f in functions if not f['name'].startswith('fn_'))
    # Fuzzy coverage weighted by function size; an exact function counts its whole size once.
    fuzzy = math.fsum(fuzzy_bytes(f) for f in functions)
    matched_code = num(m.get('matched_code'))
    if not matched_code <= fuzzy <= total_code:
        fail('fuzzy code bytes %.1f outside matched %d .. total %d' % (fuzzy, matched_code, total_code))
    return {
        'code': {
            'totalBytes': total_code,
            'linkedBytes': num(m.get('complete_code')),
            'matchedBytes': matched_code,
            'fuzzyEquivalentBytes': fuzzy,
        },
        'data': {
            'totalBytes': total_data,
            'linkedBytes': num(m.get('complete_data')),
            'matchedBytes': num(m.get('matched_data')),
            # objdiff measures no fuzzy similarity for data.
            'fuzzyEquivalentBytes': None,
        },
        'functions': {'total': len(functions), 'exact': exact, 'named': named, 'basis': FUNCTION_BASIS},
        'files': files(report),
    }


def files(report):
    """Units counted as files, provisionally (owner's call, 2026-10-25): most game code still sits
    in dtk's auto-generated address ranges, not EA's objects, until the unit boundaries are checked."""
    units = report.get('units', [])

    def auto(u):
        return u.get('metadata', {}).get('auto_generated', False)

    def exact(u):
        m = u.get('measures', {})
        return all(num(m.get('matched_' + k)) == num(m.get('total_' + k)) for k in ('code', 'data'))
    return {'total': len(units),
            'exact': sum(1 for u in units if exact(u) and not auto(u)),
            'named': sum(1 for u in units if not auto(u)),
            'basis': FILE_BASIS}


CODE_SECTIONS = ('.init', '.text')


def hexaddr(value):
    return '0x%08X' % value


def merged(ranges):
    result = []
    for start, end in sorted(ranges):
        if result and start <= result[-1][1]:
            result[-1][1] = max(result[-1][1], end)
        else:
            result.append([start, end])
    return result


def extents(ranges):
    return [{'start': hexaddr(a), 'end': hexaddr(b)} for a, b in merged(ranges)]


def group(name, kind, children):
    # A group's measures are its children's sums; its extents are their merged ranges.
    node = {'name': name, 'kind': kind,
            'size': sum(c['size'] for c in children),
            'linked': sum(c['linked'] for c in children),
            'matched': sum(c['matched'] for c in children)}
    if kind == 'code':
        node['fuzzy'] = math.fsum(c['fuzzy'] for c in children)
    node['_ranges'] = [tuple(r) for r in merged(r for c in children for r in c['_ranges'])]
    node['mapped_extents'] = extents(node['_ranges'])
    node['children'] = children
    return node


def map_document(report):
    """The site's map-v1 payload: every function as a tile, grouped by source unit (`files`, what
    the page draws) and by DOL section (`sections`, a cross-check over the same bytes).

    objdiff reports data matches per unit, not per section, so a unit's data is one tile spanning
    its data sections, and the `sections` tree holds data as one group of those tiles."""
    code_by_section = {name: [] for name in CODE_SECTIONS}
    files, data_tiles = [], []
    for unit in report.get('units', []):
        m, md = unit.get('measures', {}), unit.get('metadata', {})
        name = unit['name'][len('main/'):] if unit['name'].startswith('main/') else unit['name']
        complete = bool(md.get('complete'))
        sections = [(s['name'], int(s['metadata']['virtual_address']), num(s.get('size')))
                    for s in unit.get('sections', []) if num(s.get('size'))]
        functions = []
        for f in unit.get('functions', []):
            start, size = int(f['metadata']['virtual_address']), num(f.get('size'))
            exact = f.get('fuzzy_match_percent', 0) >= 100
            leaf = {'name': f['name'], 'kind': 'code', 'type': 'function',
                    'address': hexaddr(start), 'size': size,
                    'linked': size if complete else 0, 'matched': size if exact else 0,
                    'fuzzy': fuzzy_bytes(f),
                    'function_address': hexaddr(start), 'original_size': size,
                    '_ranges': [(start, start + size)]}
            functions.append(leaf)
            section = next(s for s, a, n in sections if s in CODE_SECTIONS and a <= start < a + n)
            code_by_section[section].append(dict(leaf))
        if functions:
            files.append(group(name, 'code', functions))
        data = [(a, a + n) for s, a, n in sections if s not in CODE_SECTIONS]
        total_data = num(m.get('total_data'))
        if total_data:
            if sum(b - a for a, b in data) != total_data:
                fail('%s: data sections do not add up to total_data' % name)
            tile = {'name': name, 'kind': 'data', 'size': total_data,
                    'linked': total_data if complete else 0, 'matched': num(m.get('matched_data')),
                    'mapped_extents': extents(data), '_ranges': data}
            files.append(tile)
            data_tiles.append(dict(tile))
    # The page draws tiles in list order: keep them in address order, as in the DOL.
    files.sort(key=lambda f: min(f['_ranges']))
    sections = [group(s, 'code', sorted(fs, key=lambda f: f['_ranges'][0])) for s, fs in code_by_section.items() if fs]
    sections.append(group('Data sections', 'data', sorted(data_tiles, key=lambda t: t['_ranges'][0])))

    def strip(node):
        node.pop('_ranges', None)
        for child in node.get('children', []):
            strip(child)
        return node
    return {'schemaVersion': 1, 'sections': [strip(s) for s in sections], 'files': [strip(f) for f in files]}


# The timeline (timeline-v1). Each main run restores the timeline of the last successful main run
# before it and appends its own row. Main runs queue (build.yml's concurrency group), so every
# row any earlier run published is carried, including rows the site has not imported yet.
SITE_API = 'https://api.github.com/repos/mitsevox/mitsevox.github.io/contents/'
# The site's durable store, then its main branch: each holds a lock naming its accepted package.
SITE_BRANCHES = ('report-data', 'main')
# The retired standalone page's history (its pages.yml), carried over once: docs/public_report.md.
OLD_HISTORY = 'origin/pages-history:history.json'
OLD_HISTORY_SOURCE = ('old progress page, pages-history/history.json blob %s: values from that '
                      "commit's main-build report.json; built_at is the commit time, not the build time")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


def fetch(url, accept, token=True):
    request = urllib.request.Request(url, headers={'Accept': accept})
    if token and os.environ.get('GH_TOKEN'):
        request.add_header('Authorization', 'Bearer ' + os.environ['GH_TOKEN'])
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def package_timeline(manifest_raw, read, where):
    """The timeline rows of one package, its asset checked against its manifest; None when the
    package has no timeline."""
    module = json.loads(manifest_raw)['modules']['timeline']
    if module['status'] != 'supported':
        return None
    raw = read(module['asset']['path'])
    if sha256(raw) != module['asset']['sha256']:
        fail('%s: timeline differs from its manifest' % where)
    return json.loads(raw)['snapshots']


def site_timelines():
    """The timelines the site holds as accepted, from each branch of its store."""
    result = []
    for branch in SITE_BRANCHES:
        def read(path):
            return fetch(SITE_API + path + '?ref=' + branch, 'application/vnd.github.raw')
        entry = json.loads(read('data/reports.lock.json'))['projects'].get(PROJECT)
        if not entry:
            continue
        raw = read(entry['path'] + '/manifest.json')
        if sha256(raw) != entry['manifestSha256']:
            fail('site %s: accepted manifest differs from its lock' % branch)
        rows = package_timeline(raw, lambda path: read(entry['path'] + '/' + path), 'site ' + branch)
        if rows is not None:
            result.append(rows)
    return result


def previous_run():
    """This workflow's last successful main publication before this run, as (run id, the
    public-report artifact's files); None outside Actions or when no such artifact is left."""
    repository, run_id = os.environ.get('GITHUB_REPOSITORY'), os.environ.get('GITHUB_RUN_ID')
    if not (repository and run_id):
        return None
    api = '%s/repos/%s/actions/' % (os.environ.get('GITHUB_API_URL', 'https://api.github.com'), repository)
    runs = json.loads(fetch(api + 'workflows/%s/runs?branch=main&status=success&per_page=20'
                            % os.path.basename(WORKFLOW), 'application/vnd.github+json'))['workflow_runs']
    runs = [r for r in runs if r['event'] in ('push', 'workflow_dispatch') and str(r['id']) != run_id]
    if not runs:
        return None
    run = runs[0]
    artifacts = json.loads(fetch(api + 'runs/%d/artifacts?name=public-report' % run['id'],
                                 'application/vnd.github+json'))['artifacts']
    if not artifacts or artifacts[0]['expired']:
        return None
    # The download redirects to a signed URL, which must not get the token.
    try:
        urllib.request.build_opener(NoRedirect).open(urllib.request.Request(
            api + 'artifacts/%d/zip' % artifacts[0]['id'],
            headers={'Authorization': 'Bearer ' + os.environ.get('GH_TOKEN', '')}), timeout=60)
        fail('run %d: artifact download did not redirect' % run['id'])
    except urllib.error.HTTPError as redirect:
        if redirect.code != 302:
            raise
        location = redirect.headers['Location']
    return run['id'], zipfile.ZipFile(io.BytesIO(fetch(location, '*/*', token=False)))


def old_page_history(revision):
    """The old page's rows that are in this commit's history, as reconstructed rows."""
    blob = git('rev-parse', OLD_HISTORY)
    rows = []
    for r in json.loads(git('show', OLD_HISTORY)):
        if subprocess.call(['git', '-C', ROOT, 'merge-base', '--is-ancestor', r['sha'], revision]):
            continue
        rows.append({'revision': r['sha'],
                     'built_at': datetime.datetime.fromtimestamp(r['time'], datetime.timezone.utc)
                                 .strftime('%Y-%m-%dT%H:%M:%SZ'),
                     'code': {'total': r['total_code'], 'linked': r['complete_code']},
                     'data': {'total': r['total_data'], 'linked': r['complete_data']},
                     'provenance': {'kind': 'reconstructed', 'source': OLD_HISTORY_SOURCE % blob}})
    return rows


def timeline(summary_doc, measured_at):
    """Earlier rows unchanged, then this commit's measured row. A fetch failure stops the build:
    a timeline restarted from nothing would drop rows the site already published."""
    revision = git('rev-parse', 'HEAD')
    accepted = site_timelines()
    previous = previous_run()
    rows = None
    if previous is not None:
        run_id, files = previous
        rows = package_timeline(files.read('manifest.json'), files.read, 'run %d' % run_id)
    if rows is None and accepted:
        rows = max(accepted, key=len)
    if rows is None:
        # The first timeline: the old page's history, with any row for this commit replaced by
        # the measurement.
        rows = [r for r in old_page_history(revision) if r['revision'] != revision]
    if not any(r['revision'] == revision for r in rows):
        rows.append({'revision': revision, 'built_at': measured_at,
                     'code': {k: summary_doc['code'][f] for k, f in (('total', 'totalBytes'), ('linked', 'linkedBytes'))},
                     'data': {k: summary_doc['data'][f] for k, f in (('total', 'totalBytes'), ('linked', 'linkedBytes'))},
                     'provenance': {'kind': 'measured',
                                    'source': 'build.yml run %s' % os.environ.get('GITHUB_RUN_ID', '(local build)')}})
    # The site rejects a timeline that drops or changes a row it accepted; fail here first.
    held = {r['revision']: r for r in rows}
    for old in (r for t in accepted for r in t):
        if held.get(old['revision']) != old:
            fail('timeline lost or changed the row the site accepted for %s' % old['revision'])
    return {'schemaVersion': 1, 'snapshots': rows}


def git(*args):
    return subprocess.check_output(['git', '-C', ROOT, *args], text=True).strip()


def tools():
    text = open(os.path.join(ROOT, 'configure.py')).read()
    result = []
    for tag in TOOL_TAGS:
        m = re.search(r'^config\.%s = "([^"]+)"$' % tag, text, re.M)
        if not m:
            fail('configure.py has no %s' % tag)
        result.append({'name': tag[:-len('_tag')], 'identity': m.group(1)})
    return result


def target(version):
    line = open(os.path.join(ROOT, 'config', version, 'build.sha1')).read().split()
    if not re.fullmatch(r'[0-9a-f]{40}', line[0]):
        fail('config/%s/build.sha1 has no SHA-1' % version)
    return {'id': version, 'console': CONSOLE, 'sha1': line[0]}


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def metadata(version, measured_at):
    if git('status', '--porcelain', '--untracked-files=no'):
        fail('the checkout has local changes; a report must describe a commit')
    env = {k: os.environ.get(k) for k in ('GITHUB_REPOSITORY', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT')}
    if not all(env.values()):
        fail('needs the GitHub Actions run (GITHUB_REPOSITORY, GITHUB_RUN_ID, GITHUB_RUN_ATTEMPT)')
    return {
        'project': PROJECT,
        'repository': env['GITHUB_REPOSITORY'],
        'target': target(version),
        'revision': git('rev-parse', 'HEAD'),
        'tree': git('rev-parse', 'HEAD^{tree}'),
        'methodology': METHODOLOGY,
        'generation': GENERATION,
        'measuredAt': measured_at,
        'publishedAt': now(),
        'tools': tools(),
        'runId': int(env['GITHUB_RUN_ID']),
        'attempt': int(env['GITHUB_RUN_ATTEMPT']),
        'workflowBlob': git('rev-parse', 'HEAD:' + WORKFLOW),
        'mode': 'full',
        'source': None,
    }


def write(path, value):
    with open(path, 'w') as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    s = sub.add_parser('inputs', help='write summary.json, map.json and timeline.json into a new public-input folder')
    s.add_argument('--report', required=True, help="objdiff's report.json")
    s.add_argument('--measured-at', required=True)
    s.add_argument('--output', required=True, help='folder to create')
    sub.add_parser('now', help='print the current UTC time (the measurement time, right after ninja)')
    md = sub.add_parser('metadata', help="write the site packager's execution metadata")
    md.add_argument('--version', default='GV4E69')
    md.add_argument('--measured-at', required=True)
    md.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.command == 'now':
        print(now())
    elif args.command == 'inputs':
        report = json.load(open(args.report))
        os.makedirs(args.output)
        summary_doc = summary(report)
        write(os.path.join(args.output, 'summary.json'), summary_doc)
        write(os.path.join(args.output, 'timeline.json'), timeline(summary_doc, args.measured_at))
        # 24k function tiles: written compact, unlike the small files above.
        with open(os.path.join(args.output, 'map.json'), 'w') as f:
            json.dump(map_document(report), f, separators=(',', ':'), sort_keys=True)
    else:
        write(args.output, metadata(args.version, args.measured_at))


if __name__ == '__main__':
    main()
