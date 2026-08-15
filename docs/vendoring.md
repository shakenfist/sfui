# Vendoring and layout

## Layout

    README.md         The project pitch, which travels with a
                      vendored copy so a reader landing in one
                      knows what it is and not to edit it
    tokens.css        Design tokens: the shared visual vocabulary
                      (see design-tokens.md)
    sf.css            Shared page styles: the .sf-* page
                      primitives (see page-styles.md)
    sf-theme.js       Theme boot script: page infrastructure, not
                      a component (see components.md)
    shakenfist-logo.svg  Brand asset: the canonical Shaken Fist
                      logo with the viewBox tightened to the globe
                      mark (the embedded wordmark is dark teal and
                      unreadable on the dark theme; pages supply
                      their own heading text)
    lit-core.min.js   Vendored Lit runtime (see Vendored
                      dependencies below)
    morphdom-umd.js   Vendored morphdom library (see Vendored
                      dependencies below)
    components/       One file per component, named after its
                      element

The canonical repository additionally carries `tools/` (the
vendor script, the linters and the consistency checker),
`tests/`, `docs/`, and `demo.html` (see
[page-styles.md](page-styles.md)); those are not part of the
vendored set. A vendored copy instead carries `.sfui-commit`,
the source commit it was vendored from.

## Vendored dependencies

- `lit-core.min.js`: Lit 3.3.1 core bundle, BSD-3-Clause,
  unmodified from
  https://cdn.jsdelivr.net/gh/lit/dist@3.3.1/core/lit-core.min.js.
  Single-file ES module; no npm, no build step, which is a
  property to preserve -- consumers of sfui should never need a
  JavaScript toolchain to ship.
- `morphdom-umd.js`: morphdom 2.7.7, MIT, unmodified from
  https://unpkg.com/morphdom@2.7.7/dist/morphdom-umd.js. Consumers
  use it directly for poll-and-morph page refresh -- fetching a
  fresh fragment and morphing it into the live DOM so scroll
  position, focus and open disclosures survive a refresh. Like Lit,
  a single file with no npm and no build step, a property to
  preserve.

Each file carries a local provenance header comment naming its
version, upstream URL and licence, and each is pinned by SHA-256
in `tools/verify-vendor-deps.sh`. The pinned digest covers the
committed file -- header and payload -- so it matches nothing
upstream: what it detects is a vendored bundle drifting from the
one that was reviewed, not a compromised upstream release. That
script runs as a pre-commit hook, in CI, and from `vendor.sh`
before it copies anything into a consumer, which is the last
point at which the bundles are checked before they are served.
The consistency checker cross-checks the pinned list against the
list above, so a third library cannot be vendored and documented
while silently shipping unpinned.

## Updating a vendored dependency

The pinned digest has to move in lockstep with the file, so a
bump fails the hook until it does. The sequence:

1. Fetch the new release from its upstream URL, and record the
   new version and URL in the Vendored dependencies list above.
2. Re-create the provenance header at the top of the file, in
   the same shape as the one it replaces, and note how many
   lines it now occupies.
3. Confirm the payload is the upstream release untouched:
   stripping the header must leave a file whose SHA-256 is the
   upstream digest, which for a six-line header is

       tail -n +7 lit-core.min.js | sha256sum

   Record that upstream digest and the header line count in the
   comment beside the pin, so the next person can repeat this
   check rather than trust the pin.
   `tests/test_verify_vendor_deps.py` asserts that the recorded
   provenance still re-derives.
4. Update the pinned digest in `tools/verify-vendor-deps.sh` to
   the SHA-256 of the whole committed file, then run
   `pre-commit run --all-files` and `pytest tests/`.

## Vendoring into a consumer

A consumer keeps a vendored copy of the distributable set (the
Layout list above) in its static assets, conventionally at a
path ending in `sfui/`. From a checkout of this repository:

    tools/vendor.sh <consumer>/static/sfui

copies the distributable files into the target and records the
source commit in `<target>/.sfui-commit`. The same script checks
an existing copy for drift without writing anything:

    tools/vendor.sh --check <consumer>/static/sfui

which exits non-zero on any difference, so consumers can wire it
into CI or a pre-commit hook. The rule matches shared-blocks:
never edit a vendored copy directly -- fix the canonical file
here and re-vendor, otherwise the next sync silently discards
the local change.

Vendor from `develop`, and only once the change you need has
merged there -- never from the branch you made it on. The
`sfui-vendor` consistency audit compares `.sfui-commit` against
canonical `develop` and reports a copy that is behind it, so a
stamp naming a branch commit is flagged even when every vendored
file is byte for byte correct. A pull request merged as a merge
commit is the easy way to get this wrong: the commit you
vendored from is then an ancestor of `develop` rather than its
head, and the audit does not care that the merge changed no
files.

Current consumers:

- private-ci: the conductor dashboard, vendored at
  `conductor/static/sfui/`. Its header is the reference brand
  treatment (see [design-tokens.md](design-tokens.md)).
- kerbside: the admin UI, vendored at
  `kerbside/api/static/sfui/`. Converting incrementally, page by
  page, which is what the `sf-page` gate is for (see
  [page-styles.md](page-styles.md)).
