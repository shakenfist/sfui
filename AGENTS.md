# Guidance for AI assistants

This is the canonical home of sfui, the Shaken Fist web UI design
system. README.md is the primary specification -- the design token
rules, theming model, component contract, and consistency audit all
live there, and changes must keep code and README in agreement.

Things that trip up assistants:

- There is no build step and there must never be one. No npm, no
  bundler, no transpiler. Lit is vendored as a single file
  (`lit-core.min.js`); components import it with a relative path.
- Consumers vendor this repository's distributable files with
  `tools/vendor.sh`; the distributable file list lives in that
  script. If you add a top-level distributable file, add it to the
  list. Never edit a consumer's vendored copy -- change this
  repository and re-vendor.
- Components follow the "data in, events out" contract in
  README.md: no fetching, no location/history/storage access, no
  application judgement. Review any new component against the
  contract's six rules before proposing it.
- Every color token must be defined in both the dark (`:root`) and
  light (`:root[data-theme="light"]`) palettes in `tokens.css`, and
  `var()` fallbacks in components must match the dark values
  exactly.
- `demo.html` renders every `sf.css` primitive and both
  components. It must be served over HTTP (`python3 -m
  http.server` from the repository root) -- its components are ES
  modules and will not load from `file://`. Add a new primitive or
  component to it in the same change that introduces it: an
  unrendered primitive is one nobody has looked at.
- Run `pre-commit run --all-files` before proposing a commit
  (shellcheck on `tools/`).

The spin-out history and consumer conversion steps are in
`docs/plans/PLAN-sfui-spinout.md`.
