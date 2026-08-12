"""Tests for tools/consistency-check.py.

The checker guards the design-system rules, so these tests build a
minimal synthetic repository that passes, break one rule at a
time, and assert the right finding appears -- plus a run against
the real repository, which must be clean.
"""

import importlib.util
import pathlib
import subprocess

import pytest


REPO = pathlib.Path(__file__).resolve().parent.parent
CHECKER = REPO / 'tools' / 'consistency-check.py'

spec = importlib.util.spec_from_file_location('consistency_check', CHECKER)
consistency_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(consistency_check)


CLEAN = {
    'tokens.css': """
:root {
    --sf-bg: #0f1117;
    --sf-red: #f87171;
    --sf-brand: #58a8c8;
}
:root[data-theme="light"] {
    --sf-bg: #f4f5f8;
    --sf-red: #b91c1c;
    --sf-brand: #1d6d87;
}
""",
    'sf.css': """
:root {
    --sf-radius: 6px;
}
.sf-header {
    border-color: color-mix(in srgb, var(--sf-brand) 45%, transparent);
}
.sf-card {
    color: var(--sf-red);
    border-radius: var(--sf-radius);
}
""",
    'demo.html': '<div class="sf-header"><div class="sf-card"></div></div>\n',
    'components/sf-thing.js': """
import {LitElement, css} from '../lit-core.min.js';

class SfThing extends LitElement {
    static styles = css`
        div {
            color: var(--sf-red, #f87171);
            border-radius: var(--sf-radius, 6px);
        }
    `;

    report() {
        this.dispatchEvent(new CustomEvent('sf-thing-done', {detail: {}}));
    }
}

customElements.define('sf-thing', SfThing);
""",
    'tools/vendor.sh': """
files=(
    README.md
    tokens.css
    sf.css
)
""",
    'docs/vendoring.md': """
## Layout

    README.md         the pitch
    tokens.css        the tokens
    sf.css            the page styles
    components/       the components

## Something else
""",
    'README.md': 'the pitch\n',
}


def build_repo(tmp_path, overrides=None):
    files = dict(CLEAN)
    files.update(overrides or {})
    for name, content in files.items():
        if content is None:
            continue
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    return tmp_path


def findings(tmp_path, overrides=None):
    return consistency_check.Checker(build_repo(tmp_path, overrides)).run()


def test_the_synthetic_repo_is_clean(tmp_path):
    assert findings(tmp_path) == []


def test_the_real_repo_is_clean():
    result = subprocess.run([CHECKER], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout


def test_token_missing_from_light_palette(tmp_path):
    tokens = CLEAN['tokens.css'].replace('    --sf-red: #b91c1c;\n', '')
    assert any('--sf-red' in finding and 'not the light palette' in finding
               for finding in findings(tmp_path, {'tokens.css': tokens}))


def test_fallback_not_matching_dark_value(tmp_path):
    component = CLEAN['components/sf-thing.js'].replace('#f87171', '#ff0000')
    assert any('fallback for --sf-red' in finding
               for finding in findings(tmp_path, {'components/sf-thing.js': component}))


def test_color_literal_outside_a_fallback(tmp_path):
    component = CLEAN['components/sf-thing.js'].replace(
        'color: var(--sf-red, #f87171);', 'color: #f87171;')
    assert any('outside a var() fallback' in finding
               for finding in findings(tmp_path, {'components/sf-thing.js': component}))


def test_color_literal_in_page_styles(tmp_path):
    styles = CLEAN['sf.css'].replace('var(--sf-red)', 'rgba(248, 113, 113, 0.5)')
    assert any('sf.css' in finding and 'color literal' in finding
               for finding in findings(tmp_path, {'sf.css': styles}))


def test_undefined_token_reference(tmp_path):
    styles = CLEAN['sf.css'].replace('var(--sf-red)', 'var(--sf-read)')
    assert any('var(--sf-read) does not name' in finding
               for finding in findings(tmp_path, {'sf.css': styles}))


def test_unprefixed_element_and_event_names(tmp_path):
    component = CLEAN['components/sf-thing.js'].replace(
        "customElements.define('sf-thing'", "customElements.define('thing'").replace(
        "new CustomEvent('sf-thing-done'", "new CustomEvent('thing-done'")
    found = findings(tmp_path, {'components/sf-thing.js': component})
    assert any("custom element 'thing'" in finding for finding in found)
    assert any("event 'thing-done'" in finding for finding in found)


def test_disallowed_import(tmp_path):
    component = CLEAN['components/sf-thing.js'].replace(
        "from '../lit-core.min.js'", "from 'https://esm.sh/lit'")
    assert any('imports' in finding and 'esm.sh' in finding
               for finding in findings(tmp_path, {'components/sf-thing.js': component}))


def test_forbidden_api_reference(tmp_path):
    component = CLEAN['components/sf-thing.js'].replace(
        'this.dispatchEvent', "localStorage.setItem('x', 'y'); this.dispatchEvent")
    assert any("references 'localStorage'" in finding
               for finding in findings(tmp_path, {'components/sf-thing.js': component}))


def test_forbidden_api_in_a_comment_is_fine(tmp_path):
    component = CLEAN['components/sf-thing.js'].replace(
        '    report() {', '    // never touches localStorage or location.href\n    report() {')
    assert findings(tmp_path, {'components/sf-thing.js': component}) == []


def test_brand_outside_page_chrome(tmp_path):
    styles = CLEAN['sf.css'] + '\n.sf-headerish {\n    color: var(--sf-brand);\n}\n'
    demo = CLEAN['demo.html'].replace('sf-header', 'sf-header sf-headerish')
    assert any('outside a .sf-header rule' in finding
               for finding in findings(tmp_path, {'sf.css': styles, 'demo.html': demo}))


def test_class_shadowing_an_element_name(tmp_path):
    styles = CLEAN['sf.css'] + '\n.sf-thing {\n    color: var(--sf-red);\n}\n'
    demo = CLEAN['demo.html'].replace('sf-card', 'sf-card sf-thing')
    assert any('.sf-thing duplicates the <sf-thing> element name' in finding
               for finding in findings(tmp_path, {'sf.css': styles, 'demo.html': demo}))


def test_primitive_missing_from_demo(tmp_path):
    demo = CLEAN['demo.html'].replace(' sf-card', '').replace('<div class="sf-card"></div>', '')
    assert any('.sf-card is defined in sf.css but never rendered' in finding
               for finding in findings(tmp_path, {'demo.html': demo}))


def test_vendor_list_and_layout_disagree(tmp_path):
    vendoring = CLEAN['docs/vendoring.md'].replace('    sf.css            the page styles\n', '')
    assert any('sf.css is vendored but missing from the Layout list' in finding
               for finding in findings(tmp_path, {'docs/vendoring.md': vendoring}))


def test_vendored_file_must_exist(tmp_path):
    assert any('README.md is listed for vendoring but does not exist' in finding
               for finding in findings(tmp_path, {'README.md': None}))


def test_extract_block_handles_nesting():
    css = '@layer x {\n.a { color: red; }\n}\n:root {\n--sf-a: 1;\n}\n'
    block = consistency_check.extract_block(css, ':root')
    assert consistency_check.parse_declarations(block) == {'--sf-a': '1'}


def test_enclosing_selectors_tracks_the_stack():
    css = '@layer sfui.components {\n.sf-header {\n color: var(--sf-brand);\n}\n}\n'
    position = css.index('var(--sf-brand')
    stack = consistency_check.enclosing_selectors(css, position)
    assert stack == ['@layer sfui.components', '.sf-header']
