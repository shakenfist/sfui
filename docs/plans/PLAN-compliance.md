# sfui: fleet compliance, linting, and tests

## Context

sfui is the new canonical design-system repo (plain CSS/JS, no build step, no
npm — consumers vendor files via `tools/vendor.sh`). It currently has no
`.github/` directory at all and is not in shakenfist/development's consistency
audit scope. The goals: (1) bring sfui in line with every applicable fleet
audit, (2) add linting and unit testing so a merged PR can't silently break
downstream vendors, (3) register sfui in the audit system so drift is caught
daily.

Decisions already made with Mikal:
- **README**: split the 403-line spec into `docs/`; README becomes a short
  pitch that stays in the vendored set.
- **Lint**: Biome as a pinned, checksum-verified standalone binary (no npm).
- **Tests**: pytest + Playwright (real Chromium) plus a stdlib-Python
  consistency checker.
- **PUSH-AUDIT.md**: yes, with the two v1 shared blocks.

Facts established from `development`'s audit tooling (scripts/audit-check.py):
- Adding tracked `.py` files makes the `pyproject-usage` check **fail** unless
  `REPO_OVERRIDES['sfui'] = {'not_python': True}` is added in development.
- `readme-structure` caps README at 150 lines / 1200 words and requires a link
  containing `docs/`; `readme-absolute-links` requires every README link be
  scheme-qualified — so the docs link must be
  `https://github.com/shakenfist/sfui/blob/develop/docs/...`.
- `github-security` (live API) requires secret scanning + push protection
  enabled and, for a public repo, a file named exactly
  `.github/workflows/codeql-analysis.yml`.
- `ci-review-automation` requires `pr-re-review.yml`, `pr-address-comments.yml`,
  `pr-retest.yml`, and the string `review-pr-with-claude@main` in some workflow.
- `secret-scanning-ci` requires "gitleaks" (uncommented) in some workflow.
- Fleet reality is `functional-tests.yml` (plural) — the pr-retest template
  hardcodes that name; the singular name in one audit doc is the outlier.
- Workflow hygiene checks: top-level `permissions:` in every workflow, no
  GitHub-hosted runner labels, `static` label only ever paired as exactly
  `[self-hosted, static]`. Doc-only standards: `timeout-minutes` on every job,
  English-sentence display names, devpi pip cache with pypi fallback.
- The sfui-vendor audit walks trees for `.sfui-commit` files — tests must
  never write one inside the repo tree (use tmpdirs outside it).

## PR 1 — sfui (this worktree, branch `compliance`)

### 0. Plan file
Copy this plan to `docs/plans/PLAN-compliance.md` in the worktree (plans live
with the PR).

### 1. README split
- New `README.md`: pitch under 150 lines / 1200 words — what sfui is, who it's
  for, the "if you are reading this inside another repo's static assets, never
  edit in place" warning (it ships in the vendored set), vendoring quickstart,
  and absolute links (`https://github.com/shakenfist/sfui/blob/develop/docs/...`)
  into the spec docs. All links scheme-qualified.
- Move spec content (wording preserved) into:
  - `docs/design-tokens.md` (tokens + theming + palettes)
  - `docs/page-styles.md` (sf.css primitives, naming rules, knobs, demo.html)
  - `docs/components.md` (component contract, page infrastructure/sf-theme.js,
    per-component notes)
  - `docs/vendoring.md` (layout/distributable list, vendored dependencies,
    vendoring into a consumer, current consumers)
  - `docs/consistency-audit.md` (the "Auditing for consistency" rules — now
    also documenting the mechanical checker below)
- `tools/vendor.sh`: file list unchanged (README.md stays vendored; docs/ does
  not).
- Update `AGENTS.md` / `ARCHITECTURE.md`: "README.md is the primary
  specification" becomes pointers into `docs/`.

