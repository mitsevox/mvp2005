#!/usr/bin/env python3
"""Read the shared source as one target compiles it. Version differences live in shared files
under `#if VERSION_<DEFINE>` blocks (tools/targets.py derives the define from the target id) and
the group macros of include/version.h; this tool resolves exactly those directives and nothing else.

    view  --target <id> <file>              the file as that target compiles it
    diff  --target <a> --target <b> <file>  unified diff between two targets' views
    check [path...]                          default: src/, include/ and configure.py

`check` fails on a VERSION_ token that is not a known define or group, a MatchingFor argument that
is not a known target id, a version condition mixed with other macros, and any use of
BUILD_VERSION in source (it stays defined for dtk-template and is never read).

A version condition names the targets it includes. A branch that a target listed later would take,
a condition that holds when every version token is false (`!VERSION_X`, `!GROUP`) or the `#else`
of a chain no condition of which does, covers every target not named. With two targets listed it
is the other target's branch and `check` only warns; from the third listed target on it is an
error, so the pull request that lists a third target makes every such block explicit. `view` and
`diff` resolve such branches like any other."""
import argparse
import difflib
from pathlib import Path
import re
import sys
try:
    from tools.targets import registry,define
except ModuleNotFoundError:
    from targets import registry,define

ROOT=Path(__file__).resolve().parents[1]
SUFFIXES={'.c','.cpp','.cc','.cxx','.h','.hpp','.hh','.inc','.inl'}
DIRECTIVE=re.compile(r'^\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b\s*(.*?)\s*$')
TOKEN=re.compile(r'\s*(?:(\|\||&&|!|\(|\))|([A-Za-z_][A-Za-z0-9_]*)|(\S))')
IDENT=re.compile(r'\b[A-Za-z_][A-Za-z0-9_]*\b')
GROUP=re.compile(r'^\s*#\s*define\s+([A-Za-z_][A-Za-z0-9_]*)\s+(.+?)\s*$')


def read(path):
    """A source file as text; bytes that are not UTF-8 (a Latin-1 copyright sign) never stop the check."""
    return Path(path).read_text(encoding='utf-8',errors='replace')


def strip_comments(text):
    """Blank C comments, keeping line numbers, so that prose never reads as a token."""
    text=re.sub(r'/\*.*?\*/',lambda m:re.sub(r'[^\n]',' ',m.group(0)),text,flags=re.S)
    return re.sub(r'//[^\n]*','',text)


def tokens(text):
    """Split a condition into (operator, identifier, other) triples; `defined X` reads as X."""
    result=[]
    for op,ident,other in TOKEN.findall(text):
        if ident=='defined':continue
        result.append((op,ident,other))
    return result


class Expression:
    """A boolean expression of identifiers with !, && and || only."""
    def __init__(self,text):
        self.tokens=tokens(text)
        self.identifiers={ident for _,ident,_ in self.tokens if ident}
        self.valid=all(not other for _,_,other in self.tokens) and bool(self.tokens)
        if self.valid:
            self.pos=0
            try:
                self.tree=self._or();self.valid=self.pos==len(self.tokens)
            except (IndexError,ValueError):self.valid=False

    def _peek(self):return self.tokens[self.pos] if self.pos<len(self.tokens) else (None,None,None)
    def _or(self):
        node=self._and()
        while self._peek()[0]=='||':self.pos+=1;node=('or',node,self._and())
        return node
    def _and(self):
        node=self._unary()
        while self._peek()[0]=='&&':self.pos+=1;node=('and',node,self._unary())
        return node
    def _unary(self):
        op,ident,_=self._peek()
        if op=='!':self.pos+=1;return ('not',self._unary())
        if op=='(':
            self.pos+=1;node=self._or()
            if self._peek()[0]!=')':raise ValueError('unbalanced')
            self.pos+=1;return node
        if ident:self.pos+=1;return ('id',ident)
        raise ValueError('unexpected token')

    def evaluate(self,lookup,node=None):
        node=node or self.tree
        if node[0]=='id':return lookup(node[1])
        if node[0]=='not':return not self.evaluate(lookup,node[1])
        left=self.evaluate(lookup,node[1]);right=self.evaluate(lookup,node[2])
        return (left and right) if node[0]=='and' else (left or right)


