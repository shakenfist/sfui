# Page styles

`sf.css` is the shared page-level stylesheet: the primitives a
Shaken Fist page is built from -- chrome (`.sf-page`,
`.sf-container`, `.sf-header`, `.sf-nav`, `.sf-footer`,
`.sf-status-line`), content (`.sf-section`, `.sf-card`,
`.sf-table`, `.sf-btn`, `.sf-badge`, `.sf-code`, `.sf-banner`,
`.sf-empty`, `.sf-footnote`), disclosures and form controls. It
exists so two projects do not write a table style twice and
then drift. It is not a framework: no grid system, no utility
vocabulary, no JavaScript, and no opinion about layout beyond a
centered container.

Everything in it lives in the `sfui` cascade layer, in the
sub-layers `sfui.reset`, `sfui.base`, `sfui.components` and
`sfui.utilities`. Unlayered rules beat layered ones whatever
their specificity, so **a page's own styles always win over
`sf.css`**, with no `!important` and no specificity contest.
That is what makes adoption incremental: a page takes one
primitive at a time and keeps local overrides for the rest.

Nothing in it applies until `<body>` carries the `sf-page` class.
The reset and the element-level base rules are gated on that
class, so linking the stylesheet changes nothing until a page
opts in -- which is what lets a consumer vendor the file long
before any of its pages is ready to use it. Without the gate,
`* { margin: 0; padding: 0 }` would flatten every page that
merely linked it.

`.sf-nav` is the site navigation strip: a flex row of anchors,
the current section marked `aria-current="page"`, styled to look
exactly like `<sf-tabs>` so the design system has one tab-strip
appearance whichever mechanism draws it. Every measurement in it
is copied from `components/sf-tabs.js`, and the two carry
comments saying they must stay in step.

Navigation is deliberately a stylesheet class and not a
component, which is worth stating because the resemblance
invites the opposite conclusion. `<sf-tabs>` is right when
selecting an item swaps a panel inside the same document, and
wrong when it means a page load: its arrow keys move the
selection, so a page that navigated on selection would load a
page per keypress -- a keyboard trap on the app's primary
navigation. `role="tab"` and `role="tablist"` promise tab panels
in this document, where a screen reader should hear site
sections as the links they are. Buttons in shadow DOM cannot be
middle-clicked, copied as a link or opened in a new tab, and do
nothing at all without JavaScript. And the tabs contract puts
complex values in properties, so a server-rendered nav would
have to be marshalled into an inline script to set `.tabs`,
where a Jinja `{% for %}` over anchors is four lines.

Buttons come in two sizes, and the default is the smaller one.
`.sf-btn` is sized for an action on a table row, which is where
almost every button in these UIs lives; `.sf-btn--lg` takes
`.sf-input`'s padding and font size, so a button that submits a
form is exactly as tall as the fields above it. Without it a
submit control reads as smaller than its own form. The two
rules carry comments saying they must stay in step. Size and
color are separate modifiers -- a form's primary control is
`.sf-btn .sf-btn--primary .sf-btn--lg`.

`.sf-btn` works on `<a>` as well as `<button>`. Reach for an
anchor when the action is a real navigation or download -- it
keeps middle-click, open-in-new-tab and copy-link working, which
a button can never do. Reach for a button when the action changes
state instead of going anywhere.

Tables exist in both mechanisms, unlike navigation. `.sf-table`
is for server-rendered markup: a Jinja loop over rows costs
nothing and works without JavaScript. `<sf-data-table>` is for a
page that builds rows from data and wants what markup alone
cannot give it -- column sorting, in-cell action buttons
reporting through events -- at the price of handing the rows to
a script. The component copies the class's measurements (its
th/td rules, and `.sf-btn`, `.sf-empty` and `.sf-footnote` for
its buttons, empty state and footnote), so the design system has
one table appearance whichever mechanism draws it; the two carry
comments saying they must stay in step. `.sf-table--striped` has
no component counterpart on purpose: the component's tables are
polled data where the row hover carries the eye, and a consumer
who wants stripes on one should say so before a variant is
invented for it. The component's sort markers go the other way
and are component-only despite needing no JavaScript at all:
they are a matched pair, a muted double arrow saying a column
can be sorted and a solid one saying it is the column the table
is sorted by, and the first half is a promise `.sf-table` cannot
keep. A solid arrow alone on a static header invites a click
that does nothing, so a server-rendered page says what it sorted
by in its caption or footnote instead. The element is named
`sf-data-table` rather than `sf-table` because of the naming
rule below.

