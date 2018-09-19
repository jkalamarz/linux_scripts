#!/bin/bash

IFS=$'\n'

touch ~/tmp/photolist.old

find ~/BtSync/JacekPhoto ~/BtSync/DorotaPhoto -iname '*.jpg' -or -iname '*.mov' -or -iname '*.png' | sort > ~/tmp/photolist.txt

sort ~/tmp/photolist.old | diff --changed-group-format='%<' --unchanged-group-format='' ~/tmp/photolist.txt - > ~/tmp/photolist.diff

echo Run for `wc -l ~/tmp/photolist.diff` files
for filepath in $(cat ~/tmp/photolist.diff)
do
	echo "Converting: $filepath"

	ext=`exiftool -FileType -s -S "$filepath" 2>/dev/null | tr '[:upper:]' '[:lower:]'`
	
	date=`exiftool -d "%Y%m%d_%H%m%S" -DateTimeOriginal -s -S "$filepath" 2>/dev/null`
	[ "$date" == "" ] && date=`exiftool -d "%Y%m%d_%H%m%S" -FileModifyDate -s -S "$filepath" 2>/dev/null`
	
	year=`echo $date | cut -c 1-4`
	dir="$HOME/BtSync/zdjecia-oryginaly/${year}/${year}-00-00 CameraUploads"
	mkdir -p "$dir"
	
	outpath="$dir/IMG_${date}.${ext}"
	
	echo "$filepath" >> ~/tmp/photolist.old
	[ -f "$outpath" ] && echo "File exists, skipping!" && continue

	echo cp -n "$filepath" "$outpath"
	cp -n "$filepath" "$outpath"
	touch -r "$filepath" "$outpath"
	
	$HOME/bin/convert_images.py -Hgv "$outpath" -o "$HOME/Dropbox/zdjeciaHD" 2>&1 | head -n 10

done

