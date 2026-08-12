#!/bin/bash

# Run Biome (https://biomejs.dev) against this repository, fetching
# the pinned standalone binary first if it is not already cached.
#
#     tools/run-biome.sh            # lint + format check (biome ci)
#     tools/run-biome.sh <args...>  # any other biome invocation,
#                                   # e.g. tools/run-biome.sh format --write .
#
# Biome ships as a single static binary, which is why it is the
# linter here: sfui's contract is that no npm and no JavaScript
# toolchain is ever required, for consumers or for this repository's
# own development. The version and per-architecture sha256 are
# pinned below and verified before the binary is executed; bumping
# the version means updating both.

set -e

BIOME_VERSION='2.5.8'

case "$(uname -s)-$(uname -m)" in
    Linux-x86_64)
        asset='biome-linux-x64'
        sha256='17abac7ef72e7a1aaccd89892f7e2e62c9919d27473defe772be04ad78400ac2'
        ;;
    Linux-aarch64)
        asset='biome-linux-arm64'
        sha256='3f2be9f1f68dca8e0b96d2a9212b408f15dc2668203b2c42cfb78a2894cc966b'
        ;;
    *)
        echo "run-biome.sh: no pinned biome binary for $(uname -s)/$(uname -m)" >&2
        exit 1
        ;;
esac

src="$(cd "$(dirname "$0")/.." && pwd)"
cache="${XDG_CACHE_HOME:-$HOME/.cache}/sfui-biome"
binary="$cache/biome-$BIOME_VERSION-$asset"

if [ ! -x "$binary" ]; then
    mkdir -p "$cache"
    tmp="$(mktemp "$cache/download.XXXXXX")"
    trap 'rm -f "$tmp"' EXIT
    url="https://github.com/biomejs/biome/releases/download"
    url="$url/%40biomejs%2Fbiome%40$BIOME_VERSION/$asset"
    curl --silent --show-error --location --output "$tmp" "$url"
    echo "$sha256  $tmp" | sha256sum --check --quiet
    chmod +x "$tmp"
    mv "$tmp" "$binary"
    trap - EXIT
fi

cd "$src"
if [ $# -eq 0 ]; then
    exec "$binary" ci .
fi
exec "$binary" "$@"
