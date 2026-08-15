# Linting and testing

sfui's contract is that no npm and no JavaScript toolchain is
ever required -- for consumers, and for this repository's own
development. The tooling honours that: linting is a single
static binary, and the tests are Python.

## Linting

`pre-commit run --all-files` runs everything: shellcheck over
`tools/`, actionlint over the workflows, Biome over the
JavaScript and CSS, and the consistency checker. Install
pre-commit with `pip install pre-commit` and enable it with
`pre-commit install`.

Biome (https://biomejs.dev) lints and format-checks the
JavaScript and CSS. `tools/run-biome.sh` fetches the pinned,
checksum-verified standalone binary on first use (no npm), and
with no arguments runs `biome ci .` -- the check CI runs. To
apply formatting fixes:

    tools/run-biome.sh format --write .

The configuration lives in `biome.json`. The vendored
`lit-core.min.js` and `morphdom-umd.js` are excluded: upstream
files are never modified. `sf-theme.js` carries a small override
block: it deliberately uses `document.cookie` and pre-arrow
function style (it is page infrastructure that must run as a
classic script), so the rules that would rewrite that are off
for that one file.

## The consistency checker

`tools/consistency-check.py` (Python, standard library only)
mechanises the design-system rules in
[consistency-audit.md](consistency-audit.md): token parity
across the two palettes, `var()` fallbacks matching the dark
values, no color literals outside `tokens.css`, `sf-` name
prefixes, component import and API purity, `--sf-brand` staying
in page chrome, and demo.html rendering every primitive. It runs
as a pre-commit hook and in CI, and prints one line per finding.

## The test suite

The tests are pytest, with Playwright driving the real files in
a real Chromium -- ES modules do not load from `file://`, so a
fixture serves the repository root over HTTP, the same way
demo.html is viewed. To run them:

    python3 -m venv /tmp/venv-sfui
    /tmp/venv-sfui/bin/pip install pytest playwright
    /tmp/venv-sfui/bin/playwright install chromium
    /tmp/venv-sfui/bin/pytest tests/

Without Playwright installed the browser tests skip and only the
checker and vendoring tests run -- except under CI (the `CI`
environment variable is set), where a missing Playwright fails
the run outright: CI installs it explicitly, so its absence there
means the install step degraded, and skipping would report a
green run that exercised no browser contracts.

What is covered:

- `tests/test_theme.py`: the `sf-theme.js` contract -- the auto
  state following the operating system scheme, cookie semantics
  of `sfTheme.set()`, rejection of unknown preferences, live
  restamping on OS theme changes, and the documented host-page
  wiring of `<sf-theme-toggle>` to `window.sfTheme`.
- `tests/test_components.py`: the components against their file
  header contracts -- rendering, ARIA semantics, selection by
  click and arrow key (including wrap-around and focus), badge
  variants, events firing on user action and staying silent on
  programmatic property sets, and the toggle never touching
  cookies or the document element. For the data table: cell
  descriptor rendering (parts, tones, links, badges, ribbons,
  numeric alignment), the sort cycle back to natural order with
  `aria-sort` and sort events, missing keys sorting last, sort
  surviving row replacement, the hint marking a sortable header
  and the colors separating it from the applied sort, the
  declared natural order (named on first paint, reordering
  nothing, its two-state cycle, and on a column the viewer
  cannot click), and action events with disabled buttons staying
  silent. Also loads `demo.html` in both themes
  and asserts zero console errors.
- `tests/test_vendor.py`: `tools/vendor.sh` round-trip into a
  temporary directory, `.sfui-commit` stamping, and `--check`
  drift detection for edited, added and deleted files.
- `tests/test_consistency.py`: the consistency checker against a
  synthetic repository, breaking each rule in turn, plus a clean
  run against the real tree.

The browser test pages live in `tests/pages/`; they play the
host-page role from the component contract, handing components
data through properties and recording the events they emit.

CI runs all of this on every pull request (the "Functional
tests" workflow), and the automated reviewer only runs once the
tests pass.
