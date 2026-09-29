#!/usr/bin/env python3
"""
Local progress dashboard for the MVP Baseball 2005 decompilation.

    python tools/dashboard/server.py [--port 8420] [--host 0.0.0.0] [--agents DIR]
    python tools/dashboard/server.py --export site/ [--report report.json] [--history history.json] [--sha SHA]

--export writes the static copy CI publishes on GitHub Pages (index.html reading progress.json,
no "in flight" panel; report.json numbers only) and exits. Without a report it still writes the
page, which then says no build of main has produced one yet.

Serves one page and /api/progress. Reads build/GV4E69/report.json (written by every `ninja`
run), config/GV4E69/symbols.txt, build/dashboard_history.json (a history file in the format
pages.py writes, if present) and, for the "in flight" panel, each agent worktree's report under
--agents (default: the folder next to the repo named <repo>-agents). Standard library only.
Never launches another program: on this PC any console program started from a windowless process
opens a Windows Terminal window.
"""
import argparse, json, os, re, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
VERSION = 'GV4E69'
REPORT = os.path.join(ROOT, 'build', VERSION, 'report.json')
SYMBOLS = os.path.join(ROOT, 'config', VERSION, 'symbols.txt')
HISTORY = os.path.join(ROOT, 'build', 'dashboard_history.json')
AGENTS = os.path.join(os.path.dirname(ROOT), os.path.basename(ROOT) + '-agents')

_cache = {}


def cached(path, parse):
    """parse(path), redone only when the file's mtime or size changes."""
    try:
        st = os.stat(path)
    except OSError:
        return None
    key = (st.st_mtime, st.st_size)
    hit = _cache.get((path, parse))
    if hit and hit[0] == key:
        return hit[1]
    try:
        val = parse(path)
    except Exception:
        return None
    _cache[(path, parse)] = (key, val)
    return val


def git_branch(root=ROOT):
    """Current branch, read from .git/HEAD (or a worktree's gitdir). No subprocess: on this PC a
    git call from a windowless process opens a Windows Terminal window (see docs/decomp-notes.md)."""
    try:
        git = os.path.join(root, '.git')
        if os.path.isfile(git):
            git = open(git).read().split('gitdir:', 1)[1].strip()
        head = open(os.path.join(git, 'HEAD')).read().strip()
        return head.split('refs/heads/', 1)[-1] if head.startswith('ref:') else head[:7]
    except Exception:
        return '?'


def num(v):
    """objdiff writes byte counts as strings and percentages as numbers."""
    if isinstance(v, (int, float)):
        return v
    try:
        return int(v)
    except (TypeError, ValueError):
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0


# objdiff leaves a measure out of report.json when it is zero (e.g. matched_code before anything
# matches); the page reads these, so a missing one is 0, not undefined (NaN on the page).
MEASURES = ('total_code', 'matched_code', 'matched_code_percent', 'complete_code', 'complete_code_percent',
            'total_data', 'matched_data', 'matched_data_percent', 'complete_data', 'complete_data_percent',
            'total_functions', 'matched_functions', 'matched_functions_percent', 'fuzzy_match_percent',
            'total_units', 'complete_units')


def measures(m):
    out = dict.fromkeys(MEASURES, 0)
    out.update((k, num(v)) for k, v in m.items())
    return out


def parse_report(path):
    """The parts of an objdiff report.json the page needs."""
    r = json.load(open(path))
    units, fns = [], {}
    unsplit = {'code': 0, 'data': 0, 'units': 0, 'by_cat': {}}
    for u in r.get('units', []):
        md = u.get('metadata', {})
        um = measures(u.get('measures', {}))
        linked = bool(md.get('complete')) or um.get('complete_code_percent', 0) >= 100
        for f in u.get('functions', []):
            addr = f.get('metadata', {}).get('virtual_address')
            if addr is not None:
                fns[addr] = (num(f.get('size')), f.get('fuzzy_match_percent', 0) >= 100, linked, u['name'])
        if md.get('auto_generated'):
            # dtk's gap units: code no source file covers yet. The ones configure.py puts in a
            # category (tools/match/autocat.py) are counted in it as well: by_cat keeps them apart
            # so the page shows them inside their category, not as extra code beside it.
            unsplit['code'] += um.get('total_code', 0)
            unsplit['data'] += um.get('total_data', 0)
            unsplit['units'] += 1
            if um.get('total_code', 0):
                cat = (md.get('progress_categories') or [''])[0]
                g = unsplit['by_cat'].setdefault(cat, {'code': 0, 'units': 0})
                g['code'] += um.get('total_code', 0)
                g['units'] += 1
            continue
        name = u['name'][5:] if u['name'].startswith('main/') else u['name']
        cats = md.get('progress_categories', [])
        units.append({
            'name': name,
            'cat': cats[0] if cats else '',
            'code': um.get('total_code', 0),
            'matched': um.get('matched_code', 0),
            'data': um.get('total_data', 0),
            'fns': um.get('total_functions', 0),
            'exact': um.get('matched_functions', 0),
            'fuzzy': round(um.get('fuzzy_match_percent', 0), 2),
            'linked': linked,
            'sweep': name.startswith('unsorted/sweep_'),
        })
    m = measures(r.get('measures', {}))
    return {
        'mtime': os.path.getmtime(path),
        'measures': m,
        'categories': [{'id': c.get('id'), 'name': c.get('name'), 'measures': measures(c.get('measures', {}))}
                       for c in r.get('categories', [])],
        'unsplit': unsplit,
        'units': units,
        '_fns': fns,
    }


def parse_history(path):
    return json.load(open(path))


