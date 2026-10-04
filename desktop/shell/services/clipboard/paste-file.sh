#!/bin/bash

# Copy a file to the clipboard as the given type, then paste it into the
# focused window.
#
#   paste-file.sh [--copy-only] <mime-type> <path>
#
# Vendored from omarchy 4.0.4 bin/omarchy-clipboard-paste-file (MIT, Copyright
# (c) David Heinemeier Hansson; see ../LICENSE-omarchy). Unchanged apart from
# this header.

copy_only=false

if [[ ${1:-} == "--copy-only" ]]; then
  copy_only=true
  shift
fi

mime=${1:-}
path=${2:-}

if [[ -z $mime || -z $path ]]; then
  echo "Usage: paste-file.sh [--copy-only] <mime-type> <path>" >&2
  exit 1
fi

[[ -r $path ]] || exit 1

wl-copy --type "$mime" < "$path"

if [[ $copy_only == "true" ]]; then
  exit
fi

sleep 0.15
wtype -M shift -k Insert -m shift 2>/dev/null || true
