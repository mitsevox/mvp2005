"""The kit tools against this repository's registry and against scratch trees. Run from the
repository root: python3 -m unittest discover -s tests -p 'test_*.py'"""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from tools.targets import registry,select,build_targets,define,check as check_targets
from tools.ci_targets import affected,target_patterns,pr_base
from tools.evidence import check_text,COLUMNS
from tools.measuring_tools import tools as measuring_tools,verify
from tools.new_target import scaffold
from tools.versions import Versions
from tools.tier import declared,floor
from tools.credits import credits_line,credits_tsv,CreditError

ROOT=Path(__file__).resolve().parents[1]
DIGEST='ghcr.io/owner/game-build@sha256:'+'0'*64


def scratch(tmp):
    """A root with this repository's registry and a scaffolded config/<id>/ per target."""
    root=Path(tmp);(root/'config').mkdir();shutil.copy(ROOT/'config/targets.json',root/'config/targets.json')
    for target in registry()['targets']:
        scaffold(target['id'],root)
        (root/'config'/target['id']/'build.sha1').write_text(target['sha1']+'  build/main.dol\n')
    return root


class Targets(unittest.TestCase):
    def test_registry_is_valid_and_rejects_broken_entries(self):
        value=registry()
        self.assertIn(value['defaultTarget'],build_targets(value))
        for target in value['targets']:
            self.assertEqual(select(target['id'])['status'],target['status'])
        with self.assertRaises(ValueError):select('no-such-target')
        for change in ({'status':'live'},{'platform':'GameCube'},{'sha1':'A'*40},{'extra':1}):
            broken=copy.deepcopy(value);broken['targets'][0].update(change)
            with self.subTest(change=change),tempfile.NamedTemporaryFile('w',suffix='.json') as f:
                json.dump(broken,f);f.flush()
                with self.assertRaises(ValueError):registry(f.name)

    def test_define_derives_from_the_id(self):
        self.assertEqual(define('GAME01-rev0'),'VERSION_GAME01_REV0')
        self.assertEqual(define('SLUS-20349-v1.01'),'VERSION_SLUS_20349_V1_01')
        with self.assertRaises(ValueError):define('bad id')
        self.assertEqual(len({define(t['id']) for t in registry()['targets']}),len(registry()['targets']))

    def test_check_finds_missing_files_and_disagreeing_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=scratch(tmp)
            self.assertEqual(check_targets(root),[])
            active=build_targets()[0]
            (root/'config'/active/'build.sha1').write_text('f'*40+'  build/main.dol\n')
            (root/'config'/active/'evidence.tsv').unlink()
            problems=check_targets(root)
            self.assertIn('config/%s/build.sha1 differs from targets.json'%active,problems)
            self.assertIn('config/%s/evidence.tsv is missing'%active,problems)

    def test_changed_paths_select_their_targets(self):
        value=registry();deps=json.loads((ROOT/'config/ci-targets.json').read_text())
        active=build_targets(value)
        self.assertEqual(set(deps),{'schemaVersion','shared','nonBuild'})
        self.assertEqual(affected(['src/unit.cpp'],value,deps),active)
        self.assertEqual(affected(['docs/guide.md'],value,deps),[])
        self.assertEqual(affected(['unclassified/path'],value,deps),active)
        self.assertEqual(affected([],value,deps,force=True),active)
        for target in value['targets']:
            expected=[target['id']] if target['status']=='active' else []
            with self.subTest(target=target['id']):
                self.assertEqual(target_patterns(value)[target['id']],['config/%s/**'%target['id'],'orig/%s/**'%target['id']])
                self.assertEqual(affected(['config/%s/splits.txt'%target['id']],value,deps),expected)
                self.assertEqual(affected(['orig/%s/sys/main.dol'%target['id']],value,deps),expected)
        with self.assertRaises(ValueError):affected(['../escape'],value,deps)
        with self.assertRaises(ValueError):affected([],value,dict(deps,targets={}))

    def test_pull_request_diff_starts_where_the_merge_commit_was_built(self):
        # The event's base.sha can lag the base branch the test merge commit was built on (and
        # the merge commit can lag it too): either way the diff starts at the merge's first parent.
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            git=lambda *a:subprocess.check_output(['git','-c','user.name=t','-c','user.email=t@t',*a],cwd=tmp).decode().strip()
            git('init','-q','-b','main')
            def commit(path):
                (Path(tmp)/path).parent.mkdir(parents=True,exist_ok=True);(Path(tmp)/path).write_text(path)
                git('add','-A');git('commit','-q','-m',path);return git('rev-parse','HEAD')
            old=commit('src/a.c')
            git('switch','-q','-c','pr');commit('docs/b.md')
            tip=git('rev-parse','HEAD')
            git('switch','-q','main');new=commit('config/GAME01-rev0/evidence.tsv')
            git('switch','-q','--detach',old);git('merge','-q','--no-ff','-m','test merge','pr');on_old=git('rev-parse','HEAD')
            git('switch','-q','--detach',new);git('merge','-q','--no-ff','-m','test merge','pr');on_new=git('rev-parse','HEAD')
            changed=lambda b,h:git('diff','--name-only',b,h).split()
            pr=lambda base:{'base':{'sha':base},'head':{'sha':tip}}
            # base.sha one commit behind a merge built on the branch tip (n100f#114's case).
            self.assertEqual(pr_base(pr(old),on_new,tmp),new)
            self.assertEqual(changed(pr_base(pr(old),on_new,tmp),on_new),['docs/b.md'])
            self.assertIn('config/GAME01-rev0/evidence.tsv',changed(old,on_new))  # what the old diff saw
            # A merge built on an older base than base.sha, and both up to date.
            self.assertEqual(pr_base(pr(new),on_old,tmp),old)
            self.assertEqual(pr_base(pr(new),on_new,tmp),new)
            # Not a merge commit of the pull request's head: the merge base.
            self.assertEqual(pr_base(pr(new),tip,tmp),old)
        with self.assertRaises(ValueError):pr_base({'base':{'sha':'main'},'head':{'sha':'0'*40}},'0'*40)

    def test_new_target_refuses_unknown_ids_and_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=scratch(tmp);first=registry()['targets'][0]['id']
            self.assertEqual((root/'config'/first/'evidence.tsv').read_text(),'\t'.join(COLUMNS)+'\n')
            self.assertIn('hash: '+select(first)['sha1'],(root/'config'/first/'config.yml').read_text())
            with self.assertRaises(ValueError):scaffold('no-such-target',root)
            # Its own files are adopted; a file with other content is never overwritten.
            self.assertTrue(all(line.startswith('adopted ') for line in scaffold(first,root)))
            (root/'config'/first/'evidence.tsv').write_text('\t'.join(COLUMNS)+'\nname\t-\t-\tx\tinferred\t-\t-\te\n')
            with self.assertRaises(SystemExit):scaffold(first,root)

    def test_new_target_adopts_the_placeholder_of_a_target_listed_but_not_built(self):
        # A planned or archived target holds config/<id>/README.md (prose) and orig/<id>/.gitkeep
        # before it is scaffolded; both are kept, and the rest is written beside them.
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'config').mkdir();shutil.copy(ROOT/'config/targets.json',root/'config/targets.json')
            later=[t['id'] for t in registry()['targets'] if t['status']!='active']
            if not later:self.skipTest('the registry lists no planned or archived target')
            tid=later[0];folder=root/'config'/tid;folder.mkdir()
            (folder/'README.md').write_text('# %s\n\nKnown identity only; no verified build.\n'%tid)
            (root/'orig'/tid).mkdir(parents=True);(root/'orig'/tid/'.gitkeep').write_bytes(b'')
            lines=scaffold(tid,root)
            self.assertEqual(lines[1:],['wrote config/%s/config.yml'%tid,'wrote config/%s/evidence.tsv'%tid,'adopted orig/%s/.gitkeep'%tid])
            self.assertTrue(lines[0].startswith('adopted config/%s/README.md (a placeholder'%tid),lines[0])
            self.assertIn('rewrite it',lines[0])
            self.assertIn('Known identity only',(folder/'README.md').read_text())
            # With anything else beside it, the README is real content: refused unless it is the stub.
            other=root/'config'/(tid+'-x');shutil.rmtree(folder);folder.mkdir()
            (folder/'README.md').write_text('# prose\n');(folder/'splits.txt').write_text('')
            with self.assertRaises(SystemExit):scaffold(tid,root)

    def test_versions_view_diff_and_check(self):
        value=registry();ids=[t['id'] for t in value['targets']];first=define(ids[0])
        with tempfile.TemporaryDirectory() as tmp:
            root=scratch(tmp);(root/'include').mkdir();(root/'src').mkdir()
            (root/'include/version.h').write_text('#define GROUP_ALL (%s)\n'%' || '.join(define(i) for i in ids))
            (root/'src/a.c').write_text('int a;\n#if %s\nint first;\n#else\nint other;\n#endif\n#ifdef DEBUG\n#if GROUP_ALL\nint all;\n#endif\n#endif\n'%first)
            (root/'src/latin1.c').write_bytes(b'/* \xa9 1999 */\nint c;\n')
            versions=Versions(root)
            self.assertEqual(versions.check(),[])
            self.assertEqual(versions.view(root/'src/a.c',ids[0]),['int a;','int first;','#ifdef DEBUG','int all;','#endif'])
            if len(ids)>1:self.assertIn('int other;',versions.view(root/'src/a.c',ids[1]))
            (root/'src/b.c').write_text('#if VERSION_NOPE\n#endif\n#if %s && DEBUG\n#endif\n#if BUILD_VERSION > 0\n#endif\n'%first)
            (root/'configure.py').write_text('Object(MatchingFor("not-a-target"), "a.c")\n')
            errors=versions.check()
            self.assertEqual(len(errors),4,errors)
            self.assertTrue(any('unknown VERSION_ token VERSION_NOPE' in e for e in errors))
            self.assertTrue(any('mixed with other macros' in e for e in errors))
            self.assertTrue(any('BUILD_VERSION' in e for e in errors))
            self.assertTrue(any('not-a-target' in e for e in errors))

    def test_broad_version_conditions_warn_with_two_targets_and_fail_from_the_third(self):
        # A branch a target listed later would take: a condition that holds with every version
        # token false, or the #else of a chain none of whose conditions does.
        def root_with(tmp,count):
            root=Path(tmp);(root/'config').mkdir();(root/'include').mkdir();(root/'src').mkdir()
            targets=[{'id':'GAME01-rev%d'%n,'platform':'gamecube','label':'GAME01','region':'USA','revision':str(n),
                      'sha1':'%040x'%(n+1),'status':'active' if n==0 else 'planned'} for n in range(count)]
            (root/'config/targets.json').write_text(json.dumps({'schema':1,'defaultTarget':'GAME01-rev0','targets':targets}))
            (root/'include/version.h').write_text('#define NOT_FIRST (!VERSION_GAME01_REV0)\n#define BOTH (VERSION_GAME01_REV0 || VERSION_GAME01_REV1)\n')
            (root/'src/a.c').write_text(
                '#if VERSION_GAME01_REV0\nint a;\n#else\nint b;\n#endif\n'                      # 3: the else is broad
                '#if !VERSION_GAME01_REV0\nint c;\n#else\nint d;\n#endif\n'                     # 6: the condition is broad, its else is not
                '#if VERSION_GAME01_REV0\nint d2;\n#elif VERSION_GAME01_REV1\nint e;\n#endif\n'  # explicit chain: not broad
                '#if VERSION_GAME01_REV0 && !VERSION_GAME01_REV1\nint f;\n#endif\n'             # false with every token false: not broad
                '#if !NOT_FIRST\nint g;\n#endif\n'                                              # double negation: not broad
                '#if BOTH\nint h;\n#else\nint i;\n#endif\n')                                     # 24: the else is broad
            return root
        with tempfile.TemporaryDirectory() as tmp:
            versions=Versions(root_with(tmp,2))
            self.assertEqual(versions.check(),[])
            self.assertEqual([w.split(':')[1] for w in versions.warnings],['3','6','24'],versions.warnings)
            self.assertEqual(versions.view(Path(tmp)/'src/a.c','GAME01-rev1'),['int b;','int c;','int e;','int h;'])
        with tempfile.TemporaryDirectory() as tmp:
            versions=Versions(root_with(tmp,3))
            errors=versions.check()
            self.assertEqual([e.split(':')[1] for e in errors],['3','6','24'],errors)
            self.assertTrue(all('covers every target not named' in e for e in errors))
            self.assertEqual(versions.warnings,[])
            # The errors are check's alone: view and diff still resolve every branch.
            self.assertEqual(versions.view(Path(tmp)/'src/a.c','GAME01-rev2'),['int b;','int c;','int i;'])
            self.assertEqual(versions.view(Path(tmp)/'src/a.c','GAME01-rev0'),['int a;','int d;','int d2;','int f;','int g;','int h;'])

    def test_matching_scope_pins_unconditional_matching_to_the_proven_targets(self):
        from tools.matching_scope import pin,scopes,other_uses,run
        # The scratch root carries this repository's own registry, whatever its ids: the first active
        # target is the proven one, and a made-up id stands for a target activated later.
        active=build_targets(registry());first=active[0];later=first+'-later'
        text=('Matching = True  # Object matches and should be linked\nNonMatching = False\nEquivalent = config.non_matching\n'
              'def MatchingFor(*versions):\n    return config.version in versions\nx = []\n'
              'objects = [\n    Object(Matching, "a.c"),\n    Object(NonMatching, "b.c"),  # Matching soon\n'
              '    Object(MatchingFor("%s"), "c.c"),\n    Object(Equivalent, "d.c"),\n    Object( Matching , "e.c", cflags=x),\n'
              '    Object(Matching, "f# Matching.c"), Object(Matching, "g.c"),\n]\n'%first)
        self.assertEqual([(u,s) for _,u,s in scopes(text)],[('a.c','all'),('b.c','none'),('c.c',[first]),('d.c','none'),('e.c','all'),('f# Matching.c','all'),('g.c','all')])
        self.assertEqual(other_uses(text),[])  # the comment, the string and the first arguments are not other uses
        new,count=pin(text,[first])
        self.assertEqual(count,4)
        self.assertEqual([s for _,_,s in scopes(new)],[[first],'none',[first],'none',[first],[first],[first]])
        self.assertEqual(pin(new,[first])[1],0)
        # What each target's configure sees: unchanged for the proven target, nothing linked for a new one.
        def flags(source,version):
            seen={};scope={'config':type('C',(),{'version':version,'non_matching':False})(),
                           'Object':lambda flag,name,**kw:seen.__setitem__(name,bool(flag))}
            exec(source,scope);return seen
        self.assertEqual(flags(text,first),flags(new,first))
        self.assertEqual(set(flags(new,later).values()),{False})
        # Other uses and unclassified calls are found through the tokens, not the text.
        self.assertEqual(other_uses(text+'flag = Matching if fast else NonMatching\n'),['15: flag = Matching if fast else NonMatching'])
        self.assertEqual(other_uses(text+'Linked = Matching\n'),['15: Linked = Matching'])
        self.assertEqual(other_uses(text+'Object(NonMatching, "h.c", flag=Matching)\n'),['15: Object(NonMatching, "h.c", flag=Matching)'])
        self.assertEqual([(u,s) for _,u,s in scopes(text+'Object(True, "z.c")\nObject(Linked, "w.c")\n')[-2:]],[('z.c','unclassified'),('w.c','unclassified')])
        with tempfile.TemporaryDirectory() as tmp:
            root=scratch(tmp);(root/'configure.py').write_text(text)
            with self.assertRaises(SystemExit):run(root,'pin',[later])  # not an active target
            with self.assertRaises(SystemExit):run(root,'pin',[])
            self.assertTrue(run(root,'pin',active)[0].startswith('pinned 4 '))
            self.assertIn('a.c: '+', '.join(sorted(active)),run(root,'show'))
            for tail in ('flag = Matching\n','Object(True, "z.c")\n','Linked = Matching\nObject(Linked, "w.c")\n'):
                (root/'configure.py').write_text(text+tail)
                with self.subTest(tail=tail),self.assertRaises(SystemExit):run(root,'pin',active)
            # Every active target must be named: a subset would drop the others' claims. The scratch
            # registry gets a second active target: a listed inactive one activated, or, when every
            # listed target is active, a made-up copy of the first.
            value=registry(root/'config/targets.json')
            inactive=[t for t in value['targets'] if t['status']!='active']
            if inactive:inactive[0]['status']='active'
            else:
                sha1='0'*40 if value['targets'][0]['sha1']!='0'*40 else '1'*40
                value['targets'].append(dict(value['targets'][0],id=later,sha1=sha1))
            (root/'config/targets.json').write_text(json.dumps(value))
            (root/'configure.py').write_text(text)
            now=build_targets(registry(root/'config/targets.json'))
            self.assertGreater(len(now),1)
            with self.assertRaises(SystemExit):run(root,'pin',now[:1])
            self.assertTrue(run(root,'pin',now)[0].startswith('pinned 4 '))

    def test_matching_scope_check_refuses_a_claim_on_every_target_once_two_are_active(self):
        from tools.matching_scope import check,run
        def root_with(tmp,statuses):
            root=Path(tmp);(root/'config').mkdir()
            targets=[{'id':'GAME01-rev%d'%n,'platform':'gamecube','label':'GAME01','region':'USA','revision':str(n),
                      'sha1':'%040x'%(n+1),'status':status} for n,status in enumerate(statuses)]
            (root/'config/targets.json').write_text(json.dumps({'schema':1,'defaultTarget':'GAME01-rev0','targets':targets}))
            return root
        text=('Matching = True\nNonMatching = False\nEquivalent = False\ndef MatchingFor(*versions):\n    return True\n'
              'objects = [\n    Object(Matching, "a.c"),\n    Object(MatchingFor("GAME01-rev0"), "b.c"),\n    Object(NonMatching, "c.c"),\n]\n')
        with tempfile.TemporaryDirectory() as tmp:
            root=root_with(tmp,['active','planned']);(root/'configure.py').write_text(text)
            self.assertEqual(check(root),[])  # one active target: plain Matching is the normal form
            self.assertEqual(run(root,'check'),['matching_scope: no problems'])
            (root/'config/targets.json').write_text((root/'config/targets.json').read_text().replace('"planned"','"active"'))
            problems=check(root)
            self.assertEqual(len(problems),1,problems)
            self.assertTrue(problems[0].startswith('configure.py:7: a.c is declared Matching for every target; GAME01-rev0, GAME01-rev1 are active'))
            with self.assertRaises(SystemExit):run(root,'check')
            (root/'configure.py').write_text(text.replace('Object(Matching, "a.c")','Object(MatchingFor("GAME01-rev0"), "a.c")'))
            self.assertEqual(check(root),[])
            self.assertEqual(run(root,'check'),['matching_scope: no problems'])
            # A call the tool cannot classify, or Matching used elsewhere, hides a claim: a failure too.
            for tail in ('Object(True, "z.c")\n','flag = Matching\n'):
                (root/'configure.py').write_text(text.replace('    Object(Matching, "a.c"),\n','')+tail)
                with self.subTest(tail=tail):self.assertEqual(len(check(root)),1,check(root))
            (root/'configure.py').unlink()
            self.assertEqual(check(root),[])  # a build without configure.py keeps its claims elsewhere

    def test_tier_floor_follows_what_the_diff_touches(self):
        self.assertEqual(declared('## Scope\n\nTier (A, B or C), task\n\nTier B, import of x.c'),'B')
        self.assertIsNone(declared('Tier (A, B or C), task'))
        self.assertEqual(declared('**Tier:** A'),'A')
        inferred='function\t0x80001000\t0x80001010\tfoo\tinferred\texact\texact\tloads'
        related=inferred.replace('inferred','related')
        lines={'config/GAME01-rev0/evidence.tsv':[inferred],'config/GAME01-rev1/evidence.tsv':[related],
               'configure.py':['    Object(Matching, "a.c"),'],'docs/a.md':[]}
        diff=lambda path:lines.get(path,[])
        self.assertEqual(floor(['docs/a.md','tools/x.py'],diff)[0],'C')
        self.assertEqual(floor(['src/a.c'],diff)[0],'B')
        self.assertEqual(floor(['configure.py'],diff)[0],'B')
        self.assertEqual(floor(['config/GAME01-rev1/evidence.tsv'],diff)[0],'C')
        self.assertEqual(floor(['config/GAME01-rev0/evidence.tsv','src/a.c'],diff)[0],'A')
        self.assertEqual(floor(['config/GAME01-rev0/symbols.txt'],diff)[0],'A')
        lines['configure.py']=['cflags_game = [*cflags_base, "-O4,s"]']
        self.assertEqual(floor(['configure.py'],diff)[0],'A')

    def test_evidence_rows_are_checked(self):
        header='\t'.join(COLUMNS)+'\n'
        good=header+'function\t0x80000000\t0x80000010\tfn_80000000\ttarget\texact\tprovisional\tdtk extent\n'
        self.assertEqual(check_text(good),[])
        for row,message in (('name\t0x80000000\t-\tx\tinferred\texact\t-\tbehavior','edges belong to'),
                            ('function\t80000000\t0x80000010\tx\ttarget\t-\t-\te','eight upper-case hex'),
                            ('function\t0x80000010\t0x80000000\tx\ttarget\t-\t-\te','end is not after start'),
                            ('story\t-\t-\tx\ttarget\t-\t-\te','unknown kind'),
                            ('name\t-\t-\tx\tguess\t-\t-\te','unknown origin'),
                            ('name\t-\t-\tx\tinferred\t-\t-','7 columns')):
            with self.subTest(row=row):self.assertTrue(any(message in p for p in check_text(header+row+'\n')),check_text(header+row+'\n'))
        self.assertTrue(any('header row' in p for p in check_text('kind\tstart\n')))

    def test_credits_line_and_overrides_are_checked(self):
        self.assertEqual(credits_line('## Scope\n\nCredits: @alice, bob\n'),['alice','bob'])
        self.assertIsNone(credits_line('<!-- a line `Credits: @login` names them -->'))
        for bad in ('Credits: ','Credits: @a, @a','Credits: not a login!'):
            with self.subTest(bad=bad),self.assertRaises(CreditError):credits_line(bad)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'credits.tsv'
            path.write_text('# address\tlogins\treason\n0x80000010\talice,bob\timported from #12\n')
            self.assertEqual(credits_tsv(path),{'0x80000010':['alice','bob']})
            for bad in ('0x8000001a\talice\tr\n','0x80000010\talice\t \n','0x80000010\talice\n'):
                path.write_text(bad)
                with self.subTest(bad=bad),self.assertRaises(CreditError):credits_tsv(path)

    def test_measuring_tools_reads_the_image_from_the_environment(self):
        configure='config.dtk_tag = "v1.8.3"\nconfig.objdiff_tag = "v3.6.1"\n'
        # pins=[]: these cases read configure.py whatever this repository's PINS names.
        self.assertEqual(measuring_tools(DIGEST,configure,pins=[])[0],('build-environment',DIGEST))
        with self.assertRaises(SystemExit):measuring_tools('ghcr.io/owner/game-build:main',configure,pins=[])
        with self.assertRaises(SystemExit):measuring_tools(DIGEST,'',pins=[])
        pins=[{'dtk':{'version':'v1.8.4','linux-x86_64':{}}},{'objdiff':{'version':'v3.8.2'}}]
        self.assertEqual(measuring_tools(DIGEST,pins=pins)[1:],[('dtk','v1.8.4'),('objdiff','v3.8.2')])
        with self.assertRaises(SystemExit):measuring_tools(DIGEST,pins=[{'dtk':{}}])

    def test_verify_requires_the_pinned_version_from_the_image(self):
        # The reported version's first word (a patched dtk adds words) without its `v` must appear
        # in what the tool prints; a tool that prints another version, or cannot run, stops the step.
        found=[('build-environment',DIGEST),('dtk','v1.8.3 + a local patch sha256:0912')]
        say=lambda text,code=0:[sys.executable,'-c','print(%r);raise SystemExit(%d)'%(text,code)]
        self.assertEqual(verify(found,{'dtk':say('dtk 1.8.3')}),found)
        self.assertEqual(verify(found,{'dtk':say('dtk v1.8.3 (release)')}),found)
        for output in ('dtk 1.8.4','dtk 1.8.30','dtk 1.8','dtk 11.8.3',''):
            with self.subTest(output=output),self.assertRaises(SystemExit):verify(found,{'dtk':say(output)})
        with self.assertRaises(SystemExit):verify([('dtk','v1.8')],{'dtk':say('dtk 1.8.3')})  # a short pin is not a match
        with self.assertRaises(SystemExit):verify(found,{'dtk':say('dtk 1.8.3',code=1)})  # the command must succeed
        with self.assertRaises(SystemExit):verify(found,{'dtk':['/no/such/tool','--version']})
        with self.assertRaises(SystemExit):verify(found,{'objdiff':say('objdiff 3.6.1')})


if __name__=='__main__':unittest.main()
