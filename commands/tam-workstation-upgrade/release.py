"""Resolve and validate a released Tamlinux assembly without changing a host."""
import json
import re
import urllib.error
import urllib.request

API = 'https://api.github.com/repos/greenermoose/tamlinux-packages'
RAW = 'https://raw.githubusercontent.com/greenermoose/tamlinux-packages'
VERSION = re.compile(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\Z')
REVISION = re.compile(r'[0-9a-f]{40}\Z')
MAX_RESPONSE = 2 * 1024 * 1024


class ReleaseError(Exception):
    pass


def get_json(url):
    request = urllib.request.Request(url, headers={'Accept': 'application/vnd.github+json',
                                                   'User-Agent': 'tam-workstation-upgrade'})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            final = response.geturl()
            if not (final.startswith(API + '/') or final.startswith(RAW + '/')):
                raise ReleaseError('unexpected release server redirect')
            payload = response.read(MAX_RESPONSE + 1)
        if len(payload) > MAX_RESPONSE:
            raise ReleaseError('release metadata exceeds size limit')
        return json.loads(payload)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise ReleaseError(f'cannot read release metadata: {exc}') from exc


def resolve(version=None, fetch=get_json):
    if version is not None and not VERSION.fullmatch(version):
        raise ReleaseError('version must be a plain X.Y.Z release')
    endpoint = f'{API}/releases/tags/{version}' if version else f'{API}/releases/latest'
    release = fetch(endpoint)
    if not isinstance(release, dict):
        raise ReleaseError('release metadata is malformed')
    tag = release.get('tag_name', '')
    if not isinstance(tag, str) or not VERSION.fullmatch(tag):
        raise ReleaseError('release does not have a plain version tag')
    if release.get('draft') is not False or release.get('prerelease') is not False:
        raise ReleaseError('release is a draft or prerelease')
    if version and tag != version:
        raise ReleaseError('release tag differs from requested version')
    ref = fetch(f'{API}/git/ref/tags/{tag}')
    if not isinstance(ref, dict) or not isinstance(ref.get('object'), dict):
        raise ReleaseError('release tag is malformed')
    obj = ref.get('object', {})
    for _ in range(4):
        sha, kind = obj.get('sha'), obj.get('type')
        if not isinstance(sha, str) or not REVISION.fullmatch(sha):
            raise ReleaseError('invalid release tag revision')
        if kind == 'commit':
            break
        if kind != 'tag':
            raise ReleaseError('release tag does not point to a commit')
        annotated = fetch(f'{API}/git/tags/{sha}')
        if not isinstance(annotated, dict) or not isinstance(annotated.get('object'), dict):
            raise ReleaseError('annotated release tag is malformed')
        obj = annotated['object']
    else:
        raise ReleaseError('release tag nesting exceeds limit')
    record = fetch(f'{RAW}/{sha}/deliveries/tamlinux-{tag}.json')
    lock = fetch(f'{RAW}/{sha}/flake.lock')
    if not isinstance(record, dict) or not isinstance(lock, dict):
        raise ReleaseError('release record or lock is malformed')
    if record.get('schemaVersion') != 1 or record.get('id') != f'tamlinux-{tag}' or record.get('version') != tag:
        raise ReleaseError('delivery record does not identify this release')
    try:
        nodes = lock['nodes']
        inputs = nodes[lock['root']]['inputs']
        selected = {name: nodes[node]['locked'] for name, node in inputs.items()}
        if not selected or record['components'] != selected:
            raise ReleaseError('delivery record and lock inputs disagree')
        if selected['tamlinux']['repo'] != 'tamlinux' or selected['tamlinux']['owner'] != 'greenermoose':
            raise ReleaseError('delivery record has an unexpected product source')
        if any(not REVISION.fullmatch(value.get('rev', '')) for value in selected.values()):
            raise ReleaseError('release has an unpinned input')
    except (KeyError, TypeError, AttributeError) as exc:
        raise ReleaseError('release record or lock is malformed') from exc
    return {'version': tag, 'revision': sha, 'record': record, 'components': selected}
