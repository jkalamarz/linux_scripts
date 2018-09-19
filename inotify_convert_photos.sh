inotifywait -mr /home/simson/BtSync/*Photo/ -e MOVED_TO | xargs -L 1 ~/bin/move_photos_to_zdjeciaoryginaly.sh
