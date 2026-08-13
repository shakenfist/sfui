# sf-data-table: reusable sortable table component + dashboard conversion

## Context

The conductor dashboard hand-rolls seven HTML-string-rendered tables with three
near-identical local stylesheets, and its sort order is fixed server-side. The
request: extract a reusable table component into sfui with optional per-column
sorting, re-vendor sfui into private-ci, convert all seven dashboard tables, and
make the repos-activity table sortable (e.g. by bug count). This is also the
"shared table styling" future work already flagged in PLAN-sfui-theming.md.

This is inherently a **two-PR job with a pause**: sfui's vendoring rule says
consumers vendor only from merged `develop` (never a feature branch), and Mikal
creates all PRs. So: PR 1 (sfui) → Mikal opens/merges → PR 2 (private-ci).

Two constraints discovered in exploration shape the design:
- The sfui consistency checker **bans an element name that duplicates a `.sf-*`
  class**. `.sf-table` CSS exists and kerbside uses it in server-rendered Jinja,
  so it stays. The component is therefore named **`sf-data-table`** (verified:
  no `.sf-data-table` class exists).
- The vendored `lit-core.min.js` has **no directives** (no `unsafeHTML`), so
  cells cannot be HTML strings — they are structured descriptors the component
  renders itself (which also fits the "data in, events out" component contract).

## PR 1 — sfui: the component

Worktree `~/src/shakenfist/sfui-wt-data-table`, branch from `develop`. Copy this
plan into the worktree as `docs/plans/PLAN-data-table.md` (plans travel with the
PR).

### New file: `components/sf-data-table.js`

Modeled on `components/sf-tabs.js` (file-header contract prose ~62 cols; Biome:
4-space indent, lineWidth 72, single quotes, bracketSpacing false; imports only
`{css, html, LitElement, nothing}` from `../lit-core.min.js`; `customElements.
define` last line).

**Properties** (all `attribute: false`, defaults in constructor):
- `columns`: `[{label, align?: 'num', sortable?: bool, title?}]` — `num`
  right-aligns header+cells; `title` is a th tooltip.
- `rows`: array of rows; a row is an array of cells.
- `emptyText`: string; when rows is empty, render a centered dim message
  instead of the table (nothing if also empty).
- `footnote`: string; small dim text under the table when non-empty.

**Cell descriptors.** A cell is a primitive (plain text) or an object
`{sortValue?, parts?: [Part, ...]}`; an object without `parts` is a single
part. Sort key: `sortValue` if present, else the primitive, else the first
part's text/badge. Part kinds (key precedence button > ribbon > badge > text):
- Text: `{text, tone?, href?, title?, small?, block?}`. `tone` ∈ accent|green|
  amber|red|purple|pink|teal|orange|dim → `var(--sf-<tone>, <dark fallback>)`
  (`dim` → `--sf-text-dim`); all tones verified present in tokens.css. `href`
  renders `<a target="_blank" rel="noopener">` (accent, hover accent-hover;
  tone overrides). `small` → 0.8em; `block` → own line (stacked cells).
- Badge: `{badge, tone?, title?}` — outline pill (the `.size-badge` look);
  glyphs like ↓/↑ are page-composed text inside `badge`.
- Ribbon: `{ribbon: [tone, ...], title?}` — inline row of 3×8px boxes,
  `aria-hidden` (decorative sparkline; meaning is host-page policy).
- Button: `{button: {label, action, data?, disabled?, tone?}}` — small outline
  button; click dispatches the action event.

All text lands in Lit text bindings — auto-escaped, never HTML.

**Sorting.** Internal reactive state (column index + direction); `render()`
computes a sorted *view*, never mutates `rows` — so replacing `rows` every
poll tick re-applies the current sort. Header click cycles none → asc → desc →
none (third click restores the as-given "natural" order, which for the repos
table is the meaningful server order). Compare: both-numbers numeric, else
case-insensitive string; null/undefined last; stable (tie-break original
index). Sortable headers are real `<button>`s in the th (keyboard for free),
`aria-sort` on the active th, aria-hidden ▲/▼ glyph.

