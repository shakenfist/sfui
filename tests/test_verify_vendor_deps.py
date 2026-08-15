"""Tests for tools/verify-vendor-deps.sh: the drift detection.

The script hashes the vendored bundles against digests pinned in
its own source, so the fixture here is a copy of the real bundles
in tmp_path with the script pointed at it -- which is what the
optional root argument exists for. A clean copy, a byte-modified
copy and a missing file are the three outcomes worth pinning.
"""

import hashlib
import pathlib
import re
import subprocess


REPO = pathlib.Path(__file__).resolve().parent.parent
VERIFY = REPO / 'tools' / 'verify-vendor-deps.sh'
PINNED = ('lit-core.min.js', 'morphdom-umd.js')


def verify(root):
    return subprocess.run([VERIFY, str(root)], capture_output=True, text=True)


def fixture(tmp_path):
    for name in PINNED:
        (tmp_path / name).write_bytes((REPO / name).read_bytes())
    return tmp_path


def test_the_real_repository_verifies():
    result = subprocess.run([VERIFY], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    for name in PINNED:
        assert name in result.stdout


def test_a_faithful_copy_verifies(tmp_path):
    assert verify(fixture(tmp_path)).returncode == 0


def test_a_modified_file_is_a_mismatch(tmp_path):
    root = fixture(tmp_path)
    target = root / 'morphdom-umd.js'
    target.write_bytes(target.read_bytes() + b'// tampered\n')
    result = verify(root)
    assert result.returncode != 0
    assert 'SHA-256 mismatch for morphdom-umd.js' in result.stderr


def test_a_missing_file_fails(tmp_path):
    root = fixture(tmp_path)
    (root / 'lit-core.min.js').unlink()
    result = verify(root)
    assert result.returncode != 0
    assert 'lit-core.min.js is missing' in result.stderr


def test_the_pinned_payloads_match_their_recorded_upstream_digests():
    """The provenance recorded beside each pin is re-derivable.

    This is the property the script header claims: strip the
    recorded number of provenance header lines and the remainder
    hashes to the recorded upstream digest. A bump that refreshes
    the committed digest but not the provenance fails here.
    """
    script = VERIFY.read_text()
    for name in PINNED:
        provenance = re.search(
            re.escape(f'# {name} ') + r'.*?(\d+)-line provenance header.*?'
            r'upstream sha256\n#\s+([0-9a-f]{64})',
            script, flags=re.DOTALL)
        assert provenance, f'{name} has no re-derivable provenance recorded'
        header_lines, upstream = int(provenance.group(1)), provenance.group(2)
        body = (REPO / name).read_bytes().split(b'\n', header_lines)[header_lines]
        assert hashlib.sha256(body).hexdigest() == upstream, \
            f'{name} payload does not match its recorded upstream digest'
