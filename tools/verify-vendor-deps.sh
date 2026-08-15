#!/bin/bash
# Verify that the vendored dependencies match their official, cryptographically pinned checksums.

set -e

src="$(cd "$(dirname "$0")/.." && pwd)"

# File list with expected SHA-256 checksums
# Format: <checksum>  <file>
checksums="
d0bb7a23dc654534ee8be1032d0e15058837c94de05684f4061c3a436e68c294  lit-core.min.js
ac8ea1c12e33e1b0115897fc8c9a222705f056404a212bb9176373d8e8179d5f  morphdom-umd.js
"

hash_file() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | awk '{print $1}'
    else
        openssl dgst -sha256 -r "$1" | awk '{print $1}'
    fi
}

status=0
while read -r expected file; do
    [ -z "$file" ] && continue
    target="$src/$file"
    
    if [ ! -f "$target" ]; then
        echo "Error: $file is missing from the repository root" >&2
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
