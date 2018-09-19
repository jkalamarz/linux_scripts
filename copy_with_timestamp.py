#!/usr/bin/env python3

import time
import datetime
import sys
import time
import logging
import re
import os
import shutil
import traceback
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

SOURCE_FOLDER = '/home/zup/Dropbox'
DESTINATION_FOLDER = '/home/zup/history'
IGNORED = [r'~', r'/\.[^/]*$', r'/\.[^/]*/', r'!sync$', r'\$\$\$$', r'\$', r'.bak$', r'.tmp$']
FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
logging.basicConfig(level=logging.INFO, format=FORMAT)

class DocumentFolderWatcher(FileSystemEventHandler):
    def __init__(self, src, dst):
        super(DocumentFolderWatcher, self).__init__()
        self.src = src
        self.dst = dst
        self.queue = []

    def isIgnored(self, path):
        for ign in IGNORED:
            if re.search(ign, path.lower()):
                logging.debug("Ignored: %s by pattern: %s", path, ign)
                return True
        return False

    def convert(self, path, infix=None):
        basename = os.path.basename(path)
        new_path = path.replace(self.src, self.dst, 1)
        fileName, fileExtension = os.path.splitext(basename)
        middle_name = infix or datetime.datetime.fromtimestamp(os.stat(path).st_mtime).strftime('%Y-%m-%d_%H:%M:%S')
        return '%s/%s.%s%s' % (new_path, fileName, middle_name, fileExtension)

    def add_to_queue(self, src_path, may_be_duplicate=True):
        if self.isIgnored(src_path):
            return
        if may_be_duplicate:
            for e in self.queue:
                if e['src_path'] == src_path:
                    self.queue.remove(e)
                    logging.debug('add_to_queue: File already added, replace: %s', e)
                    break
        elem = {'src_path': src_path, 'timestamp': time.time()}
        logging.debug('add_to_queue: Added: %s', elem)
        self.queue.append(elem)

    def check_queue(self):
        while self.queue and self.queue[0]['timestamp'] < time.time() - 5:
            if (len(self.queue) % 1000 == 0):
                logging.info("Queue left: %s entries", len(self.queue))
            elem = self.queue.pop(0)
            try:
                elem['dst_path'] = self.convert(elem['src_path']) if os.path.exists(elem['src_path']) else None
                elem['latest_path'] = self.convert(elem['src_path'], 'latest')
                elem['deleted_path'] = self.convert(elem['src_path'], 'deleted.%s' % datetime.datetime.fromtimestamp(elem['timestamp']).strftime('%Y-%m-%d_%H:%M:%S'))
                logging.debug('check_queue: Processing %s', elem)

                if elem['dst_path'] and os.path.exists(elem['dst_path']):
                    logging.debug('check_queue: File exists, skipping: %s', elem['src_path'])
                    continue

                if not os.path.exists(elem['src_path']):
                    logging.info('delete: %s', elem['src_path'])
                    os.rename(elem['latest_path'], elem['deleted_path'])
                    continue

                if os.path.exists(elem['latest_path']):
                    os.unlink(elem['latest_path'])

                if not os.path.isdir(os.path.dirname(elem['dst_path'])):
                    os.makedirs(os.path.dirname(elem['dst_path']))
                shutil.copy(elem['src_path'], elem['dst_path'])
                os.link(elem['dst_path'], elem['latest_path'])
                logging.info('check_queue: Copied %s -> %s', elem['src_path'], elem['dst_path'])
            except Exception as e:
                logging.warning("check_queue: Cannot process '%s' to '%s': %s", elem.get('src_path'), elem.get('dst_path'), traceback.format_exc())

    def on_modified(self, event):
        if not event.is_directory:
            self.add_to_queue(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.add_to_queue(event.src_path)
            self.add_to_queue(event.dest_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self.add_to_queue(event.src_path)
    
if __name__ == "__main__":
    event_handler = DocumentFolderWatcher(SOURCE_FOLDER, DESTINATION_FOLDER)
    observer = Observer()
    observer.schedule(event_handler, SOURCE_FOLDER, recursive=True)
    observer.start()
    logging.info("Starting...")
    for (folder, f, files) in os.walk(SOURCE_FOLDER):
        for f in files:
            event_handler.add_to_queue(os.path.join(folder, f), False)
    logging.info("Processing queue...")
    event_handler.check_queue()
    logging.info("Idle")
    try:
        while True:
            time.sleep(1)
            event_handler.check_queue()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