def parse_symbols(path):
    total = named = 0
    for line in open(path, errors='replace'):
        m = re.match(r'^(\S+) = \.(?:text|init):0x[0-9A-Fa-f]+; // type:function', line)
        if m:
            total += 1
            if not m.group(1).startswith('fn_'):
                named += 1
    return {'functions': total, 'named': named}


def in_flight(main, agents_dir):
    """Per agent worktree: the code its last build matches (or links) that main's build does not.
    Compared function by function (by address), so folded sweep files and main moving on since
    the branch point do not count as progress."""
    out = []
    try:
        names = sorted(os.listdir(agents_dir))
    except OSError:
        return out
    base = main['_fns']
    for name in names:
        root = os.path.join(agents_dir, name)
        if os.path.normcase(os.path.abspath(root)) == os.path.normcase(ROOT):
            continue
        rep = cached(os.path.join(root, 'build', VERSION, 'report.json'), parse_report)
        if not rep:
            continue
        matched = linked = new_fns = 0
        per_unit = {}
        for addr, (size, exact, is_linked, unit) in rep['_fns'].items():
            b = base.get(addr, (0, False, False, ''))
            if exact and not b[1]:
                matched += size
                new_fns += 1
                per_unit[unit] = per_unit.get(unit, 0) + size
            if is_linked and not b[2]:
                linked += size
        units = sorted(per_unit.items(), key=lambda kv: -kv[1])[:4]
        out.append({
            'name': name,
            'branch': git_branch(root),
            'mtime': rep['mtime'],
            'matched_ahead': matched,
            'linked_ahead': linked,
            'functions_ahead': new_fns,
            'units': [{'name': u[5:] if u.startswith('main/') else u, 'bytes': b} for u, b in units],
        })
    out.sort(key=lambda a: -a['matched_ahead'])
    return out


def progress(agents_dir):
    rep = cached(REPORT, parse_report)
    return {
        'now': time.time(),
        'branch': git_branch(),
        'report': {k: v for k, v in rep.items() if not k.startswith('_')} if rep else None,
        'symbols': cached(SYMBOLS, parse_symbols) or {'functions': 0, 'named': 0},
        'history': cached(HISTORY, parse_history) or [],
        'agents': in_flight(rep, agents_dir) if rep else [],
    }


PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>mvp2005 progress</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<style>
:root{
 color-scheme:light;
 --bg:#f6f6f4;--surface:#fcfcfb;--line:#e4e3de;--line-strong:#cfcdc6;
 --text:#0b0b0b;--text-2:#52514e;--text-3:#7a7974;
 --linked:#1c5cab;--matched:#86b6ef;--track:#ebeae6;
 --accent:#1c5cab;--accent-soft:#e3eefb;
 --good:#0a7d0a;--good-soft:#e2f3e2;--ready:#1c5cab;--ready-soft:#e3eefb;
 --shadow:0 1px 2px rgba(0,0,0,.04);
}
@media (prefers-color-scheme:dark){:root{
 color-scheme:dark;
 --bg:#121211;--surface:#1a1a19;--line:#2c2c2a;--line-strong:#3c3c39;
 --text:#f4f4f2;--text-2:#c3c2b7;--text-3:#8e8d86;
 --linked:#6da7ec;--matched:#184f95;--track:#2a2a28;
 --accent:#86b6ef;--accent-soft:#1b2a3d;
 --good:#4cc44c;--good-soft:#16301a;--ready:#86b6ef;--ready-soft:#1b2a3d;
 --shadow:none;
}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;font-variant-numeric:tabular-nums}
.wrap{max-width:1080px;margin:0 auto;padding:28px 16px 40px}
header{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:4px 16px;margin-bottom:22px}
h1{font-size:19px;line-height:1.3;margin:0;font-weight:650;letter-spacing:-.01em}
h1 span{color:var(--text-3);font-weight:500}
.meta{color:var(--text-3);font-size:13px}
.meta b{color:var(--text-2);font-weight:500}
h2{font-size:13px;font-weight:600;margin:0 0 12px;color:var(--text-2);letter-spacing:.02em}
.card{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px 20px;box-shadow:var(--shadow);margin-top:14px}
.hero{display:grid;grid-template-columns:3fr 2fr;gap:14px}
.hero .card{margin-top:0}
.figs{display:flex;flex-wrap:wrap;gap:6px 28px;align-items:baseline}
.fig .n{font-size:34px;font-weight:650;letter-spacing:-.02em;line-height:1.1}
.fig .l{font-size:13px;color:var(--text-2);display:flex;align-items:center;gap:6px}
.fig.sec .n{font-size:24px;color:var(--text-2)}
.sw{width:10px;height:10px;border-radius:3px;display:inline-block;flex:none}
.sw.linked{background:var(--linked)}.sw.matched{background:var(--matched)}.sw.rest{background:var(--track);outline:1px solid var(--line-strong);outline-offset:-1px}
.bar{display:flex;gap:2px;height:14px;margin:14px 0 10px;border-radius:4px;overflow:hidden;background:var(--track)}
.bar i{display:block;height:100%}
.bar i.linked{background:var(--linked)}.bar i.matched{background:var(--matched)}
.bar.sm{height:8px;margin:6px 0 0;border-radius:3px}
.legend{display:grid;grid-template-columns:auto 1fr auto auto;gap:3px 10px;font-size:13px;color:var(--text-2);align-items:center}
.legend .v{text-align:right;color:var(--text)}
.legend .p{text-align:right;min-width:58px}
.note{font-size:12.5px;color:var(--text-3);margin:10px 0 0;line-height:1.45}
.cats{margin-top:16px;border-top:1px solid var(--line);padding-top:12px;display:grid;gap:12px}
.cat .row{display:flex;justify-content:space-between;gap:10px;font-size:13px}
.cat .row span:last-child{color:var(--text-2);text-align:right}
.cat.sub{margin:-6px 0 0 18px}.cat.sub .row{font-size:12.5px;color:var(--text-2)}
.cat small{color:var(--text-3);font-size:12px}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:14px}
.stats .card{margin-top:0;padding:14px 16px}
.stat .k{font-size:12.5px;color:var(--text-2)}
.stat .v{font-size:22px;font-weight:650;letter-spacing:-.01em}
.stat .s{font-size:12.5px;color:var(--text-3)}
button.link{all:unset;cursor:pointer;color:var(--accent);text-decoration:underline;text-underline-offset:2px}
#chartbox{position:relative}
#chart{display:block;width:100%;height:220px;touch-action:pan-y}
#chart text{fill:var(--text-3);font-size:11px}
#chart .grid{stroke:var(--line);stroke-width:1}
#chart .a-m{fill:var(--matched)}#chart .a-l{fill:var(--linked)}
#chart .l-m{stroke:var(--linked);stroke-opacity:.55;fill:none;stroke-width:1.5}
#chart .cross{stroke:var(--text-3);stroke-width:1}
#chart .dot{stroke:var(--surface);stroke-width:2}
.tip{position:absolute;pointer-events:none;background:var(--surface);border:1px solid var(--line-strong);border-radius:8px;padding:8px 10px;font-size:12.5px;box-shadow:0 4px 14px rgba(0,0,0,.12);max-width:280px;display:none;z-index:2}
.tip .h{color:var(--text-3);font-size:12px}
.tip .t{margin:2px 0 6px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tip .r{display:flex;align-items:center;gap:6px}.tip .r b{margin-left:auto;font-weight:600;padding-left:12px}
.chartlegend{display:flex;flex-wrap:wrap;gap:4px 18px;font-size:13px;color:var(--text-2);margin-bottom:8px}
.chartlegend span{display:flex;align-items:center;gap:6px}
.toolbar{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;margin-bottom:10px}
.seg{display:flex;flex-wrap:wrap;gap:4px}
.seg button{font:inherit;font-size:13px;border:1px solid var(--line-strong);background:transparent;color:var(--text-2);padding:4px 10px;border-radius:999px;cursor:pointer}
.seg button[aria-pressed=true]{background:var(--text);color:var(--surface);border-color:var(--text)}
.seg button .c{opacity:.7;margin-left:4px}
#sortsel{display:none;font:inherit;font-size:13px;padding:4px 6px;border:1px solid var(--line-strong);border-radius:8px;background:var(--surface);color:var(--text)}
input[type=search]{font:inherit;font-size:13px;padding:5px 10px;border:1px solid var(--line-strong);border-radius:8px;background:var(--surface);color:var(--text);min-width:0;flex:1 1 160px;max-width:260px}
.callout{display:flex;gap:10px;align-items:center;background:var(--ready-soft);border-radius:8px;padding:9px 12px;font-size:13.5px;margin-bottom:12px}
.tbl{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);vertical-align:middle}
th{font-weight:500;font-size:12.5px;color:var(--text-3);white-space:nowrap}
th[data-k]{cursor:pointer;user-select:none}
th[data-k]:hover{color:var(--text)}
th .arr{display:inline-block;width:10px}
td.n,th.n{text-align:right}
td.file{font-family:ui-monospace,"Cascadia Mono",Consolas,monospace;font-size:12.5px;word-break:break-all}
td.file small{font-family:system-ui,sans-serif;color:var(--text-3);font-size:11px;margin-left:6px;border:1px solid var(--line-strong);border-radius:4px;padding:0 4px;white-space:nowrap}
td.n{white-space:nowrap}
.pc{display:flex;align-items:center;gap:8px;justify-content:flex-end}
.pc .bar{width:70px;margin:0;height:6px;flex:none}
.pc span{min-width:48px;text-align:right}
.badge{display:inline-flex;align-items:center;gap:4px;font-size:12px;padding:1px 8px;border-radius:999px;white-space:nowrap}
.badge.linked{background:var(--good-soft);color:var(--good)}
.badge.ready{background:var(--ready-soft);color:var(--ready);font-weight:600}
.badge.part{color:var(--text-2)}
.badge.none{color:var(--text-3)}
tr.group td{background:var(--bg)}
tr.group button{all:unset;cursor:pointer;display:flex;gap:6px;align-items:center;font-weight:550}
tr.group .file small{border:0;padding:0}
.more{margin-top:8px;font-size:13px;color:var(--text-3)}
.agents{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px}
.agent{border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.agent .top{display:flex;justify-content:space-between;gap:8px;align-items:baseline}
.agent .nm{font-weight:600}
.agent .age{font-size:12px;color:var(--text-3)}
.agent .big{font-size:20px;font-weight:650;margin-top:2px}
.agent .sub{font-size:12.5px;color:var(--text-2)}
.agent ul{margin:6px 0 0;padding:0;list-style:none;font-size:12px;color:var(--text-3)}
.agent li{display:flex;justify-content:space-between;gap:8px}
.agent li span:first-child{font-family:ui-monospace,Consolas,monospace;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.agent.idle{opacity:.6}
.commits td{font-size:13px}
.commits code{font-family:ui-monospace,Consolas,monospace;font-size:12px;color:var(--text-3)}
.commits .d{white-space:nowrap;text-align:right;color:var(--text-2)}
.commits .when{white-space:nowrap;text-align:right;color:var(--text-3)}
.up{color:var(--good)}
footer{color:var(--text-3);font-size:12px;margin-top:22px;line-height:1.6}
footer code{font-family:ui-monospace,Consolas,monospace}
@media (max-width:760px){
 .hero{grid-template-columns:1fr}
 .stats{grid-template-columns:repeat(2,1fr)}
 .fig .n{font-size:28px}
 .card{padding:14px}
 .hide-sm{display:none}
 .pc .bar{display:none}
 .cat .row{flex-direction:column;gap:0}
 .cat .row span:last-child{text-align:left;font-size:12.5px}
 #units thead{display:none}
 #units tr{display:grid;grid-template-columns:1fr auto auto;align-items:center;gap:2px 12px;padding:8px 2px;border-bottom:1px solid var(--line)}
 #units td{border:0;padding:0}
 #units td.file{grid-column:1/-1;font-size:12.5px}
 #units tr.group{background:var(--bg);padding:8px 6px;border-radius:6px}
 #units tr.group td{background:none}
 #units td[colspan]{grid-column:1/-1}
 #sortsel{display:block}
 .commits .subj{max-width:0;width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
}
</style></head><body><div class="wrap">
<header><h1>MVP Baseball 2005 <span>&middot; decompilation progress</span></h1><div class="meta" id="meta">loading&hellip;</div></header>
<div id="main"></div>
<footer>Reads <code>build/GV4E69/report.json</code> (written by every <code>ninja</code> run), <code>symbols.txt</code> and <code>build/dashboard_history.json</code> (if present). Refreshes every 20&nbsp;s. Read-only.</footer>
</div>
<script>
const API='/api/progress',REFRESH=20000,AGENTS_PANEL=true,NO_REPORT='No report.json yet: run ninja once.';
const $=s=>document.querySelector(s);
const fmt=n=>Math.round(n).toLocaleString('en-US');
const pct=(a,b)=>b?100*a/b:0;
const pf=(p,d=2)=>p.toFixed(d)+'%';
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const ago=t=>{const s=Math.max(0,Date.now()/1000-t);if(s<90)return Math.round(s)+' s ago';if(s<5400)return Math.round(s/60)+' min ago';if(s<172800)return (s/3600).toFixed(1)+' h ago';return (s/86400).toFixed(1)+' d ago'};
const bar=(l,m,t,cls='')=>{const L=pct(l,t),M=Math.max(0,pct(m,t)-L);return `<div class="bar ${cls}" role="img" aria-label="${pf(L)} linked, ${pf(L+M)} matched">${L>0?`<i class="linked" style="width:${Math.max(L,.4)}%"></i>`:''}${M>0?`<i class="matched" style="width:${Math.max(M,.4)}%"></i>`:''}</div>`};
const state={filter:'all',q:'',sort:'status',dir:1,sweepOpen:false,limit:300,data:null};
const STATUS={ready:0,part:1,none:2,linked:3};
const statusOf=u=>u.linked?'linked':(u.code>0&&u.matched>=u.code)?'ready':u.matched>0?'part':'none';
const BADGE={linked:'<span class="badge linked">&#10003; Linked</span>',ready:'<span class="badge ready">&#8594; Ready to link</span>',part:'<span class="badge part">In progress</span>',none:'<span class="badge none">Not started</span>'};

function codeCard(m,cats,uns){
 const T=m.total_code,L=m.complete_code,M=m.matched_code;
 // Gap units (code not yet in a source file) that belong to a category are already inside its
 // total: they are shown as an "of which" line under it, never as extra code beside it.
 const gaps=(uns.by_cat||{}),gapRow=(label,g,top)=>`<div class="cat${top?'':' sub'}"><div class="row"><span>${label}</span><span>${g.units} gaps &middot; ${fmt(g.code)} B</span></div>${bar(0,0,g.code,'sm')}</div>`;
 const catRows=cats.map(c=>{const x=c.measures,g=gaps[c.id];return `<div class="cat"><div class="row"><span>${esc(c.name)}${g?' <small>(all its code, gaps included)</small>':''}</span><span>${pf(pct(x.matched_code,x.total_code),1)} matched &middot; ${pf(pct(x.complete_code,x.total_code),1)} linked &middot; ${fmt(x.total_code)} B</span></div>${bar(x.complete_code,x.matched_code,x.total_code,'sm')}</div>`+
  (g?gapRow(`of which not yet in a source file`,g):'')}).join('')+
  (gaps['']?gapRow('Not yet in a source file, in no category (gaps among the SDK libraries)',gaps[''],1):'')+
  (!uns.by_cat&&uns.code?gapRow('Not yet in a source file',{units:uns.units,code:uns.code},1):'');
 return `<section class="card"><h2>Code</h2>
 <div class="figs"><div class="fig"><div class="n">${pf(pct(M,T))}</div><div class="l"><i class="sw matched"></i>matched</div></div>
 <div class="fig"><div class="n">${pf(pct(L,T))}</div><div class="l"><i class="sw linked"></i>fully linked</div></div></div>
 ${bar(L,M,T)}
 <div class="legend">
  <i class="sw linked"></i><span>Linked</span><span class="v">${fmt(L)} B</span><span class="p">${pf(pct(L,T))}</span>
  <i class="sw matched"></i><span>Matched, not yet linked</span><span class="v">${fmt(M-L)} B</span><span class="p">${pf(pct(M-L,T))}</span>
  <i class="sw rest"></i><span>Not matched</span><span class="v">${fmt(T-M)} B</span><span class="p">${pf(pct(T-M,T))}</span>
 </div>
 <p class="note">Total ${fmt(T)} B of code. Matched counts every function that compiles byte-for-byte; linked counts only files marked <code>Matching</code> in configure.py, whose object replaces the original in the build.</p>
 <div class="cats">${catRows}</div></section>`}

function dataCard(m){
 const T=m.total_data,L=m.complete_data,M=m.matched_data,extra=Math.max(0,M-L);
 return `<section class="card"><h2>Data</h2>
 <div class="figs"><div class="fig"><div class="n">${pf(pct(L,T))}</div><div class="l"><i class="sw linked"></i>fully linked</div></div>
 <div class="fig sec"><div class="n">${pf(pct(M,T))}</div><div class="l">matched</div></div></div>
 ${bar(L,Math.max(L,M),T)}
 <div class="legend">
  <i class="sw linked"></i><span>Linked</span><span class="v">${fmt(L)} B</span><span class="p">${pf(pct(L,T))}</span>
  ${extra?`<i class="sw matched"></i><span>Matched, not yet linked</span><span class="v">${fmt(extra)} B</span><span class="p">${pf(pct(extra,T))}</span>`:''}
  <i class="sw rest"></i><span>Not linked</span><span class="v">${fmt(T-Math.max(L,M))} B</span><span class="p">${pf(pct(T-Math.max(L,M),T))}</span>
 </div>
 <p class="note">Total ${fmt(T)} B of data (.bss included). Matched data (${fmt(M)} B) counts only data symbols objdiff compared equal; linked data counts every data byte of linked files, so here it is the larger number.</p></section>`}

function stat(k,v,s){return `<div class="card stat"><div class="k">${k}</div><div class="v">${v}</div><div class="s">${s}</div></div>`}

function render(d){
 const r=d.report,m=r.measures,s=d.symbols,units=r.units;
 const counts={all:units.length,game:0,sdk:0,linked:0,not:0,ready:0};
 let readyBytes=0;
 for(const u of units){u.st=statusOf(u);u.pct=pct(u.matched,u.code);if(u.cat==='game')counts.game++;if(u.cat==='sdk')counts.sdk++;if(u.linked)counts.linked++;else counts.not++;if(u.st==='ready'){counts.ready++;readyBytes+=u.code}}
 state.counts=counts;
 $('#main').innerHTML=
  `<div class="hero">${codeCard(m,r.categories,r.unsplit)}${dataCard(m)}</div>`+
  `<div class="stats">`+
   stat('Functions exact',fmt(m.matched_functions),`of ${fmt(m.total_functions)} &middot; ${pf(pct(m.matched_functions,m.total_functions),1)}`)+
   stat('Functions named',fmt(s.named),`of ${fmt(s.functions)} &middot; ${pf(pct(s.named,s.functions),1)}`)+
   stat('Source files linked',fmt(counts.linked),`of ${fmt(units.length)} &middot; ${fmt(counts.ready)} ready to link`)+
   stat('Fuzzy code match',pf(m.fuzzy_match_percent||0,1),'partial functions count in part')+
  `</div>`+
  `<section class="card"><h2>History</h2><div class="chartlegend"><span><i class="sw matched"></i>Matched code</span><span><i class="sw linked"></i>Linked code</span><span style="color:var(--text-3)">% of all code, per commit</span></div><div id="chartbox"><svg id="chart" aria-label="Matched and linked code over time"></svg><div class="tip" id="tip"></div></div><p class="note" id="chartnote"></p></section>`+
  (AGENTS_PANEL&&d.agents&&d.agents.length?`<section class="card"><h2>In flight &middot; agent worktrees ahead of main</h2><div class="agents" id="agents"></div><p class="note">From each worktree's last <code>ninja</code> report: code in functions that match there but not in main's build, compared function by function. Linked counts functions in files that worktree links and main does not.</p></section>`:'')+
  `<section class="card"><h2>Source files</h2>
   ${counts.ready?`<div class="callout"><span class="badge ready">&#8594; ${counts.ready}</span><span>${counts.ready===1?'file is':'files are'} 100% matched but not linked yet (${fmt(readyBytes)} B of code). <button class="link" data-f="ready">Show them</button></span></div>`:''}
   <div class="toolbar"><div class="seg" id="seg"></div><input type="search" id="q" placeholder="Filter by name" value="${esc(state.q)}"><select id="sortsel" aria-label="Sort by">${[['status','Sort: status'],['pct','Sort: matched %'],['code','Sort: size'],['fns','Sort: functions'],['name','Sort: name']].map(([k,l])=>`<option value="${k}"${state.sort===k?' selected':''}>${l}</option>`).join('')}</select></div>
   <div class="tbl"><table id="units"><thead><tr>
    <th data-k="name">File<span class="arr"></span></th><th data-k="status">Status<span class="arr"></span></th>
    <th data-k="fns" class="n">Functions<span class="arr"></span></th><th data-k="code" class="n hide-sm">Code<span class="arr"></span></th>
    <th data-k="pct" class="n">Matched<span class="arr"></span></th></tr></thead><tbody></tbody></table></div><div class="more" id="more"></div></section>`+
  `<section class="card commits"><h2>Recent commits</h2><table><tbody id="commits"></tbody></table></section>`;
 renderSeg();renderUnits();renderAgents(d);renderCommits(d);drawChart();
 $('#sortsel').addEventListener('change',e=>{state.sort=e.target.value;state.dir=(state.sort==='name'||state.sort==='status')?1:-1;renderUnits()});
 $('#q').addEventListener('input',e=>{state.q=e.target.value;state.limit=300;renderUnits()});
 document.querySelectorAll('#units th[data-k]').forEach(th=>th.addEventListener('click',()=>{const k=th.dataset.k;if(state.sort===k)state.dir=-state.dir;else{state.sort=k;state.dir=(k==='name'||k==='status')?1:-1}renderUnits()}));
 document.querySelectorAll('[data-f]').forEach(b=>b.addEventListener('click',()=>{state.filter=b.dataset.f;renderSeg();renderUnits();$('#seg').scrollIntoView({block:'nearest'})}));
}

function renderSeg(){
 const c=state.counts,F=[['all','All'],['game','Game code'],['sdk','SDK'],['linked','Linked'],['not','Not linked'],['ready','Ready to link']];
 $('#seg').innerHTML=F.map(([k,l])=>`<button data-seg="${k}" aria-pressed="${state.filter===k}">${l}<span class="c">${c[k]}</span></button>`).join('');
 document.querySelectorAll('#seg button').forEach(b=>b.addEventListener('click',()=>{state.filter=b.dataset.seg;state.limit=300;renderSeg();renderUnits()}));
}

function unitRow(u){
 return `<tr><td class="file">${esc(u.name)}${u.cat==='sdk'?'<small>SDK</small>':''}</td><td>${BADGE[u.st]}</td>
 <td class="n">${u.exact} / ${u.fns}</td><td class="n hide-sm">${fmt(u.code)}</td>
 <td class="n"><div class="pc">${bar(u.linked?u.code:0,u.matched,u.code||1,'sm')}<span>${u.code?pf(u.pct,1):'&ndash;'}</span></div></td></tr>`}

function renderUnits(){
 const q=state.q.trim().toLowerCase(),f=state.filter;
 let us=state.data.report.units.filter(u=>(f==='all'||(f==='game'&&u.cat==='game')||(f==='sdk'&&u.cat==='sdk')||(f==='linked'&&u.linked)||(f==='not'&&!u.linked)||(f==='ready'&&u.st==='ready'))&&(!q||u.name.toLowerCase().includes(q)));
 const key={name:u=>u.name.toLowerCase(),status:u=>STATUS[u.st]*1e3-u.pct,fns:u=>u.fns,code:u=>u.code,pct:u=>u.pct}[state.sort];
 us.sort((a,b)=>{const x=key(a),y=key(b);return (x<y?-1:x>y?1:0)*state.dir||a.name.localeCompare(b.name)});
 const sweeps=us.filter(u=>u.sweep),rest=us.filter(u=>!u.sweep);
 let html='';
 if(sweeps.length){
  const code=sweeps.reduce((a,u)=>a+u.code,0),matched=sweeps.reduce((a,u)=>a+u.matched,0),lk=sweeps.filter(u=>u.linked),lcode=lk.reduce((a,u)=>a+u.code,0),fns=sweeps.reduce((a,u)=>a+u.fns,0),ex=sweeps.reduce((a,u)=>a+u.exact,0);
  html+=`<tr class="group"><td class="file"><button id="sw">${state.sweepOpen?'&#9662;':'&#9656;'} unsorted/sweep_*<small>${fmt(sweeps.length)} files</small></button></td><td><span class="badge ${lk.length===sweeps.length?'linked':'part'}">${lk.length===sweeps.length?'&#10003; All linked':fmt(lk.length)+' linked'}</span></td><td class="n">${fmt(ex)} / ${fmt(fns)}</td><td class="n hide-sm">${fmt(code)}</td><td class="n"><div class="pc">${bar(lcode,matched,code||1,'sm')}<span>${pf(pct(matched,code),1)}</span></div></td></tr>`;
  if(state.sweepOpen)html+=sweeps.map(unitRow).join('');
 }
 html+=rest.slice(0,state.limit).map(unitRow).join('');
 $('#units tbody').innerHTML=html||'<tr><td colspan="5" style="color:var(--text-3)">No files match.</td></tr>';
 $('#more').innerHTML=rest.length>state.limit?`Showing ${state.limit} of ${fmt(rest.length)} files. <button class="link" id="showall">Show all</button>`:'';
 const sa=$('#showall');if(sa)sa.addEventListener('click',()=>{state.limit=1e9;renderUnits()});
 const sw=$('#sw');if(sw)sw.addEventListener('click',()=>{state.sweepOpen=!state.sweepOpen;renderUnits()});
 document.querySelectorAll('#units th[data-k]').forEach(th=>{th.querySelector('.arr').textContent=th.dataset.k===state.sort?(state.dir>0?'↑':'↓'):'';th.setAttribute('aria-sort',th.dataset.k===state.sort?(state.dir>0?'ascending':'descending'):'none')});
}

function renderAgents(d){
 const el=$('#agents');if(!el)return;
 el.innerHTML=d.agents.map(a=>`<div class="agent${a.matched_ahead?'':' idle'}"><div class="top"><span class="nm">${esc(a.name)}</span><span class="age">built ${ago(a.mtime)}</span></div>
  <div class="big">${a.matched_ahead?'+'+fmt(a.matched_ahead)+' B':'&ndash;'}</div>
  <div class="sub">${a.matched_ahead?`matched in ${a.functions_ahead} function${a.functions_ahead===1?'':'s'}`:'nothing ahead of main'}${a.linked_ahead?` &middot; +${fmt(a.linked_ahead)} B linked`:''}</div>
  ${a.units.length?`<ul>${a.units.map(u=>`<li><span>${esc(u.name)}</span><span>+${fmt(u.bytes)}</span></li>`).join('')}</ul>`:''}</div>`).join('');
}

function renderCommits(d){
 const h=d.history,rows=[];
 for(let i=h.length-1;i>=0&&rows.length<12;i--){
  const c=h[i],p=h[i-1],dm=p?c.matched_code-p.matched_code:0,dl=p?(c.complete_code??c.linked_code)-(p.complete_code??p.linked_code):0;
  const delta=[dm?`<span class="${dm>0?'up':''}">${dm>0?'+':''}${fmt(dm)} matched</span>`:'',dl?`<span class="${dl>0?'up':''}">${dl>0?'+':''}${fmt(dl)} linked</span>`:''].filter(Boolean).join('<br>');
  rows.push(`<tr><td><code>${esc(c.commit)}</code></td><td class="subj">${esc(c.subject)}</td><td class="d hide-sm">${delta}</td><td class="when">${ago(+c.time)}</td></tr>`)}
 $('#commits').innerHTML=rows.join('')||'<tr><td style="color:var(--text-3)">No history yet.</td></tr>';
}

function drawChart(){
 const d=state.data,h=d.history,svg=$('#chart'),note=$('#chartnote');if(!svg)return;
 const T=d.report.measures.total_code;
 if(h.length<2||!T){svg.style.display='none';note.textContent='Not enough history yet.';return}
 const W=svg.clientWidth||600,H=220,pl=38,pr=10,pt=10,pb=24;
 svg.setAttribute('viewBox',`0 0 ${W} ${H}`);
 const t0=+h[0].time,t1=+h[h.length-1].time,now=Math.max(t1,Math.min(d.now,t1+(t1-t0)*.02));
 const lk=x=>x.complete_code??x.linked_code;
 const maxP=Math.max(...h.map(x=>pct(x.matched_code,T)),1);const step=maxP>40?10:maxP>15?5:maxP>6?2:1;const top=Math.ceil(maxP*1.08/step)*step;
 const X=t=>pl+(W-pl-pr)*(t-t0)/Math.max(1,now-t0),Y=p=>pt+(H-pt-pb)*(1-p/top);
 const area=f=>{let s=`M${X(t0)},${Y(0)}`;h.forEach((x,i)=>{const y=Y(pct(f(x),T));s+=(i?`H${X(+x.time)}`:'')+`V${y}`});return s+`H${X(now)}V${Y(0)}Z`};
 const edge=f=>{let s='';h.forEach((x,i)=>{const y=Y(pct(f(x),T));s+=i?`H${X(+x.time)}V${y}`:`M${X(t0)},${y}`});return s+`H${X(now)}`};
 let g='';for(let p=0;p<=top+1e-9;p+=step)g+=`<line class="grid" x1="${pl}" x2="${W-pr}" y1="${Y(p)}" y2="${Y(p)}"/><text x="${pl-6}" y="${Y(p)+4}" text-anchor="end">${p}%</text>`;
 const span=now-t0,n=Math.max(2,Math.min(6,Math.floor((W-pl)/110)));
 for(let i=0;i<=n;i++){const t=t0+span*i/n,dt=new Date(t*1000);const lbl=span>5*86400?dt.toLocaleDateString(undefined,{month:'short',day:'numeric'}):dt.toLocaleString(undefined,{weekday:'short',hour:'2-digit',minute:'2-digit'});g+=`<text x="${X(t)}" y="${H-6}" text-anchor="${i===0?'start':i===n?'end':'middle'}">${esc(lbl)}</text>`}
 svg.innerHTML=g+`<path class="a-m" d="${area(x=>x.matched_code)}"/><path class="a-l" d="${area(lk)}"/><path class="l-m" d="${edge(x=>x.matched_code)}"/><g id="hover" style="display:none"><line class="cross" y1="${pt}" y2="${H-pb}"/><circle class="dot" r="4" style="fill:var(--matched)"/><circle class="dot" r="4" style="fill:var(--linked)"/></g><rect x="${pl}" y="0" width="${W-pl-pr}" height="${H}" fill="transparent" id="hit"/>`;
 const built=h.filter(x=>x.report!==false).length;
 const last=h[h.length-1];
 note.innerHTML=`${h.length} commits, from ${pf(pct(h[0].matched_code,T),1)} to ${pf(pct(last.matched_code,T),1)} matched and ${pf(pct(lk(last),T),1)} linked. `+
  (built===h.length?'Each point is one CI build of main, read from its report.json.':`Matched and linked come from a build report for ${built} of ${h.length} commits; the others repeat the previous value.`);
 const tip=$('#tip'),hov=svg.querySelector('#hover'),[cl,cm,ck]=[hov.children[0],hov.children[1],hov.children[2]];
 const move=e=>{const rc=svg.getBoundingClientRect(),x=(e.clientX-rc.left)*W/rc.width,t=t0+(x-pl)/(W-pl-pr)*(now-t0);
  let lo=0,hi=h.length-1;while(lo<hi){const mid=(lo+hi+1)>>1;if(+h[mid].time<=t)lo=mid;else hi=mid-1}
  const c=h[lo],mp=pct(c.matched_code,T),lp=pct(lk(c),T),cx=Math.min(X(Math.max(t,t0)),W-pr);
  hov.style.display='';cl.setAttribute('x1',cx);cl.setAttribute('x2',cx);cm.setAttribute('cx',cx);cm.setAttribute('cy',Y(mp));ck.setAttribute('cx',cx);ck.setAttribute('cy',Y(lp));
  tip.innerHTML=`<div class="h">${esc(c.commit)} &middot; ${new Date(c.time*1000).toLocaleString(undefined,{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})}</div><div class="t">${esc(c.subject)}</div><div class="r"><i class="sw matched"></i>Matched<b>${pf(mp)}</b></div><div class="r"><i class="sw linked"></i>Linked<b>${pf(lp)}</b></div>${c.report===false?'<div class="h" style="margin-top:4px">no build report: matched repeats the previous one</div>':''}`;
  tip.style.display='block';const bw=svg.parentNode.clientWidth,px=cx*rc.width/W,tw=tip.offsetWidth;tip.style.left=Math.max(0,Math.min(bw-tw,px+12>bw-tw?px-tw-12:px+12))+'px';tip.style.top='8px'};
 const leave=()=>{hov.style.display='none';tip.style.display='none'};
 const hit=svg.querySelector('#hit');hit.addEventListener('pointermove',move);hit.addEventListener('pointerdown',move);hit.addEventListener('pointerleave',leave);
}

async function load(){
 let d;try{d=await (await fetch(API,{cache:'no-store'})).json()}catch(e){$('#meta').textContent='Progress data not reachable; retrying.';return}
 if(d.error){$('#meta').textContent='Error: '+d.error;return}
 if(!d.report){$('#meta').textContent='';$('#main').innerHTML=`<section class="card"><h2>No numbers yet</h2><p class="note">${NO_REPORT}</p></section>`;return}
 $('#meta').innerHTML=`branch <b>${esc(d.branch)}</b> &middot; last build <b title="${esc(new Date(d.report.mtime*1000).toLocaleString())}">${ago(d.report.mtime)}</b>`;
 const y=window.scrollY;state.data=d;render(d);window.scrollTo(0,y);
}
let rt;window.addEventListener('resize',()=>{clearTimeout(rt);rt=setTimeout(()=>state.data&&drawChart(),150)});
load();setInterval(()=>{if(!document.activeElement||document.activeElement.id!=='q')load()},REFRESH);
</script></body></html>'''


STATIC_FOOTER = ('<footer>Built by CI from <code>build/GV4E69/report.json</code> (objdiff) on every push to main. '
                 'Only progress numbers are published. <a href="history.json">history.json</a></footer>')


def export(out_dir, history_path, sha, report_path=REPORT):
    """The static site for GitHub Pages: index.html (reads progress.json, no "in flight" panel)
    and progress.json + history.json, all from report.json, symbols.txt and the history file.
    With no report (no build of main has made one yet) the page says so."""
    rep = parse_report(report_path) if report_path and os.path.exists(report_path) else None
    try:
        history = json.load(open(history_path)) if history_path else parse_history(HISTORY)
    except (OSError, ValueError):
        history = []
    data = {
        'now': time.time(),
        'branch': 'main' + (' @ ' + sha[:7] if sha else ''),
        'report': {k: v for k, v in rep.items() if not k.startswith('_')} if rep else None,
        'symbols': cached(SYMBOLS, parse_symbols) or {'functions': 0, 'named': 0},
        'history': history,
        'agents': [],
    }
    page = PAGE
    for old, new in (("const API='/api/progress',REFRESH=20000,AGENTS_PANEL=true,NO_REPORT='No report.json yet: run ninja once.';",
                      "const API='progress.json',REFRESH=300000,AGENTS_PANEL=false,"
                      "NO_REPORT='No build of main has produced a progress report yet.';"),
                     (re.search(r'<footer>.*?</footer>', PAGE, re.S).group(0), STATIC_FOOTER)):
        assert old in page, old
        page = page.replace(old, new)
    os.makedirs(out_dir, exist_ok=True)
    open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8').write(page)
    json.dump(data, open(os.path.join(out_dir, 'progress.json'), 'w'), separators=(',', ':'))
    json.dump(history, open(os.path.join(out_dir, 'history.json'), 'w'), indent=0)
    open(os.path.join(out_dir, '.nojekyll'), 'w').close()
    print('exported %s: index.html, progress.json, history.json (%d records)%s'
          % (out_dir, len(history), '' if rep else ', no report yet'))


class H(BaseHTTPRequestHandler):
    agents_dir = AGENTS

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith('/api/progress'):
            try:
                body = json.dumps(progress(self.agents_dir), separators=(',', ':')).encode()
                self._send(200, body, 'application/json')
            except Exception as e:
                self._send(500, json.dumps({'error': str(e)}).encode(), 'application/json')
        elif self.path == '/' or self.path.startswith('/index'):
            self._send(200, PAGE.encode(), 'text/html; charset=utf-8')
        else:
            self._send(404, b'not found', 'text/plain')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='0.0.0.0')
    ap.add_argument('--port', type=int, default=8420)
    ap.add_argument('--agents', default=AGENTS, help='folder of agent worktrees for the "in flight" panel')
    ap.add_argument('--export', metavar='DIR', help='write the static site (GitHub Pages) to DIR and exit')
    ap.add_argument('--history', metavar='FILE', help='with --export: the history to publish '
                    '(default build/dashboard_history.json)')
    ap.add_argument('--sha', default='', help='with --export: the commit the report is for')
    ap.add_argument('--report', default=REPORT, help='with --export: the report.json to publish '
                    '(default build/GV4E69/report.json)')
    a = ap.parse_args()
    if a.export:
        export(a.export, a.history, a.sha, a.report)
        raise SystemExit(0)
    H.agents_dir = a.agents
    srv = ThreadingHTTPServer((a.host, a.port), H)
    print(f'mvp2005 dashboard on http://{a.host}:{a.port}/  (root {ROOT}, agents {a.agents})', flush=True)
    srv.serve_forever()
