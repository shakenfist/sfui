#!/usr/bin/env python3

"""Check the mechanical sfui design-system rules.

This is the checker described in docs/consistency-audit.md: it
mechanises the rules that make the design system auditable, so a
pull request that breaks one fails pre-commit and CI rather than
waiting for a human to run the grep recipes. Uses only the Python
standard library.
"""

import re
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent

# Files a component may import: the vendored Lit runtime, or a
# sibling component.
ALLOWED_IMPORT_RE = re.compile(r'^\.\./lit-core\.min\.js$|^\./sf-[\w-]+\.js$')

# APIs a component must never touch; sf-theme.js is page
# infrastructure and exempt (see docs/components.md).
FORBIDDEN_API_RE = re.compile(
    r'\b(fetch|localStorage|sessionStorage)\b|\bwindow\.(location|history)\b|'
    r'\bdocument\.(cookie|location)\b|\b(location|history)\.[a-zA-Z]')

COLOR_LITERAL_RE = re.compile(r'#[0-9a-fA-F]{3,8}\b|\brgba?\(')

VAR_WITH_FALLBACK_RE = re.compile(r'var\((--[\w-]+)\s*,\s*([^();]+)\)')
VAR_REFERENCE_RE = re.compile(r'var\((--[\w-]+)')
DECLARATION_RE = re.compile(r'(--[\w-]+)\s*:\s*([^;{}]+);')


def strip_css_comments(text):
    return re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)


def strip_js_comments(text):
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Avoid eating URLs ("https://...") when removing line comments.
    return re.sub(r'(?<!:)//[^\n]*', '', text)


def strip_html_comments(text):
    return re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)


def normalize(value):
    return ' '.join(value.split())


def extract_block(css, selector):
    """Return the text of the top-level block for an exact selector."""
    marker = re.search(re.escape(selector) + r'\s*\{', css)
    if not marker:
        return None
    depth = 1
    start = marker.end()
    for position in range(start, len(css)):
        if css[position] == '{':
            depth += 1
        elif css[position] == '}':
            depth -= 1
            if depth == 0:
                return css[start:position]
    return None


def parse_declarations(block):
    return {name: normalize(value) for name, value in DECLARATION_RE.findall(block or '')}


def parse_palettes(tokens_css):
    dark = parse_declarations(extract_block(tokens_css, ':root'))
    light = parse_declarations(extract_block(tokens_css, ':root[data-theme="light"]'))
    return dark, light


def enclosing_selectors(css, position):
    """Return the stack of block headers open at a character position."""
    stack = []
    header_start = 0
    for index in range(position):
        character = css[index]
        if character == '{':
            stack.append(normalize(css[header_start:index]))
            header_start = index + 1
        elif character == '}':
            if stack:
                stack.pop()
            header_start = index + 1
        elif character == ';':
            header_start = index + 1
    return stack


def parse_vendor_files(vendor_sh):
    match = re.search(r'files=\(\n(.*?)\)', vendor_sh, flags=re.DOTALL)
    if not match:
        return None
    return [line.strip() for line in match.group(1).splitlines() if line.strip()]


def parse_layout_entries(vendoring_md):
    """Parse the file list from the Layout section of docs/vendoring.md."""
    section = re.search(r'## Layout\n(.*?)\n## ', vendoring_md, flags=re.DOTALL)
    if not section:
        return None
    entries = []
    for line in section.group(1).splitlines():
        match = re.match(r'^ {4}(\S+)(\s|$)', line)
        if match and ('.' in match.group(1) or match.group(1).endswith('/')):
            entries.append(match.group(1))
    return entries


def parse_vendored_dependencies(vendoring_md):
    """Parse the file names from the Vendored dependencies section of
    docs/vendoring.md."""
    section = re.search(r'## Vendored dependencies\n(.*?)\n## ', vendoring_md, flags=re.DOTALL)
    if not section:
        return None
    return re.findall(r'^- `(\S+)`:', section.group(1), flags=re.MULTILINE)


def parse_pinned_files(verify_sh):
    """Parse the file names from the checksum list of
    tools/verify-vendor-deps.sh."""
    match = re.search(r'\nchecksums="\n(.*?)\n"', verify_sh, flags=re.DOTALL)
    if not match:
        return None
    return [line.split()[-1] for line in match.group(1).splitlines() if line.strip()]


