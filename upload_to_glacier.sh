#!/bin/bash

echo $1
NAME=/tmp/$(basename "$1" | iconv -f UTF8 -t ascii//TRANSLIT).tar

echo $NAME

tar -cf "$NAME" "$1"

java -jar ~/bin/uploader-0.0.8-SNAPSHOT-jar-with-dependencies.jar -v zdjecia -u "$NAME"


rm "$NAME"
