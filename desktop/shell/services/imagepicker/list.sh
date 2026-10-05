#!/bin/bash

# List the images in one or more directories as "<image>\t<thumbnail>" rows,
# using a cached thumbnail when one exists.
#
#   list.sh <dirs, one per line>
#
# Ported from omarchy 4.0.4 shell/plugins/image-picker/list.sh (MIT,
# Copyright (c) David Heinemeier Hansson; see ../LICENSE-omarchy). Changed:
# the cache directory, and the fallback for thumbnails keyed by file content
# (an older cache layout this cache never had) is gone.

image_dirs=${1:-}
cache_dir=${XDG_CACHE_HOME:-$HOME/.cache}/tamlinux/image-picker
index_file="$cache_dir/index.tsv"

mkdir -p "$cache_dir"

thumbnail_for() {
  local image="$1"
  local signature hash thumbnail

  signature=$(stat -Lc '%s:%Y' "$image") || return
  hash=$(awk -F '\t' -v path="$image" -v sig="$signature" '$1 == path && $2 == sig { print $3; exit }' "$index_file" 2>/dev/null)

  if [[ -z $hash ]]; then
    hash=$(printf '%s\t%s' "$image" "$signature" | md5sum | cut -d ' ' -f 1)
  fi

  thumbnail="$cache_dir/$hash.jpg"

  if [[ -f $thumbnail ]]; then
    printf '%s' "$thumbnail"
  else
    printf '%s' "$image"
  fi
}

while IFS= read -r dir; do
  [[ -n $dir && -d $dir ]] || continue
  find -L "$dir" -maxdepth 1 -type f \
    \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.gif' -o -iname '*.bmp' -o -iname '*.webp' \) \
    -print0 2>/dev/null
done <<<"$image_dirs" | sort -z | while IFS= read -r -d '' image; do
  thumbnail=$(thumbnail_for "$image")
  [[ -n $thumbnail ]] || continue
  printf '%s\t%s\n' "$image" "$thumbnail"
done