**Events** (bubbles+composed, fired only on user interaction):
- `sf-data-table-action`: `{detail: {action, data, rowIndex}}` (rowIndex is
  natural order; `data` is the reliable channel; never fired when disabled).
- `sf-data-table-sort`: `{detail: {column, direction: 'asc'|'desc'|null}}`.

**Shadow styling**: replicate the `.sf-table` look (uppercase dim 0.78rem th,
mono 0.88rem td, `--sf-border` row rules, accent 8% color-mix hover,
`var(--sf-table-cell-pad, 0.5rem 0.8rem)`), with a cross-reference comment
that it must stay visually in step with `sf.css` (same pattern sf-tabs uses
for `.sf-nav`). Scroll wrapper div inside the shadow root (`overflow-x: auto`,
table `min-width: max-content`). Every color fallback byte-matches the
tokens.css dark value (checker-enforced).

### Other sfui changes
- `demo.html`: module import + a new "Data table (component)" `sf-section`
  after the existing static "Workflow runs" table section (which must stay —
  checker requires every `.sf-*` class showcased). Demo exercises sortable
  mixed-type columns, num column, links, tones, badge, ribbon,
  enabled/disabled buttons, footnote. `TestDemoPage` then covers it in both
  themes for free.
- `tests/pages/data-table.html`: harness page per tabs.html conventions
  (tokens.css only, sets properties covering every part kind, records both
  events in `window.events`, `window.harnessReady = true`).
- `tests/test_components.py`: new `class TestSfDataTable` — th/row rendering,
  part kinds, num alignment, link attrs, tone → computed token color, sort
  cycle incl. return-to-natural + aria-sort + sort events, numeric vs string
  compare, sortValue precedence, nulls last, stable ties, rows-replacement
  re-applies sort, action event payload, disabled silence, emptyText,
  footnote presence/absence.
- `docs/components.md`: add the sf-data-table bullet; `docs/testing.md`:
  extend the coverage list.
- vendor.sh copies `components/` wholesale — no vendoring/tooling changes.

### PR 1 verification
`pre-commit run --all-files` (Biome + consistency checker) and `pytest tests/`
(Playwright/Chromium per docs/testing.md). Then **stop: Mikal opens the PR**
and merges to `develop`.

## PR 2 — private-ci: vendor + convert (after PR 1 merges)

Worktree `~/src/shakenfist/private-ci-wt-data-table` from `master`. Plan copy
travels here too (docs/plans/).

1. **Vendor** from the main sfui checkout at pulled `develop`:
   `tools/vendor.sh <worktree>/conductor/static/sfui` (stamps `.sfui-commit`
   to develop head — must be the merge commit on develop, satisfying the
   sfui-vendor audit). Own commit.