## Naming

Naming, matching the element and event conventions:

- Component classes are single `.sf-*` classes with BEM-style
  `--` modifiers: `.sf-btn`, `.sf-btn--danger`, `.sf-btn--sm`. A
  modifier never styles anything on its own; it augments the base
  class. A component may reach its own structural children by
  element name (`.sf-table th`, `.sf-header h1`), and nothing
  else.
- A class never shares a name with an sfui custom element:
  differing from the element by only a leading dot is a
  readability trap, so `.sf-tabs` and `.sf-theme-toggle` are
  reserved and unused. Where those elements need page-level
  placement the rule is written against the element
  (`:where(.sf-page) :where(sf-tabs)`).
- The reservation runs the other way too. Because navigation is
  deliberately CSS-only, `.sf-nav` is a class and there must
  never be an `<sf-nav>` element: a component by that name would
  reintroduce every problem the class exists to avoid, and the
  same leading-dot readability trap with it.
- Element-level base rules take the `:where(.sf-page) :where(a)`
  form, i.e. zero specificity, so even a bare `a {}` in a page
  overrides them.
- No `!important`, no id selectors, and no color that is not a
  token or a `color-mix()` of one. Every tinted fill in the
  stylesheet -- badges, banners -- is the same 15% mix, so a new
  primitive has one strength to match rather than a choice to
  make.

## Non-color custom properties

The non-color custom properties live in `sf.css` rather than
`tokens.css`: that file's remit is color, and its central
invariant -- every token defined in both palettes -- is
meaningless for a font stack, so putting one there would weaken
an audit rule that currently has teeth. `sf.css` therefore
defines `--sf-font-sans`, `--sf-font-mono` and the radius scale
`--sf-radius-sm` / `--sf-radius` / `--sf-radius-lg` (4px / 6px /
8px, which the components use too), plus four documented knobs:

    --sf-container-max     .sf-container's max width; 1100px by
                           default, set it to 100% for a
                           full-bleed page
    --sf-page-pad          .sf-page's padding; the default drops
                           from 2rem to 1rem under 700px
    --sf-code-max-height   how tall .sf-code grows before it
                           scrolls
    --sf-table-cell-pad    .sf-table's th and td padding

Per-page tuning is by knob first, unlayered override second. All
of them are declared on `:root`, so a page overrides one for the
whole page or sets it on a subtree for one component.

## Opting in

A page opts in by including, in this order in `<head>`:

    <script src="/static/sfui/sf-theme.js"></script>
    <link rel="stylesheet" href="/static/sfui/tokens.css">
    <link rel="stylesheet" href="/static/sfui/sf.css">

and putting `sf-page` on `<body>`. The order matters: the theme
script stamps `data-theme` before first paint, `tokens.css`
defines the colors `sf.css` consumes, and a page's own styles
come after both.

## demo.html

`demo.html`, at the repository root, renders every class and
modifier `sf.css` defines, plus every component in
`components/`, so the stylesheet can be reviewed
in both palettes without a consumer application. It is the
canonical repository's safety net against an unreviewed
primitive: CI lints the CSS and checks mechanically that every
primitive appears in it (see
[consistency-audit.md](consistency-audit.md)), but only a human
looking at the rendered page can say a primitive looks right.
It is **not** part of the distributable set: like `docs/` and
`tools/`, consumers do not carry it. Because its components are
ES modules, it must be served over HTTP rather than opened as a
`file://` URL:

    python3 -m http.server

from the repository root.