class Versions:
    def __init__(self,root=ROOT):
        self.root=Path(root)
        value=registry(self.root/'config/targets.json')
        self.ids=[t['id'] for t in value['targets']]
        self.defines={define(i):i for i in self.ids}
        self.groups={};self.errors=[];self.warnings=[]
        header=self.root/'include/version.h'
        if header.is_file():
            for number,line in enumerate(strip_comments(header.read_text()).splitlines(),1):
                m=GROUP.match(line)
                if not m or m.group(1).startswith('VERSION_'):continue
                expr=Expression(m.group(2))
                if not expr.valid or not all(i in self.defines or i in self.groups for i in expr.identifiers):
                    self.errors.append('include/version.h:%d: group %s is not a boolean expression of known VERSION_ tokens and earlier groups'%(number,m.group(1)))
                    continue
                self.groups[m.group(1)]=expr

    def broad(self,message,warnings=None):
        """A branch a target listed later would take: an error from the third listed target on,
        a warning before (with two targets it is the other target's branch)."""
        message+=': it covers every target not named, a target listed later too; name the targets or a group'
        if len(self.ids)>=3:return message
        (self.warnings if warnings is None else warnings).append(message)
        return None

    def known(self,ident):return ident in self.defines or ident in self.groups

    def classify(self,condition):
        """'version' when every identifier is a define or group, 'other' when none is, else 'mixed'."""
        expr=Expression(condition)
        version=[i for i in expr.identifiers if self.known(i) or i.startswith('VERSION_')]
        if not version:return 'other',expr
        if expr.valid and len(version)==len(expr.identifiers):return 'version',expr
        return 'mixed',expr

    def truth(self,target_id):
        def lookup(ident):
            if ident in self.defines:return self.defines[ident]==target_id
            return self.groups[ident].evaluate(lookup)
        return lookup

    def future(self,expr):
        """Whether a condition holds for a target listed later: it is true when every version
        token is false (a group stands for its expression, so a double negation is not broad)."""
        def lookup(ident):return self.groups[ident].evaluate(lookup) if ident in self.groups else False
        return expr.evaluate(lookup)

    def walk(self,lines,target_id=None,warnings=None):
        """Resolve the version directives; yield (output line or None, error or None). A branch a
        target listed later would take (a condition that holds with every version token false, or
        the `#else` of a chain no condition of which does) is reported through `warnings` while two
        targets are listed and as an error from the third on; it is resolved like any other, so
        `view` and `diff` show every target's source whatever `check` says."""
        lookup=self.truth(target_id) if target_id else (lambda ident:False)
        stack=[]  # [resolved, active, taken, taken by a later target] per open conditional
        for number,line in enumerate(lines,1):
            m=DIRECTIVE.match(line);error=None
            if m:
                kind,condition=m.groups()
                if kind in ('ifdef','ifndef'):condition=('!' if kind=='ifndef' else '')+condition;kind='if'
                if kind in ('if','elif'):
                    cls,expr=self.classify(condition)
                    unknown=sorted(i for i in expr.identifiers if i.startswith('VERSION_') and i not in self.defines)
                    if unknown:error='%d: unknown VERSION_ token %s'%(number,', '.join(unknown))
                    elif cls=='mixed':error='%d: version condition mixed with other macros: %s'%(number,condition)
                    elif cls=='version' and kind=='elif' and stack and not stack[-1][0]:error='%d: version #elif inside a non-version conditional'%number
                    if 'BUILD_VERSION' in expr.identifiers:error='%d: BUILD_VERSION is never read in source'%number
                    resolved=cls=='version' and not error and (kind=='if' or (stack and stack[-1][0]))
                    if resolved:
                        earlier=stack[-1][3] if kind=='elif' else False
                        later=not earlier and self.future(expr)
                        if later:error=self.broad('%d: a version condition that holds for every target not named'%number,warnings)
                    if kind=='if':
                        if resolved:
                            value=expr.evaluate(lookup);stack.append([True,value,value,later]);yield None,error;continue
                        stack.append([False,True,True,False])
                    elif resolved:
                        frame=stack[-1];frame[1]=not frame[2] and expr.evaluate(lookup);frame[2]=frame[2] or frame[1];frame[3]=earlier or later
                        yield None,error;continue
                elif stack and stack[-1][0]:
                    if kind=='else':
                        stack[-1][1]=not stack[-1][2]
                        if not stack[-1][3]:error=self.broad('%d: #else after a version condition'%number,warnings)
                        stack[-1][3]=True
                    else:stack.pop()
                    yield None,error;continue
                elif kind=='endif' and stack:stack.pop()
            elif 'BUILD_VERSION' in IDENT.findall(line):
                error='%d: BUILD_VERSION is never read in source'%number
            emit=all(active for resolved,active,_,_ in stack if resolved)
            yield (line if emit else None),error

    def view(self,path,target_id):
        if target_id not in self.ids:raise SystemExit('versions: unknown target '+target_id)
        return [line for line,_ in self.walk(read(path).splitlines(),target_id) if line is not None]

    def check_file(self,path):
        text=strip_comments(read(path));errors=[];warnings=[]
        for _,error in self.walk(text.splitlines(),warnings=warnings):
            if error:errors.append('%s:%s'%(path,error))
        self.warnings+=['%s:%s'%(path,warning) for warning in warnings]
        for number,line in enumerate(text.splitlines(),1):
            for ident in IDENT.findall(line):
                if ident.startswith('VERSION_') and ident not in self.defines and not DIRECTIVE.match(line):
                    errors.append('%s:%d: unknown VERSION_ token %s'%(path,number,ident))
        return errors

    def check_configure(self,path):
        errors=[]
        for number,line in enumerate(Path(path).read_text().splitlines(),1):
            for call in re.findall(r'MatchingFor\(([^)]*)\)',line):
                for literal in re.findall(r'["\']([^"\']*)["\']',call):
                    if literal not in self.ids:errors.append('%s:%d: MatchingFor argument %r is not a known target id'%(path,number,literal))
        return errors

    def check(self,paths=None):
        """The errors; the warnings (broad conditions while two targets are listed) collect in
        self.warnings, with paths relative to the root."""
        errors=list(self.errors);root=self.root;self.warnings=[w for w in self.warnings if w.startswith('include/version.h')]
        paths=[root/p for p in paths] if paths else [root/'src',root/'include',root/'configure.py']
        for path in paths:
            files=sorted(p for p in path.rglob('*') if p.is_file()) if path.is_dir() else [path]
            for file in files:
                if not file.exists():continue
                if file.name=='configure.py':errors+=self.check_configure(file)
                elif file.suffix in SUFFIXES:errors+=self.check_file(file)
        self.warnings=[w.replace(str(root)+'/','',1) for w in self.warnings]
        return [e.replace(str(root)+'/','',1) for e in errors]


def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command',choices=['view','diff','check']);parser.add_argument('paths',nargs='*')
    parser.add_argument('--target',action='append',default=[]);args=parser.parse_intermixed_args()
    versions=Versions()
    if args.command=='check':
        errors=versions.check(args.paths)
        for warning in versions.warnings:print('warning: '+warning)
        print('\n'.join(errors) or 'versions: %d targets, %d groups, no errors'%(len(versions.ids),len(versions.groups)))
        return 1 if errors else 0
    if len(args.paths)!=1 or len(args.target)!={'view':1,'diff':2}[args.command]:parser.error('view takes one --target and one file; diff takes two --target and one file')
    if args.command=='view':print('\n'.join(versions.view(args.paths[0],args.target[0])));return 0
    a,b=(versions.view(args.paths[0],t) for t in args.target)
    for line in difflib.unified_diff(a,b,'%s [%s]'%(args.paths[0],args.target[0]),'%s [%s]'%(args.paths[0],args.target[1]),lineterm=''):print(line)
    return 0


if __name__=='__main__':sys.exit(main())
