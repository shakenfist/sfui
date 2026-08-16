#!/bin/bash

# Detect modification of the vendored dependencies.
#
#     tools/verify-vendor-deps.sh [repository-root]
#
# Each bundle is pinned by the SHA-256 of the file as committed here,
# which is the upstream release with a local provenance header
# prepended (see docs/vendoring.md). That digest exists nowhere
# upstream, so what this catches is a vendored file drifting from the
# one that was reviewed -- not a compromised upstream release.
#
# The upstream digest and the header length are recorded beside each
# pin so a bump can be re-derived rather than taken on trust: strip
# the header, confirm the payload matches the recorded upstream
# SHA-256, and only then update the committed digest. For example
#
#     tail -n +7 lit-core.min.js | sha256sum
#
# must print the upstream hash recorded for lit-core.min.js.
#
# The repository root defaults to this script's parent, and is
# overridable so the tests can point it at a fixture tree.

set -e

src="${1:-$(cd "$(dirname "$0")/.." && pwd)}"

# Format: <sha256 of the committed file>  <file>
#
# lit-core.min.js  Lit 3.3.1, 6-line provenance header, from
#     https://cdn.jsdelivr.net/gh/lit/dist@3.3.1/core/lit-core.min.js
#     upstream sha256
#     a511976d328c8565dd9afb7ced1bbece82b2b40078c6e2fa69967aefade265f5
# morphdom-umd.js  morphdom 2.7.7, 8-line provenance header, from
#     https://unpkg.com/morphdom@2.7.7/dist/morphdom-umd.js
#     upstream sha256
#     82e24e1562f4f3ce29de4a2e1a71013b1c63aa9c93ee3a0cf1f4576908a12fdb
checksums="
d0bb7a23dc654534ee8be1032d0e15058837c94de05684f4061c3a436e68c294  lit-core.min.js
ac8ea1c12e33e1b0115897fc8c9a222705f056404a212bb9176373d8e8179d5f  morphdom-umd.js
"

hash_file() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | awk '{print $1}'
    elif command -v openssl >/dev/null 2>&1; then
        openssl dgst -sha256 -r "$1" | awk '{print $1}'
    else
        echo "Error: no sha256sum, shasum or openssl available" >&2
        exit 1
    fi
}

status=0
while read -r expected file; do
    [ -z "$file" ] && continue
    target="$src/$file"

    if [ ! -f "$target" ]; then
        echo "Error: $file is missing from $src" >&2
        status=1
        continue
    fi

    actual="$(hash_file "$target")"
    if [ "$actual" != "$expected" ]; then
        echo "CRITICAL: SHA-256 mismatch for $file" >&2
        echo "  Expected: $expected" >&2
        echo "  Actual:   $actual" >&2
        status=1
    else
        echo "OK: $file verified successfully"
    fi
done <<< "$checksums"

exit "$status"
