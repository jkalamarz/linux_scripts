#!/bin/bash

cd $HOME/tmp/trojka/

sleep 13

export TZ=Poland

FOLDER=$HOME/tmp/trojka/`date +"%Y-%m-%d"`
TIME=`date +"%Y-%m-%d_%H%M"`

echo mkdir -p $FOLDER
mkdir -p $FOLDER

echo wget -O $FOLDER/$TIME.ogg http://41.dktr.pl:8000/trojka.ogg
wget -O $FOLDER/$TIME.ogg http://41.dktr.pl:8000/trojka.ogg &

PID=$!
sleep 1800

TITLE=`curl -s http://player.polskieradio.pl/-3 | grep 'program-title' | sed -E 's/.*>(.*)<.*/\1/' | php -R 'echo html_entity_decode($argn), "\n";' | tr ' /' '__'`

echo
echo "$TITLE"

sleep 1800

kill $PID

echo ln -s ../subdir.php '"'$FOLDER/index.php'"'
[ -f "$FOLDER/index.php" ] || ln -s ../subdir.php "$FOLDER/index.php"


echo ffmpeg '-i' $FOLDER/$TIME.ogg -b:a 192k '"'$FOLDER/${TIME}_$TITLE.mp3'"'
ffmpeg -i $FOLDER/$TIME.ogg -b:a 192k "$FOLDER/${TIME}_$TITLE.mp3"

echo rm $FOLDER/$TIME.ogg 
rm $FOLDER/$TIME.ogg 

echo id3v2 '-a' '"'Trójka'"' '-t' '"'$TITLE'"' '"'$FOLDER/${TIME}_$TITLE.mp3'"'
id3v2 -a "Trójka" -t "$TITLE" "$FOLDER/${TIME}_$TITLE.mp3"

echo python feed.py 3
python feed.py 3

WEEKOLD=`date +"%Y-%m-%d" --date '8 days ago'`
echo rm -r $HOME/public_html/trojka/$WEEKOLD
[ -d $HOME/public_html/trojka/$WEEKOLD ] && rm -r $HOME/public_html/trojka/$WEEKOLD