2. **Convert `conductor/templates/dashboard.html`** (all in this one file):
   - Load `<script type="module" src="/static/sfui/components/sf-data-table.js">`
     beside the other component imports (~line 13-15).
   - **Integration pattern (the load-bearing part)**: each renderer keeps
     building its panel HTML with a constant bare `<sf-data-table id="...">`
     inside and calls `paintPanel()` as today, then **unconditionally**
     (ignoring paintPanel's return value) assigns `columns` (module-level
     const), `rows`, `emptyText`, `footnote` on the element. For bare-element
     panels the string never changes, so paintPanel skips every tick —
     property assignment is the real update path; the string paint only
     matters for surrounding chrome (banners, category show/hide). morphdom
     preserves element identity, so internal sort state survives. Extend the
     design comment block (lines 1093–1114) with this rule.
   - **Buttons**: shadow DOM + event retargeting kill the
     `delegateClick('.cancel-btn')` pattern and the direct button mutation in
     `cancelRun`/`requestBuild`. Replace with one `sf-data-table-action`
     listener per panel container (attached once at startup), handlers using
     `event.detail` only, and data-driven optimistic state: keep the last
     `/api/state` snapshot; on click, confirm → set a pending marker
     (`pendingCancels`/`pendingBuilds` beside the existing `cancelledRuns`)
     → re-run the renderer from the snapshot (instant disabled
     "Cancelling…" button) → fetch → success promotes/clears + `refresh()`,
     failure clears + re-render + alert. Worker cards are not tables: their
     `.cancel-btn` delegate stays; share fetch logic via a thin wrapper so
     `cancelRun` keeps working for cards.
   - **Empty states**: use `emptyText` (keeps element identity; no sort-state
     loss) for message-style empties; the hide-whole-category behavior
     (reliability/sizing/costs) stays page-level.
   - **Drop `escapeHtml` on converted cell content** — Lit escapes; keeping it
     double-escapes. Keep it for still-string-rendered chrome.
   - Table-by-table mapping (formatters formatAge/formatBytes/formatCpuNs/
     workflowLabel stay in the page, producing descriptor text):
     - renderImages: Status `{text, tone}` (amber/pink/dim/green); Last build
       multi-part; Build button `{action: 'build-image', data: {name}}`.
     - renderQueue: Workflow link-or-text; Job `{tone:'dim', small}`; Avg
       runtime `{text, title}`; Cancel button `data: {repo, runId}` with
       pending/cancelled label+disabled from the maps.
     - **renderRepoActivity (the sortable one)**: all seven columns
       `sortable: true`; natural order = existing server order; zero counts
       `{text:'0', tone:'dim', sortValue: 0}`, positive counts as links with
       existing colors/tooltips and numeric sortValue (so "sort by bug
       count" works on Open Issues); footnote reworded to mention
       click-to-sort; emptyText as today.
     - renderReliability: Failure Rate = pct text part (red/amber tone) +
       ribbon part with per-run tones; sortValue = rate. Last Failure link.
     - renderSizing: stacked Workflow cell (block part); Suggested = 0–2
       badge parts (green ↓ / red ↑ / orange static); Runs num column.
     - renderCostSummary: straight transliteration, six num columns.
     - renderRecentCosts: Peak alloc `title` on the column; Disk fill red
       tone when near_full; conditional footnote = computed string or ''.
   - **Delete ~200 lines of local CSS**: `.queue-table*`, `.reliability-table*`,
     `.cost-table*`/`.cost-num`, `.cost-nearfull`, `.size-badge*`,
     `.mini-ribbon*`, `.failure-pct*`, `.table-footnote`. Keep `.empty-state`
     (used by non-table panels/banners) and `.cancel-btn` (worker cards).
3. **Docs**: AGENTS.md dashboard section gets the two-path update rule
   (paintPanel for chrome, unconditional property sets for tables, action
   listeners, shadow-DOM caveat); ARCHITECTURE.md names sf-data-table as a
   consumed component. docs/ pages if any describe the dashboard tables.

### PR 2 verification
- `pre-commit run --all-files`; existing pytest/tox (test_web.py is API-level,
  no table-markup assertions — confirmed).
- `sfui/tools/vendor.sh --check conductor/static/sfui` → drift-free.
- Eyeball: scratchpad stub server (serve dashboard.html, conductor/static/,
  canned /api/state JSON covering all seven tables incl. a near-full cost row,
  building image, queued jobs). Both themes; sort repos by Open Issues asc/
  desc/natural; verify a simulated 10 s tick preserves sort; click Build/
  Cancel (POST fails against stub — exercises optimistic + failure paths);
  zero console errors. Optionally screenshot both palettes per the
  headless-palette-screenshots memory.

## Risks
- Anyone gating property assignment on `paintPanel()`'s return value ships a
  dashboard that never updates (bare-element strings never change). Rule goes
  in the design comment + AGENTS.md.
- Composed-event retargeting: handlers must use `event.detail`, never
  `event.target` internals.
- Swapping the element out for an empty-state div would destroy sort state —
  hence `emptyText`.
- Double-escaping if any `escapeHtml` survives into descriptors.

## Checkpoints (no commits/PRs without Mikal)
1. Implement PR 1 in sfui worktree → pre-commit + pytest green → propose
   commit → **Mikal reviews/opens/merges PR 1**.
2. Vendor + implement PR 2 in private-ci worktree → checks green → propose
   commit(s) → **Mikal opens PR 2**.
