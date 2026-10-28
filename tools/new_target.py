#!/usr/bin/env python3
"""Scaffold config/<id>/ and orig/<id>/ for a target that config/targets.json already lists.

    python3 tools/new_target.py <id> [--original <path under orig/<id>/>]

Writes config/<id>/config.yml (the original's path and hash from the registry), an empty
evidence.tsv with the header row, a README.md stub and orig/<id>/.gitkeep. It refuses an id the
registry does not list and never overwrites a file: a file that already exists is adopted, and left
as it is, only when it is exactly what the tool would write, when it is an empty .gitkeep, or when
it is the README.md of a target whose config/<id>/ holds nothing else (the placeholder of a planned
or archived target, which is prose); anything else that exists stops the tool. The symbols, splits
and build.sha1 come from the toolkit's analysis of the original, by hand; see the Targets chapter
of the guide."""
import argparse
from pathlib import Path
import re
import sys
try:
    from tools.targets import registry,select,build_targets
except ModuleNotFoundError:
    from targets import registry,select,build_targets

ROOT=Path(__file__).resolve().parents[1]
HEADER='kind\tstart\tend\tsubject\torigin\tstart_boundary\tend_boundary\tevidence\n'


def original_path(root,value,fallback='sys/main.dol'):
    """The original's path under orig/<id>/, taken from an active sibling's config.yml."""
    for sibling in build_targets(value):
        text=(root/'config'/sibling/'config.yml')
        if text.is_file():
            m=re.search(r'^object:\s*(\S+)\s*$',text.read_text(),re.M)
            if m:return m.group(1)
    return fallback


def files(target,original):
    tid=target['id']
    config=('object_base: orig/%s\nobject: %s\nhash: %s\nsymbols: config/%s/symbols.txt\nsplits: config/%s/splits.txt\n'
            %(tid,original,target['sha1'],tid,tid))
    readme=('# %s\n\n%s, region %s, disc revision %s. Original SHA-1 `%s` (config/targets.json).\n\n'
            'Status: %s. This directory holds the target\'s own inputs: the toolkit configuration, the '
            'expected hash of the relinked executable and the evidence records. Shared source stays in '
            '`src/` and `include/`.\n'%(tid,target['label'],target['region'],target['revision'],target['sha1'],target['status']))
    return {'config/%s/config.yml'%tid:config,'config/%s/evidence.tsv'%tid:HEADER,
            'config/%s/README.md'%tid:readme,'orig/%s/.gitkeep'%tid:''}


def adoptable(root,path,text,placeholder):
    """An existing file the tool leaves as it is: exactly its own stub, an empty .gitkeep, or the
    README.md that is a planned or archived target's only file."""
    existing=root/path
    if not existing.is_file():return False
    if path.endswith('/.gitkeep'):return existing.read_bytes()==b''
    if path.endswith('/README.md') and placeholder:return True
    return existing.read_text()==text


def scaffold(target_id,root=ROOT,original=None):
    """Returns one line per planned file: `wrote <path>` or `adopted <path>`."""
    root=Path(root);value=registry(root/'config/targets.json');target=select(target_id,value)
    planned=files(target,original or original_path(root,value))
    folder=root/'config'/target_id
    placeholder=folder.is_dir() and [p.name for p in folder.iterdir()]==['README.md']
    adopted=[path for path,text in planned.items() if adoptable(root,path,text,placeholder)]
    refused=[path for path in planned if (root/path).exists() and path not in adopted]
    if refused:raise SystemExit('new_target: refusing to overwrite '+', '.join(refused))
    for path,text in planned.items():
        if path not in adopted:
            (root/path).parent.mkdir(parents=True,exist_ok=True);(root/path).write_text(text)
    lines=[]
    for path in sorted(planned):
        if path in adopted and placeholder and path.endswith('/README.md'):
            lines.append('adopted %s (a placeholder written while the target waited: rewrite it, its status and identity change when the target is activated)'%path)
        else:lines.append('%s %s'%('adopted' if path in adopted else 'wrote',path))
    return lines


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('target');parser.add_argument('--original');args=parser.parse_args()
    try:
        print('\n'.join(scaffold(args.target,original=args.original)))
    except ValueError as error:sys.exit('new_target: '+str(error))
