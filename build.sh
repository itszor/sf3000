#!/bin/sh
# Build Star Fighter 3000 3.21 from your own copies of the game and of a
# RISC OS 3.1 !System with the Toolbox:
#     ./build.sh 'Star Fighter 3000 3.21 (2020)(Fednet + Chris Bazley).zip' uniboot.zip system.zip
# (zips, or directories holding the same files), then: cd recomp && ./sf3000
# The steps are recipe.json's "build", run by SuperSpider's tools/weave.py.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
SUPERSPIDER="${SUPERSPIDER:-$HOME/stuff/superspider}"
[ $# -gt 0 ] || { echo "usage: $0 SF3000-3.21.zip UNIBOOT.zip SYSTEM.zip (or directories)" >&2; exit 2; }
(cd "$SUPERSPIDER" && dune build)
WEAVE_RECIPES="$HERE" exec python3 -I "$SUPERSPIDER/tools/weave.py" build "$@"
