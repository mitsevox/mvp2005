#!/usr/bin/env python3
"""The scope of every Matching declaration in configure.py: the targets a unit is declared to link
on. `Object(Matching, ...)` claims every active target, including one activated later, and a target
that has not yet linked a unit byte-identically must not inherit that claim.

    python3 tools/matching_scope.py show                 one line per unit: all, none, the targets,
                                                         or unclassified
    python3 tools/matching_scope.py pin <id> [<id>...]   before a new target is activated: rewrite
                                                         every unconditional Matching to MatchingFor(<ids>)
    python3 tools/matching_scope.py check                once two or more targets are active: fail on
                                                         a unit declared Matching for every target

`check` runs in CI (Tool tests and the scaffold check). With one active target plain Matching is the
normal form and there is nothing to check; with two or more, a unit declared Matching without
naming targets claims every active target, one activated later included, and an unclassified
Object call or a use of Matching outside the four forms hides what it claims, so each is a failure
until the claim names its targets with MatchingFor(...), a hand edit: `pin` is for the moment
before a target is activated, and afterwards the tool cannot know which targets a unit links on.

`pin` names every target active so far, all of them: pinning to a subset would silently drop
another active target's claims. For the targets named nothing changes: MatchingFor(<ids>) is true
exactly where Matching was, so configure.py generates the same build for each of them; after the
rewrite, run `python3 configure.py --version <id>` for each and compare the build.ninja and
objdiff.json it writes (under build/<id>/, or at the repository root with stock dtk-template, where
the next configure overwrites them) with the ones from before; objdiff.json needs the original at
hand. For the new target every unit is then NonMatching until it is proven. NonMatching, Equivalent and existing
MatchingFor declarations are left alone. The file is read as Python tokens, so comments and strings
never count; an Object call whose first argument is none of the four (an alias, True) is
unclassified, and a use of the identifier Matching anywhere but as that first argument or in its
definition is another use: both stop the rewrite and are listed, because the tool cannot know what
they claim, so they are pinned by hand first."""
import argparse
import ast
import io
from pathlib import Path
import sys
import tokenize
try:
    from tools.targets import registry,build_targets
except ModuleNotFoundError:
    from targets import registry,build_targets

ROOT=Path(__file__).resolve().parents[1]
LINKED={'Matching':'all','NonMatching':'none','Equivalent':'none'}


def calls(text):
    """From the tokens of configure.py: [(row, unit, scope, span)] for every Object(...) call, where
    scope is 'all', 'none', the sorted target ids of a MatchingFor, or 'unclassified', and span is
    the (start column, end column) of an unconditional Matching on that row or None; and [(row,
    line)] for every other use of the identifier Matching."""
    tokens=list(tokenize.generate_tokens(io.StringIO(text).readline))
    lines=text.splitlines()
    found=[];other=[];first=set();i=0
    while i<len(tokens):
        t=tokens[i]
        if t.type==tokenize.NAME and t.string=='Object' and i+2<len(tokens) and tokens[i+1].string=='(':
            arg=tokens[i+2];k=i+3;scope='unclassified';span=None
            if arg.type==tokenize.NAME and arg.string in LINKED:
                scope=LINKED[arg.string]
                if arg.string=='Matching':span=(arg.start[1],arg.end[1]);first.add(arg.start)
            elif arg.type==tokenize.NAME and arg.string=='MatchingFor' and k<len(tokens) and tokens[k].string=='(':
                ids=[];depth=0
                while k<len(tokens):
                    tk=tokens[k];k+=1
                    if tk.string=='(':depth+=1
                    elif tk.string==')':
                        depth-=1
                        if depth==0:break
                    elif tk.type==tokenize.STRING:ids.append(ast.literal_eval(tk.string))
                scope=sorted(ids)
            unit=None;depth=0
            while k<len(tokens):
                tk=tokens[k]
                if tk.string=='(':depth+=1
                elif tk.string==')':
                    if depth==0:break
                    depth-=1
                elif tk.type==tokenize.STRING and depth==0:unit=ast.literal_eval(tk.string);break
                k+=1
            found.append((arg.start[0],unit,scope,span))
            i+=3;continue
        if t.type==tokenize.NAME and t.string=='Matching' and t.start not in first:
            following=tokens[i+1].string if i+1<len(tokens) else ''
            if not (t.start[1]==0 and following=='='):  # the definition, `Matching = True`
                other.append((t.start[0],lines[t.start[0]-1].strip()))
        i+=1
    return found,other


