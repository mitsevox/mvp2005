#!/usr/bin/env python3
"""Compute affected targets from explicit dependencies; unknown paths fail broad.

config/ci-targets.json lists `shared` patterns (select every active target) and `nonBuild`
patterns (select nothing). The per-target patterns are not listed: every target owns
config/<id>/** and orig/<id>/**, derived here from config/targets.json."""
import argparse
import fnmatch
import json
import os
from pathlib import Path
import re
import subprocess
try:
    from tools.targets import registry,build_targets
except ModuleNotFoundError:
    from targets import registry,build_targets

ROOT=Path(__file__).resolve().parents[1]
SHA=re.compile(r'[a-f0-9]{40}')


def target_patterns(targets):
    return {target['id']:['config/%s/**'%target['id'],'orig/%s/**'%target['id']] for target in targets['targets']}


def affected(paths,targets,dependencies,force=False):
    active=set(build_targets(targets))
    if set(dependencies)!={'schemaVersion','shared','nonBuild'} or dependencies['schemaVersion']!=1:
        raise ValueError('Invalid CI dependency map')
    patterns=[dependencies['shared'],dependencies['nonBuild']]
    if any(not isinstance(group,list) or any(not isinstance(p,str) or not p or p.startswith('/') or '..' in p.split('/') for p in group) for group in patterns):raise ValueError('Unsafe CI dependency patterns')
    if force:return sorted(active)
    owned=target_patterns(targets)
    selected=set()
    def matches(path,patterns):return any(fnmatch.fnmatchcase(path,p) for p in patterns)
    for path in paths:
        if not path or path.startswith('/') or '..' in path.split('/'):raise ValueError('Unsafe changed path')
        if matches(path,dependencies['shared']):selected.update(active);continue
        owners={key for key,patterns in owned.items() if matches(path,patterns)}
        if owners:selected.update(owners&active);continue
        if matches(path,dependencies['nonBuild']):continue
        # Missing dependency knowledge must never silently skip validation.
        selected.update(active)
    return sorted(selected)


def changed_paths(base,head):
    if not SHA.fullmatch(base) or not SHA.fullmatch(head):raise ValueError('Diff endpoints must be full commit SHAs')
    # --no-renames yields both old and new paths, including deletes.
    raw=subprocess.check_output(['git','diff','--no-renames','--name-only','-z',base,head],cwd=ROOT)
    return [path.decode('utf-8') for path in raw.split(b'\0') if path]


def pr_base(pr,head,root=ROOT):
    """The commit a pull request's test merge commit (GITHUB_SHA) was built on: its first parent,
    when its second parent is the pull request's head. The event's base.sha can lag the base
    branch (it is the pull request's stored base, not the branch tip the merge was built on), and
    diffing it against the merge commit reads the base's newer commits as the pull request's
    own. Anything other than such a merge commit falls back to the merge base of the two."""
    base,tip=pr['base']['sha'],pr['head']['sha']
    if not all(SHA.fullmatch(sha or '') for sha in (base,tip,head)):raise ValueError('Diff endpoints must be full commit SHAs')
    parents=subprocess.check_output(['git','rev-list','--parents','-n','1',head],cwd=root).decode().split()[1:]
    if len(parents)==2 and parents[1]==tip:return parents[0]
    return subprocess.check_output(['git','merge-base',base,head],cwd=root).decode().strip()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--force-all',action='store_true');args=parser.parse_args()
    event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    kind=os.environ['GITHUB_EVENT_NAME'];head=os.environ['GITHUB_SHA']
    base=event.get('pull_request',{}).get('base',{}).get('sha') if kind=='pull_request' else event.get('before')
    force=args.force_all or kind=='workflow_dispatch' or not base or base=='0'*40
    if kind=='pull_request' and not force:base=pr_base(event['pull_request'],head)
    paths=[] if force else changed_paths(base,head)
    targets=affected(paths,registry(),json.loads((ROOT/'config/ci-targets.json').read_text()),force)
    result={'include':[{'target':target} for target in targets]}
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'],'a') as out:
            out.write('matrix='+json.dumps(result,separators=(',',':'))+'\n')
            out.write('has_targets='+str(bool(targets)).lower()+'\n')
    print(json.dumps({'targets':targets,'changedPaths':paths,'forced':force},indent=2))


if __name__=='__main__':main()
