#!/usr/bin/env python3
"""The one reader of config/targets.json (the site's schema-1 target list): no inferred revision
aliases and no filesystem discovery. An active target is built, verified and measured; planned and
archived targets are listed only.

    python3 tools/targets.py check          every target's files and hashes agree
    python3 tools/targets.py define <id>    the preprocessor define of one target

A target's define is VERSION_<ID> with the id upper-cased and `-` and `.` replaced by `_`
(GAME01-rev0 gives VERSION_GAME01_REV0). It is derived here and passed by configure.py; nothing
stores it."""
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
FIELDS={'id','platform','label','region','revision','sha1','status'}
ID=re.compile(r'[A-Za-z0-9._-]+')
SHA1=re.compile(r'[a-f0-9]{40}')
# Required in config/<id>/ for every active target; the dtk inputs only when the repository has
# configure.py with tools/project.py. A planned or archived target needs README.md only.
ACTIVE_FILES=('build.sha1','evidence.tsv','README.md')
DTK_FILES=('config.yml','splits.txt','symbols.txt')


def registry(path=None):
    value=json.loads(Path(path or ROOT/'config/targets.json').read_text())
    if set(value)!={'schema','defaultTarget','targets'} or value['schema']!=1:raise ValueError('Invalid target registry')
    ids=set()
    for target in value['targets']:
        if set(target)!=FIELDS:raise ValueError('Unknown target fields')
        if not (ID.fullmatch(target['id']) and re.fullmatch(r'[a-z0-9]+',target['platform'])
                and all(isinstance(target[k],str) and target[k].strip() for k in ('label','region','revision'))
                and SHA1.fullmatch(target['sha1'])):raise ValueError('Invalid target identity')
        if target['status'] not in ('active','planned','archived'):raise ValueError('Invalid target status')
        if target['id'] in ids:raise ValueError('Duplicate target')
        ids.add(target['id'])
    if len({define(i) for i in ids})!=len(ids):raise ValueError('Target defines collide')
    if value['defaultTarget'] not in build_targets(value):raise ValueError('Default target is not active')
    return value


def build_targets(value=None):
    value=value or registry()
    return [target['id'] for target in value['targets'] if target['status']=='active']


def select(target_id,value=None):
    value=value or registry()
    matches=[target for target in value['targets'] if target['id']==target_id]
    if len(matches)!=1:raise ValueError('Unknown explicit target: '+target_id)
    return matches[0]


def define(target_id):
    if not ID.fullmatch(target_id):raise ValueError('Invalid target id: '+target_id)
    return 'VERSION_'+target_id.upper().replace('-','_').replace('.','_')


def check(root=ROOT,value=None):
    """Return the problems with each target's files: the three hashes (targets.json, config.yml,
    build.sha1) must agree and every active target must have its files."""
    root=Path(root)
    value=value or registry(root/'config/targets.json')
    dtk=(root/'configure.py').is_file() and (root/'tools/project.py').is_file()
    problems=[]
    for target in value['targets']:
        tid=target['id'];folder=root/'config'/tid
        if not (root/'orig'/tid/'.gitkeep').is_file():problems.append('orig/%s/.gitkeep is missing'%tid)
        if target['status']!='active':
            if not (folder/'README.md').is_file():problems.append('config/%s/README.md is missing'%tid)
            continue
        for name in ACTIVE_FILES+(DTK_FILES if dtk else ()):
            if not (folder/name).is_file():problems.append('config/%s/%s is missing'%(tid,name))
        if (folder/'build.sha1').is_file():
            words=(folder/'build.sha1').read_text().split()
            if not words or words[0]!=target['sha1']:problems.append('config/%s/build.sha1 differs from targets.json'%tid)
        if (folder/'config.yml').is_file():
            found=re.findall(r'^hash:\s*([0-9a-fA-F]+)\s*$',(folder/'config.yml').read_text(),re.M)
            if found!=[target['sha1']]:problems.append('config/%s/config.yml hash differs from targets.json'%tid)
    return problems


def main(argv):
    if argv[:1]==['check'] and len(argv)==1:
        problems=check()
        print('\n'.join(problems) or 'targets: %d listed, every file and hash agrees'%len(registry()['targets']))
        return 1 if problems else 0
    if argv[:1]==['define'] and len(argv)==2:
        select(argv[1]);print(define(argv[1]));return 0
    print(__doc__);return 2


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
