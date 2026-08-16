# Architecture

sfui is a deliberately small design system: CSS design tokens, a
theme boot script, a brand asset, and Lit web components, shipped
as plain files with no build step. The `docs/` directory
documents the system itself (tokens, theming, page styles, the
component contract, and the consistency audit); this file only
describes the repository around it.

## Repository layout

The repository root *is* the distributable: `tokens.css`,
`sf.css`, `sf-theme.js`, `shakenfist-logo.svg`,
`lit-core.min.js`, `morphdom-umd.js`, `components/`, and
README.md are what consumers vendor. The rest is
repository-only:

- `tools/` -- `vendor.sh` (copies the distributable set into a
  consumer's static assets, stamps `.sfui-commit`, and offers a
  `--check` drift mode), `run-biome.sh` (fetches the pinned
  Biome binary and lints the JavaScript and CSS),
  `consistency-check.py` (the mechanical design-system rules),
  `verify-vendor-deps.sh` (hashes the vendored Lit and morphdom
  bundles against pinned digests, gating both the pre-commit run
  and `vendor.sh`), and `address-comments-with-claude.sh` (used
  by the PR automation).
- `tests/` -- pytest suite: Playwright browser tests for the
  components and theme script, vendor.sh round-trip tests, and
  tests for the consistency checker and the dependency pinning.
  `tests/pages/` holds the browser test harness pages. See
  `docs/testing.md`.
- `docs/` -- the specification, testing guide, and plan
  documents under `docs/plans/`.
- `demo.html` -- the primitive gallery, rendered for review in
  both palettes; not distributable.
- `.github/workflows/` -- CI (see below).
- `biome.json`, `.pre-commit-config.yaml`, `renovate.json`,
  `PUSH-AUDIT.md` -- tooling configuration and the pre-push
  runbook.

## Distribution model

Consumers vendor a copy rather than depending on a package: the
files are served from each consumer's own static assets, so a
consumer needs no JavaScript toolchain and no network dependency
at build or run time. `.sfui-commit` in each vendored copy
records provenance, and the `sfui-vendor` consistency audit (in
shakenfist/development) catches vendored copies that were edited
in place or have fallen behind. The first consumer is
private-ci's conductor dashboard; kerbside's admin UI is
converting page by page.

## Continuous integration

All CI runs on self-hosted runners, following the
shakenfist/development workflow standards:

- `functional-tests.yml` -- pre-commit (shellcheck, actionlint,
  Biome, the consistency checker) and the pytest/Playwright
  suite on every pull request, then the shared automated
  reviewer once they pass.
- `gitleaks.yml` -- repository secret scanning on pull requests
  and pushes to `develop`.
- `codeql-analysis.yml` -- GitHub CodeQL over the JavaScript,
  with the vendored Lit and morphdom bundles excluded.
- `pr-re-review.yml`, `pr-address-comments.yml`,
  `pr-retest.yml` -- the `@shakenfist-bot` developer
  automations, from the shared templates.
- `renovate.yml` / `export-repo-config.yml` -- dependency bumps
  (GitHub Actions and pre-commit hooks; Biome is pinned by hand
  in `tools/run-biome.sh`) and the daily repository
  configuration export.

The no-toolchain constraint shapes the CI choices: Biome is a
single pinned, checksum-verified binary rather than an npm
package, and the browser tests are Python driving Chromium via
Playwright rather than a node test runner.
