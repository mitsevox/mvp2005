#!/usr/bin/env python3
"""Check a pull request's declared review tier against what it changes (CONTRIBUTING.md, "Authority
and tiers"). The tier is the first `Tier A`, `Tier B` or `Tier C` in the PR body; what the diff
touches sets the lowest tier it may claim:

    A  config/<id>/splits.txt or symbols.txt, an evidence row with origin `inferred`, or a
       compiler or linker flag line in configure.py (cflags, ldflags, asflags, mw_version)
    B  anything else under src/, include/, extern/ or asm/, or configure.py
    C  everything else

A file moved without a content change counts as unchanged. A declared tier below that floor fails
the check. Outside pull requests the check passes. The floor is a minimum, not a verdict: a
reviewer still raises the tier when the change calls for it."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
ORDER='CBA'
DECLARED=re.compile(r'\bTier\**(?:[:\s]\**)+([ABC])\b')
NAME_FILES=re.compile(r'^config/[^/]+/(splits|symbols)\.txt$')
EVIDENCE=re.compile(r'^config/[^/]+/evidence\.tsv$')
SOURCE=re.compile(r'^(src|include|extern|asm)/')
FLAGS=re.compile(r'cflags|ldflags|asflags|mw_version')


def declared(body):
    m=DECLARED.search(body or '')
    return m.group(1) if m else None


def floor(paths,diff_of):
    """The lowest tier the change may claim, with the reason. diff_of(path) returns the added and
    removed lines of one file."""
    reasons={}
    for path in paths:
        if NAME_FILES.match(path):reasons.setdefault('A',path+' changes names or unit boundaries')
        elif EVIDENCE.match(path):
            for line in diff_of(path):
                fields=line.split('\t')
                if len(fields)==8 and fields[4]=='inferred':reasons.setdefault('A',path+' adds or changes an inferred claim');break
        elif path=='configure.py':
            if any(FLAGS.search(line) for line in diff_of(path)):reasons.setdefault('A','configure.py changes a compiler or linker profile')
            else:reasons.setdefault('B','configure.py changes')
        elif SOURCE.match(path):reasons.setdefault('B',path+' is source')
    for tier in 'AB':
        if tier in reasons:return tier,reasons[tier]
    return 'C','no source, names or profiles change'


def unchanged_moves(base,head):
    """Both paths of every file moved without a content change: a move changes no claim."""
    text=subprocess.check_output(['git','diff','--find-renames=100%','--name-status',base,head],cwd=ROOT).decode('utf-8','replace')
    moved=set()
    for line in text.splitlines():
        fields=line.split('\t')
        if fields[0]=='R100':moved.update(fields[1:3])
    return moved


def git_diff_lines(base,head):
    def diff_of(path):
        text=subprocess.check_output(['git','diff','--no-renames','-U0',base,head,'--',path],cwd=ROOT).decode('utf-8','replace')
        return [line[1:] for line in text.splitlines() if line[:1] in '+-' and not line.startswith(('+++','---'))]
    return diff_of


def main():
    if os.environ.get('GITHUB_EVENT_NAME')!='pull_request':
        print('tier: not a pull request, nothing to check');return 0
    sys.path.insert(0,str(ROOT/'tools'))
    from ci_targets import changed_paths
    pr=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())['pull_request']
    base,head=pr['base']['sha'],os.environ['GITHUB_SHA']
    claim=declared(pr.get('body'))
    moved=unchanged_moves(base,head)
    need,why=floor([p for p in changed_paths(base,head) if p not in moved],git_diff_lines(base,head))
    if claim is None:
        print('tier: the PR body declares no tier; write "Tier %s" (or higher) in its Scope line, because %s'%(need,why));return 1
    if ORDER.index(claim)<ORDER.index(need):
        print('tier: declared Tier %s, but this change needs at least Tier %s: %s'%(claim,need,why));return 1
    print('tier: declared Tier %s; the change needs at least Tier %s (%s)'%(claim,need,why));return 0


if __name__=='__main__':sys.exit(main())