### 2. Lint tooling (npm-free)
- `tools/run-biome.sh`: downloads the pinned Biome release binary
  (version + sha256 pinned in the script, verified before execution) into a
  cache dir, runs `biome ci .`. Used by pre-commit and CI identically.
- `biome.json`: exclude `lit-core.min.js`, `morphdom-umd.js`; match existing
  style (4-space indent, single quotes); JS + CSS lint and format-check on
  `components/`, `sf-theme.js`, `tokens.css`, `sf.css`.
- `.pre-commit-config.yaml` additions: `rhysd/actionlint` hook (workflows now
  exist), a local hook running `tools/run-biome.sh`, a local hook running
  `tools/consistency-check.py`; keep shellcheck.

### 3. Consistency checker
`tools/consistency-check.py` — stdlib-only, exit non-zero with findings,
mechanising the README/"Auditing for consistency" rules:
- token sets in `tokens.css` `:root` vs `[data-theme="light"]` are identical;
- every `var(--sf-*, fallback)` in `components/` matches the dark `:root`
  value exactly (colors and radii);
- no hex/`rgba()` literals in `sf.css` or components outside matching
  fallbacks; zero in `sf.css`;
- every `var(--sf-*)` reference resolves to a definition in `tokens.css` or
  `sf.css`;
- every `customElements.define` / dispatched `CustomEvent` name is
  `sf-`-prefixed;
- components import only `../lit-core.min.js` or sibling components; no
  `fetch`, `location`, `history`, `localStorage`;
- `--sf-brand` appears in `sf.css` only in `.sf-header` rules;
- every `.sf-*` class defined in `sf.css` appears in `demo.html`;
- the `tools/vendor.sh` files list matches the documented distributable set.

