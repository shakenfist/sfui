# Plans index

This page lists every planning document in this repository, oldest
first. None of sfui's plans so far has been large enough to need
phase files, so each is a single document.

| Date | Plan | Intent | Status |
|------|------|--------|--------|
| 2026-08-08 | [Spin sfui out of private-ci](PLAN-sfui-spinout.md) | Give the design system a neutral canonical home once kerbside became its second consumer, vendored downstream with `tools/vendor.sh` and checked for drift by the `sfui-vendor` audit | Complete |
| 2026-08-13 | [Fleet compliance, linting and tests](PLAN-compliance.md) | Bring sfui in line with the fleet's consistency audits, add Biome linting, the consistency checker and pytest plus Playwright tests, and register sfui in the daily audit | Complete |
| 2026-08-14 | [sf-data-table](PLAN-data-table.md) | Add a reusable sortable table component and convert the conductor dashboard's hand-rolled tables to it | Complete |
