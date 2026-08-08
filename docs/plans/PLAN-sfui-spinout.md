# Plan: spin sfui out of private-ci

## Context

sfui was built inside private-ci (see private-ci's
`docs/plans/PLAN-sfui-theming.md`) because the conductor dashboard
was the only Shaken Fist web UI. It was written self-contained from
the start -- no host imports, no build step -- precisely so this
move would be cheap. The trigger for spinning out is the decision
to converge kerbside's admin UI on the same design system: two
consumers means the canonical copy needs a neutral home.

The model is the shared-blocks pattern from shakenfist/development:
one canonical copy, vendored copies downstream, a consistency audit
to catch drift. Vendoring (rather than a package registry or git
submodule) preserves the no-toolchain property: a consumer serves
the files from its own static assets and needs nothing but the
files themselves.

## Steps

1. **Create shakenfist/sfui** (done): public repository,
   Apache-2.0, `develop` default branch per the org standard,
   delete-branch-on-merge enabled.

2. **Move the canonical copy here** (this commit): the
   distributable set from private-ci's `conductor/static/sfui/`
   unchanged, the README reframed from "directory that will spin
   out" to "canonical repository that is vendored", plus
   `tools/vendor.sh` (copy + `.sfui-commit` stamp, and a `--check`
   drift mode), LICENSE, pre-commit config, and this plan.

3. **Convert private-ci to a consumer**: re-vendor
   `conductor/static/sfui/` from this repository with
   `tools/vendor.sh`, which replaces the README with the canonical
   wording and adds `.sfui-commit`. Update private-ci's
   ARCHITECTURE.md/AGENTS.md to say the directory is a vendored
   copy and how to update it. No functional change: the
   distributable files are byte-identical at the moment of the
   move.

4. **Drift audit in shakenfist/development**: add an `sfui-vendor`
   consistency audit that, for each repository containing a
   `.sfui-commit` file, verifies the vendored copy matches the
   recorded canonical commit (local edits) and reports how far
   behind canonical HEAD it is (staleness). Separate change in the
   development repository.

5. **Convert kerbside**: its own plan in the kerbside repository,
   referencing private-ci's PLAN-sfui-theming.md for the theming
   decisions and this repository for the vendoring mechanics.

## Rules that keep this working

- New components and token changes land here first, then flow to
  consumers via `tools/vendor.sh`. Never edit a vendored copy.
- The distributable set is defined in one place: the `files` list
  in `tools/vendor.sh` (plus `components/`). Adding a new
  top-level file means updating that list.
- The no-toolchain property is load-bearing: no npm, no bundler,
  no build step, in this repository or any consumer.

## Future work (not this plan)

- A demo/gallery page in this repository showing each component in
  both themes, useful for development without booting a consumer.
- Component-level tests, if the component set grows enough to
  justify a harness.
