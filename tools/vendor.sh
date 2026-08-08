#!/bin/bash

# Vendor the sfui distributable files into a consumer directory, or
# check an existing vendored copy for drift.
#
#     tools/vendor.sh <target-directory>
#     tools/vendor.sh --check <target-directory>
#
# Run from any checkout of shakenfist/sfui (the script locates its
# own repository). The distributable set is the design system itself
# -- tokens, theme boot script, brand asset, vendored Lit, the
# components directory, and README.md -- but not this tools/
# directory or docs/. The source commit is recorded in
# <target-directory>/.sfui-commit so a drift audit can compare the
# vendored copy against exactly the commit it came from.
#
# --check diffs instead of copying and exits non-zero if the
# vendored copy does not match the current source tree, which makes
# it usable as a consumer CI step or pre-commit hook.

set -e

files=(README.md tokens.css sf-theme.js shakenfist-logo.svg lit-core.min.js)

src="$(cd "$(dirname "$0")/.." && pwd)"

check=0
if [ "$1" = "--check" ]; then
    check=1
    shift
fi

target="$1"
if [ -z "$target" ]; then
    echo "Usage: $0 [--check] <target-directory>" >&2
    exit 1
fi

if [ "$check" = "1" ]; then
    status=0
    for f in "${files[@]}"; do
        if ! diff -u "$target/$f" "$src/$f"; then
            status=1
        fi
    done
    if ! diff -ur "$target/components" "$src/components"; then
        status=1
    fi
    if [ "$status" != "0" ]; then
        echo "sfui: vendored copy in $target differs from $src" >&2
    fi
    exit "$status"
fi

if [ -n "$(git -C "$src" status --porcelain -- "${files[@]}" components)" ]; then
    echo "sfui: warning: vendoring from a dirty source tree;" \
         ".sfui-commit will not describe these contents" >&2
fi

mkdir -p "$target/components"
for f in "${files[@]}"; do
    cp "$src/$f" "$target/"
done
rsync -a --delete "$src/components/" "$target/components/"
git -C "$src" rev-parse HEAD > "$target/.sfui-commit"
echo "sfui: vendored $(cat "$target/.sfui-commit") into $target"
