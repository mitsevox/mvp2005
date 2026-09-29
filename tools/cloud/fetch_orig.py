"""Fetch orig/ (the game's main.dol, which is never in git) from the private build container that CI
uses (ghcr.io/mitsevox/mvp2005-build), without docker: registry API + the image's tar layers.
    MVP_BUILD_TOKEN=<token> python tools/cloud/fetch_orig.py [VERSION]
The token is a GitHub token with read:packages that the OWNER creates and stores as a secret of the
cloud environment; nothing here prints or stores it. Extracts orig/ into the repo root and checks the
DOL against the hash in config/<VERSION>/config.yml (VERSION defaults to the only one in config/).
Taken from tw2004's tools/cloud/fetch_orig.py."""
import base64, hashlib, io, json, os, pathlib, sys, tarfile, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
IMAGE, TAG = os.environ.get('MVP_BUILD_IMAGE', 'mitsevox/mvp2005-build'), os.environ.get('MVP_BUILD_TAG', 'main')
USER = os.environ.get('MVP_BUILD_USER', 'mitsevox')
TOKEN = os.environ.get('MVP_BUILD_TOKEN')
if not TOKEN:
    sys.exit('MVP_BUILD_TOKEN is not set: the owner adds it as a secret of the cloud environment')
VERSIONS = sorted(p.name for p in (ROOT / 'config').iterdir() if (p / 'config.yml').exists())
VERSION = sys.argv[1] if len(sys.argv) > 1 else (VERSIONS[0] if len(VERSIONS) == 1 else None)
if VERSION not in VERSIONS:
    sys.exit('give the version, one of: %s' % ', '.join(VERSIONS))

ACCEPT = ', '.join(['application/vnd.oci.image.index.v1+json',
                    'application/vnd.docker.distribution.manifest.list.v2+json',
                    'application/vnd.oci.image.manifest.v1+json',
                    'application/vnd.docker.distribution.manifest.v2+json'])


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None                       # handled by hand: the blob store must not get our token


opener = urllib.request.build_opener(NoRedirect)


def get(url, headers):
    try:
        return opener.open(urllib.request.Request(url, headers=headers))
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308):
            return urllib.request.urlopen(e.headers['Location'])     # signed URL, no auth header
        sys.exit('registry error %d for %s' % (e.code, url.split('?')[0]))


basic = base64.b64encode(('%s:%s' % (USER, TOKEN)).encode()).decode()
tok = json.load(get('https://ghcr.io/token?service=ghcr.io&scope=repository:%s:pull' % IMAGE,
                    {'Authorization': 'Basic ' + basic}))['token']
H = {'Authorization': 'Bearer ' + tok, 'Accept': ACCEPT}
man = json.load(get('https://ghcr.io/v2/%s/manifests/%s' % (IMAGE, TAG), H))
if 'manifests' in man:                    # a multi-platform index: take linux/amd64
    d = next(m['digest'] for m in man['manifests']
             if m.get('platform', {}).get('os') == 'linux' and m['platform'].get('architecture') == 'amd64')
    man = json.load(get('https://ghcr.io/v2/%s/manifests/%s' % (IMAGE, d), H))
found = 0
for layer in reversed(man['layers']):     # the orig/ files are in one of the last layers
    blob = get('https://ghcr.io/v2/%s/blobs/%s' % (IMAGE, layer['digest']), H)
    with tarfile.open(fileobj=io.BufferedReader(blob), mode='r|*') as tf:
        for m in tf:
            name = m.name.lstrip('./')
            if name.startswith('orig/') and (m.isfile() or m.isdir()):
                tf.extract(m, ROOT, filter='data') if hasattr(tarfile, 'data_filter') else tf.extract(m, ROOT)
                found += m.isfile()
    if found:
        break
dol = ROOT / 'orig' / VERSION / 'sys/main.dol'
if not dol.exists():
    sys.exit('no orig/%s/sys/main.dol in the image layers' % VERSION)
want = next(l.split(':', 1)[1].strip() for l in (ROOT / 'config' / VERSION / 'config.yml').read_text().splitlines()
            if l.startswith('hash:'))
got = hashlib.sha1(dol.read_bytes()).hexdigest()
print('orig/: %d files; main.dol sha1 %s: %s' % (found, got, 'OK' if got == want else 'MISMATCH (want %s)' % want))
sys.exit(0 if got == want else 1)
