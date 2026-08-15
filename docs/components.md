# Components and page infrastructure

## Page infrastructure

Not everything in sfui is a component. `sf-theme.js` is page-level
infrastructure: a small classic (non-module) script that pages
include with a synchronous `<script>` tag in `<head>`, before the
tokens stylesheet. It reads the `sf-theme` preference cookie,
resolves the "auto" state against `prefers-color-scheme`, and
stamps a concrete `data-theme` on the document element before
first paint, so there is no flash of the wrong theme. It exposes
`window.sfTheme` (`preference`, `set()`) for pages to wire theme
controls to; the contract is documented in the file header.

The distinction matters for the component contract below:
infrastructure may touch cookies and the document element
precisely because components never do. A component that wants to
change the theme emits an event; the page calls `sfTheme.set()`.

## Component contract

Components are standard Web Components built with Lit, and every
one of them follows these rules:

1. **Data in, events out.** Input arrives through properties
   (complex values as properties, not attributes); output leaves as
   `CustomEvent`s. Components never fetch, never read or write
   `location`, `history` or storage, and never contain application
   judgement. What a badge *means*, which panel a tab *shows*, what
   is *actionable* -- that is host-page policy, computed by the
   page and handed to the component as data. This split is what
   makes a component reusable across dashboards whose semantics
   differ.
2. **Names are namespaced.** Elements are `sf-*` (one component per
   file, the file named after the element), and dispatched events
   are `sf-*` too.
3. **Shadow DOM, styled by tokens.** Components render into shadow
   DOM and take all colors from design tokens (with matching
   fallbacks, per the token rules). Corner radii work the same
   way: `var(--sf-radius, 6px)` rather than a literal, with the
   fallback matching `sf.css`'s value exactly, so a component
   follows the page's radius scale where one is loaded and looks
   unchanged where it is not. Other sizing and spacing may be
   local, but should stay visually consistent with the existing
   components.
4. **The contract is documented in the file header:** properties,
   events, and anything the host page is expected to do. A reader
   should be able to use the component without reading its
   implementation.
5. **Accessible by default.** Appropriate ARIA roles and keyboard
   operation are part of the component, not the host page's
   problem.
6. **No dependencies beyond Lit** (and other sfui components). A
   component that needs a library is a design smell to discuss
   first.

## Components

- `sf-data-table`: data table built from column and cell
  descriptors, with optional per-column sorting, in-cell action
  buttons, and tones, badges and sparkline ribbons for cell
  content. Named `sf-data-table` rather than `sf-table` because
  a class must never share a name with an sfui custom element,
  and the CSS-only `.sf-table` (see page-styles.md) serves
  server-rendered pages. See the file header in
  `components/sf-data-table.js` for the contract.
- `sf-tabs`: tab strip with notification badges. See the file
  header in `components/sf-tabs.js` for the contract.
- `sf-theme-toggle`: three-state (auto/light/dark) theme
  preference control, wired by the host page to `sf-theme.js`.
  See the file header in `components/sf-theme-toggle.js` for the
  contract.

## Content Security Policy (CSP)

sfui is fully compatible with strict Content Security Policies (CSP) and does not require dangerous directives:

1. **No `unsafe-eval` required:** Neither the Lit standard runtime nor the custom components use dynamic code evaluation (such as `eval()` or `Function()`).
2. **No `unsafe-inline` required for styles:** All component styles are compiled by Lit at load time and inserted safely via Constructable Stylesheets (supported by modern browsers) or style tags securely managed by the Lit runtime.
3. **Module scripts:** Components are shipped as standard ES modules, requiring the host page's CSP to allow `script-src` policies compatible with module loading (e.g. `self` or explicit source domains).
