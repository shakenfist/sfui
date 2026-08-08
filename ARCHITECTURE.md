# Architecture

sfui is a deliberately small design system: CSS design tokens, a
theme boot script, a brand asset, and Lit web components, shipped
as plain files with no build step. README.md documents the system
itself (tokens, theming, page infrastructure, the component
contract, and the consistency audit); this file only describes the
repository around it.

## Repository layout

The repository root *is* the distributable: `tokens.css`,
`sf-theme.js`, `shakenfist-logo.svg`, `lit-core.min.js`,
`components/`, and README.md are what consumers vendor. Two
directories are repository-only:

- `tools/` -- `vendor.sh`, which copies the distributable set into
  a consumer's static assets, stamps `.sfui-commit` with the source
  commit, and offers a `--check` drift mode.
- `docs/plans/` -- plan documents, starting with the spin-out plan.

## Distribution model

Consumers vendor a copy rather than depending on a package: the
files are served from each consumer's own static assets, so a
consumer needs no JavaScript toolchain and no network dependency at
build or run time. `.sfui-commit` in each vendored copy records
provenance, and a consistency audit (in shakenfist/development)
catches vendored copies that were edited in place or have fallen
behind. The first consumer is private-ci's conductor dashboard;
kerbside's admin UI is the expected second.
