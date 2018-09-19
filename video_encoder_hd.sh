#!/bin/bash

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 src_file dst_folder"
    exit -1
fi

realpath() {
    [[ $1 = /* ]] && echo "$1" || echo "$PWD/${1#./}"
}

SRC_FILE=`realpath "$1"`
BASENAME=`basename "${1%.*}"`
DEST_FOLDER=`realpath "$2"`
DEST_FILE="$DEST_FOLDER/${BASENAME}_hd.mp4"

if [ -f "$DEST_FILE" ]; then
    echo "Output file exists. Exit"
    exit -1
fi

TMP_FILE=/tmp/vid-$RANDOM.mp4

echo "BASENAME=$BASENAME"
echo "SRC_FILE=$SRC_FILE"
echo "TMP_FOLDER=$TMP_FOLDER"
echo "DEST_FOLDER=$DEST_FOLDER"
echo "DEST_FILE=$DEST_FILE"

echo ffmpeg -i "$SRC_FILE" -vf scale="'if(gt(a,1),1024,-1)':'if(gt(a,1),-1,1024)'" -c:v libx264 -preset medium -crf 24 -ac 1 -c:a aac -b:a 40k -f mp4 "$DEST_FILE"
ffmpeg -i "$SRC_FILE" -vf scale="'if(gt(a,1),1024,-1)':'if(gt(a,1),-1,1024)'" -c:v libx264 -preset medium -ac 1 -c:a aac -strict -2 -b:a 40k -f mp4 "$TMP_FILE" 2> >(grep -v 'Past duration' 1>&2)

exiftool  -overwrite_original -tagsFromFile "$SRC_FILE" -CreateDate -ModifyDate -TrackCreateDate -TrackModifyDate -MediaCreateDate -MediaModifyDate -Make -Model -Software -GPSAltitude -GPSLatitudeRef -GPSLongitudeRef -GPSAltitudeRef -GPSLatitude -GPSLongitude -Rotation -CreationDate "$TMP_FILE"
touch -r "$SRC_FILE" "$TMP_FILE"
mv -v "$TMP_FILE" "$DEST_FILE"
