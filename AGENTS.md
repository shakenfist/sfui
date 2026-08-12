# Guidance for AI assistants

This is the canonical home of sfui, the Shaken Fist web UI design
system. The specification lives in `docs/` -- the design token
rules and theming model in `docs/design-tokens.md`, the page
styles in `docs/page-styles.md`, the component contract in
`docs/components.md`, the vendoring model in `docs/vendoring.md`,
and the audit rules in `docs/consistency-audit.md`. Changes must
keep code and docs in agreement. `README.md` is only the pitch,
and it ships in every vendored copy -- keep it short and keep its
links absolute.

Things that trip up assistants:

- There is no build step and there must never be one. No npm, no
  bundler, no transpiler -- for consumers *or* for this
  repository's own tooling. Lit is vendored as a single file
  (`lit-core.min.js`); components import it with a relative
  path. The linter is Biome precisely because it is a single
  pinned binary (`tools/run-biome.sh`), and the tests are Python
  (pytest + Playwright) for the same reason.
- Consumers vendor this repository's distributable files with
  `tools/vendor.sh`; the distributable file list lives in that
  script and must match the Layout list in `docs/vendoring.md`
  (the consistency checker cross-checks them). Never edit a
  consumer's vendored copy -- change this repository and
  re-vendor.
- Components follow the "data in, events out" contract in
  `docs/components.md`: no fetching, no location/history/storage
  access, no application judgement. Review any new component
  against the contract's six rules before proposing it.
- Every color token must be defined in both the dark (`:root`)
  and light (`:root[data-theme="light"]`) palettes in
  `tokens.css`, and `var()` fallbacks in components must match
  the dark values exactly. `tools/consistency-check.py` enforces
  this and the other mechanical rules; run it (or
  `pre-commit run --all-files`, which includes it) before
  proposing changes.
- `demo.html` renders every `sf.css` primitive and both
  components. It must be served over HTTP (`python3 -m
  http.server` from the repository root) -- its components are ES
  modules and will not load from `file://`. Add a new primitive
  or component to it in the same change that introduces it: the
  checker fails on an unrendered primitive, and only a human can
  say it looks right in both palettes.
- `sf-theme.js` carries a Biome override block in `biome.json`:
  it deliberately uses `document.cookie` and pre-arrow function
  style because it is page infrastructure running as a classic
  script. Do not "modernise" it to make the default rules happy,
  and do not extend the override to other files.
- Tests must never write a `.sfui-commit` file anywhere under
  this repository: the fleet-wide sfui-vendor audit identifies
  vendored copies by that file, and one inside the canonical
  repository would make the audit compare sfui against itself.
  `tests/test_vendor.py` uses pytest's tmp_path for exactly this
  reason.
- Run `pre-commit run --all-files` and `pytest tests/` before
  proposing a commit; `docs/testing.md` covers the setup. CI
  (`.github/workflows/functional-tests.yml`) runs the same
  checks, and the automated reviewer only runs after they pass.

The spin-out history and consumer conversion steps are in
`docs/plans/PLAN-sfui-spinout.md`; the compliance and testing
work is in `docs/plans/PLAN-compliance.md`.
