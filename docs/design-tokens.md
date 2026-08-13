# Design tokens and theming

`tokens.css` defines every color as a CSS custom property with an
`--sf-` prefix, together with the *meaning* of each token. Tokens
are the theming contract: pages link the stylesheet, and components
reference the tokens from inside their shadow DOM, which custom
properties pierce by design.

Rules:

- Every color in a Shaken Fist web UI comes from a token. No
  hardcoded colors in pages or components, with one exception:
  a component may repeat a token's dark default as a `var()`
  fallback (`var(--sf-red, #f87171)`) so it degrades sanely on a
  page that forgot the stylesheet. Fallbacks must match the
  `:root` (dark) values in `tokens.css` exactly.
- A page needing a translucent tint of a token (badge and banner
  fills) derives it with `color-mix(in srgb, var(--sf-*) N%,
  transparent)`, never by restating the color as an `rgba()`
  literal, so tints follow the active palette automatically.
- Choose tokens by meaning, not appearance: `--sf-red` because the
  thing is broken, never because red looks right next to the thing
  beside it. The semantics are documented in `tokens.css`.
- New tokens are added rarely and deliberately; a new color that is
  really "amber, but for my panel" is the existing token.

## Theming

sfui is two-theme: `tokens.css` defines the dark palette as the
`:root` default and a light palette under
`:root[data-theme="light"]`, behind the same semantic token
names. Every token must be defined in both palettes. The light
palette is a re-tuning, not an inversion -- the dark values are
bright pastels chosen against a near-black background, so each
light status color is a darker weight of the same hue, holding
WCAG AA contrast against the light surfaces for text-sized uses.

There are deliberately no `prefers-color-scheme` media queries in
`tokens.css`: the theme boot script (`sf-theme.js`, see
[components.md](components.md)) resolves the user's preference --
an `sf-theme` cookie holding `light` or `dark`, or absent meaning
"follow the operating system" -- and always stamps a concrete
`data-theme` on the document element before first paint. The CSS
therefore has exactly two states and no media-query palette copy
to drift.

A page opts in by including, in this order in `<head>`:

    <script src="/static/sfui/sf-theme.js"></script>
    <link rel="stylesheet" href="/static/sfui/tokens.css">

and typically offers an `<sf-theme-toggle>` wired to
`window.sfTheme` for the user to change the preference.

Branding is part of theming: `--sf-brand` (the Shaken Fist teal)
lives in the page chrome -- logo lockup, header accents -- and
never carries meaning in the content area, where the semantic
tokens own color. Subtle is the intent; the logo plus a teal
accent in the header is usually all a page needs. The reference
treatment is the conductor dashboard header: the globe mark
(`shakenfist-logo.svg`) sits beside the page heading, and the
header's bottom rule mixes the brand teal into the border color
(`color-mix(in srgb, var(--sf-brand) 45%, var(--sf-border))`).
