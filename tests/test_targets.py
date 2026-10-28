"""The kit tools against this repository's registry and against scratch trees. Run from the
repository root: python3 -m unittest discover -s tests -p 'test_*.py'"""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from tools.targets import registry,select,build_targets,define,check as check_targets
from tools.ci_targets import affected,target_patterns
from tools.evidence import check_text,COLUMNS
from tools.measuring_tools import tools as measuring_tools
from tools.new_target import scaffold
from tools.versions import Versions
from tools.tier import declared,floor

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

    def test_new_target_refuses_unknown_ids_and_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=scratch(tmp);first=registry()['targets'][0]['id']
            self.assertEqual((root/'config'/first/'evidence.tsv').read_text(),'\t'.join(COLUMNS)+'\n')
            self.assertIn('hash: '+select(first)['sha1'],(root/'config'/first/'config.yml').read_text())
            with self.assertRaises(ValueError):scaffold('no-such-target',root)
            with self.assertRaises(SystemExit):scaffold(first,root)

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

    def test_measuring_tools_reads_the_image_from_the_environment(self):
        configure='config.dtk_tag = "v1.8.3"\nconfig.objdiff_tag = "v3.6.1"\n'
        self.assertEqual(measuring_tools(DIGEST,configure)[0],('build-environment',DIGEST))
        with self.assertRaises(SystemExit):measuring_tools('ghcr.io/owner/game-build:main',configure)
        with self.assertRaises(SystemExit):measuring_tools(DIGEST,'')


if __name__=='__main__':unittest.main()
