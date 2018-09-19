#!/usr/bin/env bash

dir=/storage/tmp/_torrent/
target=/storage/p2p/

inotifywait -m "$dir" --excludei '\.bts$' --format '%w%f' -e CREATE,MOVED_TO |
    while read file; do
        mv -v "$file" "$target"
    done