### 4. Tests (`tests/`, pytest)
- `conftest.py`: fixture serving the repo root over `http.server` on an
  ephemeral port (ES modules don't load from `file://`); Playwright
  page/context fixtures.
- `test_consistency.py`: runs the checker; unit-tests its parsers against
  crafted good/bad snippets.
- `test_vendor.py`: `vendor.sh` into a tmpdir **outside the repo tree**:
  correct file set, `.sfui-commit` stamped with HEAD; `--check` passes clean,
  fails non-zero after mutating a vendored file and after adding/removing a
  component file.
- `test_theme.py` (Playwright, `emulate_media` for color scheme): no cookie →
  follows OS scheme; `sfTheme.set('light'|'dark')` sets cookie + restamps;
  `set('auto')` deletes cookie; invalid value throws; OS change restamps only
  in auto.
- `test_components.py` (Playwright, against small fixture pages in
  `tests/pages/`): sf-tabs — render, click selection, `sf-tab-selected` detail,
  no event on programmatic `selected` set, ArrowLeft/Right wrap + focus, badge
  pill/dot/severity classes, unknown severity → info; sf-theme-toggle —
  radiogroup semantics, `aria-checked`, `sf-theme-changed`, keyboard, no event
  on programmatic set; demo.html loads with zero console errors in both themes.

### 5. Workflows (`.github/workflows/`)
All: top-level `permissions:`, `timeout-minutes` on every job, English display
names, self-hosted runners only.
- `functional-tests.yml` (workflow_dispatch + pull_request → develop):
  - "Sanity checks" (`[self-hosted, vm, debian-12, s]`): venv, pip install
    pre-commit (devpi `PIP_INDEX_URL` + `PIP_EXTRA_INDEX_URL: https://pypi.org/simple/`),
    `pre-commit run --all-files`.
  - "Unit tests" (`[self-hosted, vm, debian-12, s]`): venv, pip install pytest
    playwright (same devpi env), `playwright install --with-deps chromium`,
    `pytest`.
  - `check-bot-commit` (`[self-hosted, static]`): clingwrap pattern verbatim.
  - `automated_reviewer`: per templates/ci-review-automation README —
    `uses: shakenfist/actions/.github/workflows/pr-auto-review.yml@main`,
    `needs:` the three jobs above, job-level permissions (contents: read,
    pull-requests: write, issues: write), `secrets: inherit`, no `runs-on`/
    `timeout-minutes`, gated on pull_request && not bot.
- `gitleaks.yml` (pull_request + push → develop, workflow_dispatch):
  `[self-hosted, vm, debian-13, s]`, checkout `fetch-depth: 0`, apt install
  gitleaks, `gitleaks detect --source . --redact --verbose --no-banner`.
- `codeql-analysis.yml`: from `templates/codeql/` with `languages: javascript`
  and a paths-ignore for the two vendored libraries; keep job-level
  `actions: read` / `contents: read` / `security-events: write`.
- `export-repo-config.yml`: template verbatim.
- `renovate.yml`: template with `RENOVATE_AUTODISCOVER_FILTER: shakenfist/sfui`;
  `renovate.json` from template plus `"pre-commit": {"enabled": true}`.
- `pr-re-review.yml`, `pr-address-comments.yml`, `pr-retest.yml`: templates
  verbatim; copy `tools/address-comments-with-claude.sh` from clingwrap with
  the project name updated in its prompt.

### 6. PUSH-AUDIT.md
Repo-specific runbook (pre-commit, pytest, consistency checker, demo.html
review in both themes) embedding `readme-discipline` v1 and
`comment-proportion` v1 verbatim from `development/templates/shared-blocks/`.

### 7. Docs/meta updates
`AGENTS.md` (new tooling, tests, CI, the no-npm constraint and how Biome/
Python respect it), `ARCHITECTURE.md` (tools/, tests/, workflows), and the new
`docs/` pages above.

## Repository settings (gh api, with Mikal's go-ahead at execution)
- Enable secret scanning, push protection, Dependabot security updates
  (`gh api -X PATCH repos/shakenfist/sfui` with a `security_and_analysis`
  payload).
- Enable auto-merge (`-F allow_auto_merge=true`).
- Verify `RENOVATE_TOKEN` is available to the repo (likely an org secret);
  flag to Mikal if not. delete-branch-on-merge and `develop` default are
  already correct.

## PR 2 — shakenfist/development (separate worktree)
- Add `sfui` to the matrix in `.github/workflows/consistency-audit.yml`.
- Add `sfui` to the in-scope list in `audits/README.md` (note: that list has
  drifted from the matrix — mention in the PR, fix if trivial).
- `scripts/audit-check.py`: `REPO_OVERRIDES['sfui'] = {'not_python': True}`
  with a comment (Python is incidental test tooling, nothing to package).
- Dry-run per development/AGENTS.md:
  `python3 scripts/audit-check.py --repo-path <sfui worktree> --repo-name sfui
  --github-org shakenfist` and iterate until every check is pass/N-A.

## Verification
- `pre-commit run --all-files` clean (shellcheck, actionlint, biome,
  consistency checker).
- `pytest` green locally in a venv (Playwright chromium installed).
- README: ≤150 lines, ≤1200 words, every link absolute.
- Audit dry-run from the development worktree against this tree: all checks
  pass or N/A (github-security passes once the settings PATCH lands).
- Serve `python3 -m http.server` and screenshot demo.html in both themes via
  Playwright as a final visual check.
- Commits proposed at logical boundaries (README split; lint+checker; tests;
  workflows; PUSH-AUDIT + docs) — each shown to Mikal per the no-unapproved-
  commit rule; PRs created by Mikal.

## Implementation notes
- Pin the current Biome release with its published sha256s per platform;
  Renovate bump for it is a possible follow-up (custom regex manager), as is
  tracking vendored lit/morphdom versions — out of scope here.
- actionlint's pre-commit hook builds via Go, which pre-commit provisions
  itself; verify it behaves on the debian-12 vm runner, else pin the
  `rhysd/actionlint` prebuilt-binary hook variant.
- Nothing in tests may write `.sfui-commit` under the repo tree.
