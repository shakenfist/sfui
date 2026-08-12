"""Tests for tools/vendor.sh: the round trip and drift detection.

Vendored copies are written to pytest's tmp_path, which lives
outside the repository tree on purpose: the fleet-wide sfui-vendor
audit identifies a vendored copy by its .sfui-commit file, so one
must never appear under this repository.
"""

import pathlib
import subprocess


REPO = pathlib.Path(__file__).resolve().parent.parent
VENDOR = REPO / 'tools' / 'vendor.sh'


def vendor(*args):
    return subprocess.run([VENDOR, *args], capture_output=True, text=True)


def test_vendor_copies_the_distributable_set(tmp_path):
    target = tmp_path / 'sfui'
    result = vendor(str(target))
    assert result.returncode == 0

    for name in ('README.md', 'tokens.css', 'sf.css', 'sf-theme.js', 'shakenfist-logo.svg',
                 'lit-core.min.js', 'morphdom-umd.js'):
        assert (target / name).read_bytes() == (REPO / name).read_bytes()
    repo_components = sorted(path.name for path in (REPO / 'components').iterdir())
    target_components = sorted(path.name for path in (target / 'components').iterdir())
    assert target_components == repo_components

    head = subprocess.run(['git', '-C', str(REPO), 'rev-parse', 'HEAD'],
                          capture_output=True, text=True).stdout.strip()
    assert (target / '.sfui-commit').read_text().strip() == head


def test_check_passes_on_a_faithful_copy(tmp_path):
    target = tmp_path / 'sfui'
    vendor(str(target))
    result = vendor('--check', str(target))
    assert result.returncode == 0


def test_check_fails_on_an_edited_file(tmp_path):
    target = tmp_path / 'sfui'
    vendor(str(target))
    edited = (target / 'tokens.css').read_text().replace('#0f1117', '#000000')
    (target / 'tokens.css').write_text(edited)
    result = vendor('--check', str(target))
    assert result.returncode != 0
    assert 'tokens.css' in result.stdout


def test_check_fails_on_a_stray_component(tmp_path):
    target = tmp_path / 'sfui'
    vendor(str(target))
    (target / 'components' / 'sf-rogue.js').write_text('// edited in place\n')
    result = vendor('--check', str(target))
    assert result.returncode != 0


def test_check_fails_on_a_missing_file(tmp_path):
    target = tmp_path / 'sfui'
    vendor(str(target))
    (target / 'sf.css').unlink()
    result = vendor('--check', str(target))
    assert result.returncode != 0


def test_usage_error_without_a_target():
    result = vendor()
    assert result.returncode != 0
    assert 'Usage' in result.stderr
