#!/usr/bin/env python3
"""Check the evidence records of every target (config/<id>/evidence.tsv, format in config/README.md).

    python3 tools/evidence.py check [file...]    default: every target's file

Each row has eight tab-separated columns; addresses are `0x` plus eight upper-case hex digits or
`-`, with an exclusive end after the start; kinds and origins come from the lists below; edge
claims (start_boundary, end_boundary) other than `-` appear only on function, data, unit, assembly and linker rows."""
from pathlib import Path
import re
import sys
try:
    from tools.targets import registry
except ModuleNotFoundError:
    from targets import registry

ROOT=Path(__file__).resolve().parents[1]
COLUMNS=['kind','start','end','subject','origin','start_boundary','end_boundary','evidence']
KINDS={'name','function','data','unit-anchor','unit','type','field','external','compiler','assembly','source-form','linker'}
ORIGINS={'target','signature','related','inferred'}
EDGES={'exact','provisional','open','-'}
EDGE_KINDS={'function','data','unit','assembly','linker'}
ADDRESS=re.compile(r'0x[0-9A-F]{8}')


def check_text(text,name='evidence.tsv'):
    problems=[]
    if '\r' in text:problems.append('%s: carriage returns'%name)
    lines=text.split('\n')
    if lines and lines[-1]=='':lines.pop()
    else:problems.append('%s: no newline at end of file'%name)
    if not lines or lines[0].split('\t')!=COLUMNS:return problems+['%s: header row differs from %s'%(name,'\t'.join(COLUMNS))]
    for number,line in enumerate(lines[1:],2):
        where='%s:%d: '%(name,number);cells=line.split('\t')
        if len(cells)!=len(COLUMNS):problems.append(where+'%d columns, expected %d'%(len(cells),len(COLUMNS)));continue
        kind,start,end,subject,origin,start_edge,end_edge,evidence=cells
        if kind not in KINDS:problems.append(where+'unknown kind '+kind)
        if origin not in ORIGINS:problems.append(where+'unknown origin '+origin)
        for label,value in (('start',start),('end',end)):
            if value!='-' and not ADDRESS.fullmatch(value):problems.append(where+'%s is not 0x plus eight upper-case hex digits or -'%label)
        if start!='-' and end!='-' and ADDRESS.fullmatch(start) and ADDRESS.fullmatch(end) and int(end,16)<=int(start,16):problems.append(where+'end is not after start')
        if end!='-' and start=='-':problems.append(where+'end without start')
        for label,value in (('start_boundary',start_edge),('end_boundary',end_edge)):
            if value not in EDGES:problems.append(where+'%s is not exact, provisional, open or -'%label)
            elif value!='-' and kind not in EDGE_KINDS:problems.append(where+'%s on a %s row; edges belong to function, data, unit, assembly and linker rows'%(label,kind))
        if not subject.strip():problems.append(where+'empty subject')
        if not evidence.strip():problems.append(where+'empty evidence')
    return problems


def check(paths=None,root=ROOT):
    root=Path(root)
    if not paths:
        paths=[root/'config'/t['id']/'evidence.tsv' for t in registry(root/'config/targets.json')['targets'] if t['status']=='active']
    problems=[]
    for path in paths:
        path=Path(path)
        if not path.is_file():problems.append('%s: missing'%path);continue
        problems+=check_text(path.read_text(),str(path).replace(str(root)+'/','',1))
    return problems


if __name__=='__main__':
    if sys.argv[1:2]!=['check']:sys.exit(__doc__)
    found=check(sys.argv[2:])
    print('\n'.join(found[:200]) or 'evidence: no problems')
    if len(found)>200:print('... %d problems in all'%len(found))
    sys.exit(1 if found else 0)