def scopes(text):
    return [(row,unit,scope) for row,unit,scope,_ in calls(text)[0]]


def other_uses(text):
    return ['%d: %s'%(row,line) for row,line in calls(text)[1]]


def pin(text,ids):
    """(new text, count): every Object(Matching, ...) becomes Object(MatchingFor(<ids>), ...)."""
    arguments='MatchingFor(%s)'%', '.join('"%s"'%i for i in ids)
    lines=text.split('\n');count=0
    spans=[(row,span) for row,_,_,span in calls(text)[0] if span]
    for row,(start,end) in sorted(spans,key=lambda s:(s[0],-s[1][0])):
        line=lines[row-1];lines[row-1]=line[:start]+arguments+line[end:];count+=1
    return '\n'.join(lines),count


def check(root=ROOT):
    """The problems with configure.py's claims once two or more targets are active, as strings:
    a unit declared Matching for every target, an Object call the tool cannot classify, a use of
    Matching outside the four forms. Empty with one active target or without a configure.py."""
    root=Path(root);active=build_targets(registry(root/'config/targets.json'))
    path=root/'configure.py'
    if len(active)<2 or not path.is_file():return []
    try:found,other=calls(path.read_text())
    except (tokenize.TokenError,SyntaxError,ValueError) as error:return ['configure.py: cannot read as Python: %s'%error]
    problems=[]
    for row,unit,scope,_ in found:
        if scope=='all':problems.append('configure.py:%d: %s is declared Matching for every target; %s are active: name the targets it links on with MatchingFor(...)'%(row,unit,', '.join(active)))
        elif scope=='unclassified':problems.append('configure.py:%d: %s: Object call whose first argument is not Matching, NonMatching, Equivalent or MatchingFor'%(row,unit))
    for row,line in other:problems.append('configure.py:%d: Matching is used outside Object(Matching, ...): %s'%(row,line))
    return problems


def run(root,command,ids=()):
    root=Path(root)
    if command=='check':
        problems=check(root)
        if problems:raise SystemExit('\n'.join(problems))
        return ['matching_scope: no problems']
    active=build_targets(registry(root/'config/targets.json'))
    path=root/'configure.py'
    try:text=path.read_text()
    except OSError as error:raise SystemExit('matching_scope: '+str(error))
    try:found,other=calls(text)
    except (tokenize.TokenError,SyntaxError,ValueError) as error:raise SystemExit('matching_scope: cannot read configure.py as Python: %s'%error)
    if command=='show':
        return ['%s: %s'%(unit,scope if isinstance(scope,str) else ', '.join(scope)) for _,unit,scope,_ in found]
    if not ids:raise SystemExit('matching_scope: pin needs the targets that have proven the units')
    if sorted(set(ids))!=sorted(active):
        raise SystemExit('matching_scope: pin names %s; the active targets are %s: name every target active before the new one, all of them'
                         %(', '.join(ids),', '.join(active)))
    if 'def MatchingFor' not in text:raise SystemExit('matching_scope: configure.py defines no MatchingFor')
    unclassified=['%d: %s'%(row,unit) for row,unit,scope,_ in found if scope=='unclassified']
    if unclassified:raise SystemExit('matching_scope: Object calls whose first argument is not Matching, NonMatching, Equivalent or MatchingFor; pin these by hand first:\n'+'\n'.join(unclassified))
    uses=other_uses(text)
    if uses:raise SystemExit('matching_scope: Matching is used outside Object(Matching, ...); pin these by hand first:\n'+'\n'.join(uses))
    new,count=pin(text,sorted(set(ids)))
    if count:path.write_text(new)
    return ['pinned %d Matching declaration(s) to MatchingFor(%s); NonMatching, Equivalent and MatchingFor declarations untouched'%(count,', '.join(sorted(set(ids)))),
            'for each of %s: run `python3 configure.py --version <id>` and compare the build.ninja and objdiff.json it writes '
            '(under build/<id>/, or at the repository root with stock dtk-template) with the ones from before the rewrite; '
            'the rewrite changes nothing there, and objdiff.json needs the original at hand'%', '.join(sorted(set(ids)))]


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command',choices=['show','pin','check']);parser.add_argument('targets',nargs='*')
    args=parser.parse_args()
    try:print('\n'.join(run(ROOT,args.command,args.targets)))
    except ValueError as error:sys.exit('matching_scope: '+str(error))
