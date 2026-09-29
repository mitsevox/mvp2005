#!/usr/bin/env python3
"""
The public progress page's history (GitHub Pages, fed by CI): one record per build of main.

    python tools/dashboard/pages.py append <history.json> <report.json> <sha> <time> <subject>

append: adds (or replaces, for the same sha) the record of one CI build: sha, date, exact
functions, matched / linked code and data, all from objdiff's report.json. Only report.json
numbers and commit subjects are written: no game data. CI keeps the file on the data-only branch
pages-history (see .github/workflows/pages.yml).
"""
import json, sys

KEYS = ('matched_code', 'complete_code', 'matched_data', 'complete_data', 'total_code', 'total_data',
        'matched_functions', 'total_functions')


def _num(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return 0


def record(report_path, sha, time, subject):
    m = json.load(open(report_path))['measures']
    rec = {'commit': sha[:7], 'sha': sha, 'time': int(time), 'subject': subject, 'report': True}
    rec.update({k: _num(m.get(k)) for k in KEYS})
    rec['exact'] = rec['matched_functions']
    return rec


def load(path):
    try:
        h = json.load(open(path))
        return h if isinstance(h, list) else []
    except (OSError, ValueError):
        return []


def append(history_path, rec):
    h = [r for r in load(history_path) if r.get('sha', r.get('commit')) not in (rec['sha'], rec['commit'])]
    h.append(rec)
    h.sort(key=lambda r: r.get('time', 0))
    json.dump(h, open(history_path, 'w'), indent=0)
    return h


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) == 6 and a[0] == 'append':
        h = append(a[1], record(a[2], a[3], a[4], a[5]))
        print('pages.py append: %s now %d records, latest %s' % (a[1], len(h), a[3][:7]))
    else:
        raise SystemExit(__doc__)
