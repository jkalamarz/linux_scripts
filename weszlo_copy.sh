#!/bin/sh

export TZ=Poland

FILE=`basename "$1"`
S=`mp3info -p'%S' "$1"`
E=`/usr/bin/stat -c'%Y' "$1"`
PREFIX2=$(date +"%H%M" --date "@$E")
PREFIX=$(date +"%Y-%m-%d_%H%M" --date "@`echo $E-$S | bc`")
TARGET=$HOME/public_html/weszlo/`echo $PREFIX | cut -c 1-10`

mkdir -p "$TARGET"

echo ln -s '"'$TARGET/../subdir.php'"' '"'$TARGET/index.php'"'
[ -f "$TARGET/index.php" ] || ln -s "$TARGET/../subdir.php" "$TARGET/index.php"

if [ "$2" == "" ]; then
 echo mv -v '"'$1'"' '"'$TARGET/$PREFIX-$PREFIX2 $FILE'"'
 mv -v "$1" "$TARGET/$PREFIX-$PREFIX2 $FILE"
 touch "$TARGET/$PREFIX-$PREFIX2 $FILE"
else
 find "$TARGET" -type l -iname "*-$2*" -delete
 echo ln -s '"'$1'"' '"'$TARGET/$PREFIX-$2 $FILE'"'
 [ -f "$TARGET/$PREFIX-$2 $FILE" ] || ln -s "$1" "$TARGET/$PREFIX-$2 $FILE"
fi

find "$TARGET" -type f -iname '*.mp3' -size -1000k -delete

WEEKOLD=`date +"%Y-%m-%d" --date '8 days ago'`
echo rm -r $HOME/public_html/weszlo/$WEEKOLD
[ -d $HOME/public_html/weszlo/$WEEKOLD ] && rm -r $HOME/public_html/weszlo/$WEEKOLD

[ "" == "$2" ] || exit

LAST=`find ~/tmp/weszlo -iname '*.mp3' -mmin -1 -type f`
/bin/sh $0 "$LAST" "NOW"

cd $HOME/public_html/weszlo/
python feed.py

