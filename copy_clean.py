#!/usr/bin/env python

import time
import datetime
import sys
import time
import logging
import re
import os
import shutil

from datetime import timedelta

from operator import attrgetter

FOLDER = '/home/zup/history'
FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
PATTERN = r'.*(\d...-..-.._..:..:..)\.?[^.]*'
logging.basicConfig(level=logging.INFO, format=FORMAT)

class DocumentCleaner:
    def __init__(self, folder):
        self.metas = [(a, c) for (a,b,c) in os.walk(FOLDER) if len(c)>1]
    
    def delete_until(self, file_timestamp):
        age = datetime.datetime.now() - file_timestamp
        if age > timedelta(days=365):
            return file_timestamp - timedelta(days=7)
        if age > timedelta(days=30):
            return file_timestamp - timedelta(days=1)
        if age > timedelta(days=7):
            return file_timestamp - timedelta(hours=1)
        if age > timedelta(days=1):
            return file_timestamp - timedelta(minutes=1)
        return file_timestamp

    def clean(self):
        for (folder, files) in self.metas:
            files_ts = []
            for f in files:
				if '.deleted.' in f:
					continue
                try:
                    date = re.match(PATTERN, f).group(1)
                    dt = datetime.datetime.strptime(date, "%Y-%m-%d_%H:%M:%S")
                    files_ts.append({'timestamp': dt, 'name': f})
                except:
                    logging.warning('Cannot parse file name: %s', f)
    
            files_ts = sorted(files_ts, key=lambda a: a['timestamp'], reverse=True)
            main_timestamp = 0
            deleted = 0
            for f in files_ts:
                if main_timestamp and f['timestamp'] > main_timestamp:
                    logging.debug("Delete %s", f['name'])
                    os.unlink(os.path.join(folder, f['name']))
                    deleted += 1
                else:
                    main_timestamp = self.delete_until(f['timestamp'])
            if deleted:
                logging.info("Deleted (%s out of %s): %s", deleted, len(files_ts), folder)
                

if __name__ == "__main__":
    handler = DocumentCleaner(FOLDER)
    handler.clean()
