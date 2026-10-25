#!/usr/bin/env python3
"""Public report-v1 inputs for the shared site (https://mitsevox.github.io/games/mvp2005/).

summary   objdiff's report.json -> summary.json, the measured code/data bytes and the function
          inventory the site's report-v1 contract asks for (docs/public_report.md).
metadata  the execution facts the site's packager binds the report to: this checkout's commit
          and tree, the workflow file's Git blob, the pinned tools in configure.py, the Actions
          run and attempt, and the measurement and publication times.

Reads only public outputs; writes no game bytes. Standard library only.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = 'mvp2005'
CONSOLE = 'GameCube'
WORKFLOW = '.github/workflows/build.yml'
# Bump when what a number means changes (the site keeps old rows under their own methodology).
METHODOLOGY = 'objdiff-report-v1'
GENERATION = 1
FUNCTION_BASIS = 'objdiff-functions; named = symbol name other than an fn_ address label'
# configure.py's pinned tool tags, in the order the site's producer policy lists them.
TOOL_TAGS = ('binutils_tag', 'compilers_tag', 'dtk_tag', 'objdiff_tag', 'sjiswrap_tag', 'wibo_tag')


def fail(message):
    sys.exit('public_report: ' + message)


def num(value):
    # objdiff writes 64-bit counts as strings and leaves out any measure that is zero.
    return int(value) if value is not None else 0


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
    fuzzy = sum(num(f.get('size')) * min(f.get('fuzzy_match_percent', 0), 100) / 100 for f in functions)
    matched_code = num(m.get('matched_code'))
    if not matched_code <= fuzzy <= total_code:
        fail('fuzzy code bytes %.1f outside matched %d .. total %d' % (fuzzy, matched_code, total_code))
    return {
        'code': {
            'totalBytes': total_code,
            'linkedBytes': num(m.get('complete_code')),
            'matchedBytes': matched_code,
            'fuzzyEquivalentBytes': round(fuzzy, 3),
        },
        'data': {
            'totalBytes': total_data,
            'linkedBytes': num(m.get('complete_data')),
            'matchedBytes': num(m.get('matched_data')),
            # objdiff measures no fuzzy similarity for data.
            'fuzzyEquivalentBytes': None,
        },
        'functions': {'total': len(functions), 'exact': exact, 'named': named, 'basis': FUNCTION_BASIS},
        # File (unit) boundaries are not yet backed by original-boundary evidence for every unit.
        'files': None,
    }


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
    s = sub.add_parser('summary', help='write summary.json into a new public-input folder')
    s.add_argument('--report', required=True, help="objdiff's report.json")
    s.add_argument('--output', required=True, help='folder to create')
    sub.add_parser('now', help='print the current UTC time (the measurement time, right after ninja)')
    md = sub.add_parser('metadata', help="write the site packager's execution metadata")
    md.add_argument('--version', default='GV4E69')
    md.add_argument('--measured-at', required=True)
    md.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.command == 'now':
        print(now())
    elif args.command == 'summary':
        os.makedirs(args.output)
        write(os.path.join(args.output, 'summary.json'), summary(json.load(open(args.report))))
    else:
        write(args.output, metadata(args.version, args.measured_at))


if __name__ == '__main__':
    main()