class Checker:
    def __init__(self, repo):
        self.repo = repo
        self.findings = []

    def finding(self, path, message):
        self.findings.append(f'{path}: {message}')

    def read(self, relative):
        return (self.repo / relative).read_text()

    def component_paths(self):
        return sorted((self.repo / 'components').glob('*.js'))

    def component_text(self, path):
        """A component's source with comments stripped, so a token
        value or hex color discussed in a file header is not a
        finding."""
        return strip_js_comments(path.read_text())

    def run(self):
        tokens_css = self.read('tokens.css')
        sf_css = strip_css_comments(self.read('sf.css'))
        # Comments are stripped throughout: a hex value mentioned in an
        # HTML comment is not a violation, and a class named only in a
        # comment is not rendered.
        demo_html = strip_html_comments(self.read('demo.html'))
        dark, light = parse_palettes(strip_css_comments(tokens_css))

        self.check_token_parity(dark, light)
        definitions = dict(dark)
        definitions.update(parse_declarations(sf_css))
        self.check_fallbacks_and_colors(definitions)
        self.check_page_colors('sf.css', sf_css)
        self.check_page_colors('demo.html', demo_html)
        self.check_var_references(definitions, sf_css, demo_html)
        self.check_component_names()
        self.check_component_purity()
        self.check_brand_scope(sf_css)
        self.check_reserved_class_names(sf_css)
        self.check_demo_coverage(sf_css, demo_html)
        self.check_vendor_list()
        self.check_dependency_pins()
        return self.findings

    def check_token_parity(self, dark, light):
        """Every token is defined in both palettes of tokens.css."""
        for name in sorted(set(dark) - set(light)):
            self.finding('tokens.css', f'{name} is defined in the dark palette but not the light palette')
        for name in sorted(set(light) - set(dark)):
            self.finding('tokens.css', f'{name} is defined in the light palette but not the dark palette')

    def check_fallbacks_and_colors(self, definitions):
        """Component var() fallbacks match the dark definitions, and no
        other color literal appears in a component."""
        for path in self.component_paths():
            relative = path.relative_to(self.repo)
            text = self.component_text(path)
            remainder = text
            for name, fallback in VAR_WITH_FALLBACK_RE.findall(text):
                if name not in definitions:
                    self.finding(relative, f'var() fallback for {name}, which is not a defined token')
                elif normalize(fallback) != definitions[name]:
                    self.finding(
                        relative,
                        f'var() fallback for {name} is {normalize(fallback)!r} but the dark definition is '
                        f'{definitions[name]!r}')
            remainder = VAR_WITH_FALLBACK_RE.sub('', remainder)
            for match in COLOR_LITERAL_RE.findall(remainder):
                self.finding(relative, f'color literal {match!r} outside a var() fallback')

    def check_page_colors(self, relative, text):
        """No hex or rgb()/rgba() literals at all in sf.css or demo.html;
        tints are color-mix() on tokens."""
        for match in COLOR_LITERAL_RE.findall(text):
            self.finding(relative, f'color literal {match!r}; use a token or color-mix() on one')

    def check_var_references(self, definitions, sf_css, demo_html):
        """Every var(--sf-*) reference names a defined custom property
        (a typo'd token silently falls back)."""
        sources = [('sf.css', sf_css), ('demo.html', demo_html)]
        sources += [(path.relative_to(self.repo), self.component_text(path)) for path in self.component_paths()]
        for relative, text in sources:
            for name in VAR_REFERENCE_RE.findall(text):
                if name not in definitions:
                    self.finding(relative, f'var({name}) does not name a defined custom property')

    def check_component_names(self):
        """Custom element and dispatched event names start with sf-."""
        for path in self.component_paths():
            relative = path.relative_to(self.repo)
            text = self.component_text(path)
            for name in re.findall(r'customElements\.define\(\s*[\'"]([^\'"]+)', text):
                if not name.startswith('sf-'):
                    self.finding(relative, f'custom element {name!r} is not sf- prefixed')
            for name in re.findall(r'new CustomEvent\(\s*[\'"]([^\'"]+)', text):
                if not name.startswith('sf-'):
                    self.finding(relative, f'dispatched event {name!r} is not sf- prefixed')

    def check_component_purity(self):
        """Components import only Lit or siblings, and never touch the
        APIs reserved for page infrastructure."""
        for path in self.component_paths():
            relative = path.relative_to(self.repo)
            text = strip_js_comments(path.read_text())
            for target in re.findall(r'import\s[^;]*?from\s*[\'"]([^\'"]+)[\'"]', text):
                if not ALLOWED_IMPORT_RE.match(target):
                    self.finding(relative, f'imports {target!r}; only ../lit-core.min.js or a sibling is allowed')
            for match in FORBIDDEN_API_RE.finditer(text):
                self.finding(relative, f'references {match.group(0)!r}, which components must not touch')

    def check_brand_scope(self, sf_css):
        """--sf-brand is chrome-only: .sf-header is the one place in
        sf.css allowed to use it."""
        header_re = re.compile(r'\.sf-header(?![\w-])')
        for match in re.finditer(r'var\(--sf-brand\b', sf_css):
            stack = enclosing_selectors(sf_css, match.start())
            if not any(header_re.search(selector) for selector in stack):
                self.finding('sf.css', 'var(--sf-brand) used outside a .sf-header rule')

    def check_reserved_class_names(self, sf_css):
        """No class shares a name with an sfui custom element, and
        no element shares a name with the CSS-only .sf-nav."""
        elements = set()
        for path in self.component_paths():
            elements.update(re.findall(
                r'customElements\.define\(\s*[\'"]([^\'"]+)', self.component_text(path)))
        for element in sorted(elements):
            if re.search(r'\.' + re.escape(element) + r'\b', sf_css):
                self.finding('sf.css', f'.{element} duplicates the <{element}> element name')
        if 'sf-nav' in elements:
            self.finding('components', '<sf-nav> is reserved: navigation is deliberately CSS-only (.sf-nav)')

    def check_demo_coverage(self, sf_css, demo_html):
        """Every .sf-* class sf.css defines is rendered in demo.html."""
        for name in sorted(set(re.findall(r'\.(sf-[a-zA-Z0-9-]+)', sf_css))):
            if name not in demo_html:
                self.finding('demo.html', f'.{name} is defined in sf.css but never rendered in demo.html')

    def check_vendor_list(self):
        """tools/vendor.sh distributes exactly the documented layout,
        and everything it lists exists."""
        vendored = parse_vendor_files(self.read('tools/vendor.sh'))
        documented = parse_layout_entries(self.read('docs/vendoring.md'))
        if vendored is None:
            self.finding('tools/vendor.sh', 'could not parse the files=( ... ) list')
            return
        if documented is None:
            self.finding('docs/vendoring.md', 'could not parse the Layout file list')
            return
        expected = set(vendored) | {'components/'}
        for name in sorted(set(documented) - expected):
            self.finding('tools/vendor.sh', f'{name} is in the documented layout but not vendored')
        for name in sorted(expected - set(documented)):
            self.finding('docs/vendoring.md', f'{name} is vendored but missing from the Layout list')
        for name in vendored:
            if not (self.repo / name).is_file():
                self.finding('tools/vendor.sh', f'{name} is listed for vendoring but does not exist')

    def check_dependency_pins(self):
        """Every third-party bundle docs/vendoring.md documents is
        pinned by tools/verify-vendor-deps.sh, and vice versa.

        The checksum list is a third copy of part of the vendored set,
        after tools/vendor.sh and the Layout list, so it drifts for the
        same reason those two do -- and its failure mode is silent: a
        library added to the other two but not here simply ships
        unpinned."""
        documented = parse_vendored_dependencies(self.read('docs/vendoring.md'))
        pinned = parse_pinned_files(self.read('tools/verify-vendor-deps.sh'))
        if documented is None:
            self.finding('docs/vendoring.md', 'could not parse the Vendored dependencies list')
            return
        if pinned is None:
            self.finding('tools/verify-vendor-deps.sh', 'could not parse the checksums list')
            return
        for name in sorted(set(documented) - set(pinned)):
            self.finding('tools/verify-vendor-deps.sh',
                         f'{name} is documented as vendored but has no pinned checksum')
        for name in sorted(set(pinned) - set(documented)):
            self.finding('docs/vendoring.md',
                         f'{name} has a pinned checksum but is not in the Vendored dependencies list')


def main():
    findings = Checker(REPO).run()
    for entry in findings:
        print(f'consistency-check: {entry}')
    if findings:
        print(f'consistency-check: {len(findings)} finding(s)', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
