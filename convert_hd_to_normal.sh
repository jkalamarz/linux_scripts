f="$1"
d="${f/_hd/}"
echo "$f -> $d"
ffmpeg -i "$f" -loglevel 0 -vf scale="'if(gt(a,1),640,-1)':'if(gt(a,1),-1,640)'" -c:v libx264 -preset medium -crf 32 -ac 1 -c:a aac -b:a 40k -strict -2 -f mp4 "$d"
exiftool  -overwrite_original -tagsFromFile "$f" -CreateDate -ModifyDate -TrackCreateDate -TrackModifyDate -MediaCreateDate -MediaModifyDate -Make -Model -Software -GPSAltitude -GPSLatitudeRef -GPSLongitudeRef -GPSAltitudeRef -GPSLatitude -GPSLongitude -Rotation -CreationDate "$d"
rm "$f"
