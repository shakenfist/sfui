# Auditing for consistency

The point of the rules in [design-tokens.md](design-tokens.md),
[page-styles.md](page-styles.md) and
[components.md](components.md) is that they are mechanically
checkable. `tools/consistency-check.py` mechanises the checks
below: it runs as a pre-commit hook and in CI, and exits non-zero
with a finding per violated rule. The grep recipes are kept here
because they are the specification the checker implements, and
because a consumer auditing a host page by hand needs them (the
checker only covers this repository's own files).

An audit (by the checker, by hand, or by an agent) should
confirm:

- No hex colors outside `tokens.css`, except `var()` fallbacks
  whose values match `tokens.css` exactly:
  `grep -rn '#[0-9a-f]\{6\}' components/ sf.css` and compare.
  `sf.css` carries no fallbacks, so its share of that grep is
  zero matches.
- No `var(--` references to tokens that `tokens.css` or `sf.css`
  does not define (a typo'd token silently falls back).
- Every custom element and every dispatched event name starts with
  `sf-`: `grep -rn 'customElements.define\|CustomEvent' components/`.
- No component imports anything but `../lit-core.min.js` or a
  sibling component, and none references `fetch`, `location`,
  `history`, `localStorage` or host-page element ids.
- Host pages set component state only through documented
  properties, and react only to documented events.
- Every token is defined in both palettes: the custom property
  names in the `:root` block of `tokens.css` and in its
  `[data-theme="light"]` block are identical sets.
- No `rgba()` or hex color literals in `sf.css` or in host pages
  either -- translucent tints are `color-mix()` on tokens:
  `grep -n 'rgba(\|#[0-9a-f]\{6\}' sf.css <page>` should return
  nothing at all for `sf.css`, and for a page only `var()`
  fallbacks whose values match the dark defaults.
- `--sf-brand` appears only in page chrome (headers, logo
  lockups), never on content-area elements whose color conveys
  state. `sf.css`'s `.sf-header` is chrome by definition and is
  the one place in the stylesheet the token appears.
- Every `.sf-*` class `sf.css` defines is rendered somewhere in
  `demo.html`: an unrendered primitive is one nobody has looked
  at.
- Every consumer's `.sfui-commit` names the head of canonical
  `develop`, not merely an ancestor of it:
  `git rev-parse develop` here against the file there. This is
  the one audit rule a byte-for-byte correct copy can still fail
  (see [vendoring.md](vendoring.md)). This rule is checked by
  the fleet-wide `sfui-vendor` audit in shakenfist/development,
  not by the local checker.

## Testing

The static checker is half the safety net; the other half is the
test suite in `tests/`, which drives the real files in a real
Chromium via Playwright: `sf-theme.js` cookie and stamping
behavior, both components' rendering, keyboard handling and
events, and `demo.html` loading console-error-free in both
themes. `tools/vendor.sh` itself is tested round-trip, including
its `--check` drift detection. See
[testing.md](testing.md) for how to run everything locally.
