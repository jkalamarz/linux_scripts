#!/usr/bin/python3
# -*- coding: utf-8 -*-
import arrow
import re
import subprocess
import datetime
import sys
import logging
import os
import shutil
import threading
import time
import xml.dom.minidom
import math
import argparse

WIN_MAIN_ROOT = r'.*?/zdjecia/'
MAIN_ROOT = u'/home/simson/Dropbox/zdjecia/'

MAIN_HD_FOLDER = u'/home/simson/Dropbox/zdjeciaHD/'

KML_FOLDER = u'/home/simson/Dropbox/zdjecia/0000 LocationHistory/'

WIN_ORIG_ROOT = u'.*?/zdjecia-oryginaly/'

ORIG_ROOT = u'/home/simson/zdjecia-oryginaly/'
MOVIE_REGEX = u'\.(mts|MTS|vob|VOB|mp4|MP4|avi|AVI|3gp|3GP|mov|MOV)$'
JPG_REGEX = u'\.(jpg|JPG|jpeg|JPEG|png|PNG)$'

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

kmlCache = {}
video_lock = threading.RLock()
mkdir_lock = threading.RLock()
NUM_PROC = 8

params = {}

def redate_file(file_path):
    logger.debug('Processing: %s', file_path)
    
    if not file_path.lower().endswith('.jpg'):
        return

    metadata = pyexiv2.ImageMetadata(file_path)
    metadata.read()

    if 'Exif.Image.DateTime' not in metadata.exif_keys:
        logger.warning('No datetime in file "%s"', file_path)
        return

    dt = metadata['Exif.Image.DateTime'].value
    logger.info('Set datetime of "%s" to: %s', file_path, dt.isoformat())
    
    timestamp = int(dt.strftime('%s'))
    
    os.utime(file_path, (timestamp, timestamp))


def median(lst):
        sortedLst = sorted(lst)
        lstLen = len(lst)
        index = (lstLen - 1) // 2

        if (lstLen % 2):
                return sortedLst[index]
        else:
                return (sortedLst[index] + sortedLst[index + 1])/2.0

def toSeconds(degree):
        v = abs(float(degree))
        d = math.floor(v)
        v = v % 1 * 60
        m = math.floor(v)
        v = v % 1 * 6000
        s = math.floor(v)
        return '%i/1 %i/1 %i/100' % (d, m, s)

def getGpsData(date):
    path = KML_FOLDER + date.strftime('history-%Y-%d-%m.kml')
    if kmlCache.get(path):
        return kmlCache[path]
    if not os.path.exists(path):
        return None
    xmldoc=xml.dom.minidom.parse(path)
    item=xmldoc.getElementsByTagName('gx:Track')[0]
    wholeday=[]
    for node in item.childNodes:
        try:
            if isinstance(node, xml.dom.minidom.Element):
                if node.tagName == 'when':
                    when = arrow.get(node.firstChild.data)
                elif node.tagName == 'gx:coord':
                    x, y, z = node.firstChild.data.split(' ')
                    wholeday.append({'time': when, 'x': x, 'y': y})
        except Exception as e:
            logger.error(e)

    medianed = [{'time': e['time'],
                            'x':median([float(p['x']) for p in wholeday[max(0, i-2) : min(len(wholeday), i+3)]]),
                            'y':median([float(p['y']) for p in wholeday[max(0, i-2) : min(len(wholeday), i+3)]])}
                            for i, e in enumerate(wholeday)]
    wholeday = []

    for m in medianed:
        wholeday.append({'time': m['time'],
                        'Exif.GPSInfo.GPSLongitudeRef': 'W' if m['x'] < 0 else 'E',
                        'Exif.GPSInfo.GPSLongitude': toSeconds(m['x']),
                        'Exif.GPSInfo.GPSLatitudeRef': 'S' if m['y'] < 0 else 'N',
                        'Exif.GPSInfo.GPSLatitude': toSeconds(m['y'])})
    kmlCache[path] = wholeday
    return wholeday

def findCoordinates(dtime):
    wholeday = getGpsData(dtime)
    if not wholeday:
        return None
    best = None
    for w in wholeday:
        if not best or abs(best['time'] - dtime) > abs(w['time'] - dtime):
            best = w
    return best

def update_exif(file_path, properties):
    cmd = ['exiv2']
    for prop in ['set %s %s' % (p[0], p[1]) for p in properties.items()]:
        cmd.extend(['-M', prop])
    cmd.append(file_path)
    subprocess.call(cmd)

def extract_exif(file_path, name):
    lines = subprocess.check_output(['exiv2', '-pt', '-g', name, file_path]).decode('utf-8').split('\n')
    if not lines:
        return None
    return lines[0].strip().split('  ')[-1]

def update_timestamp(orig_path, main_path):
    orig_timestamp = os.stat(orig_path).st_mtime
    os.utime(main_path, (orig_timestamp, orig_timestamp))

def geotagging(main_dir, offset):
    for file_name in sorted(os.listdir(main_dir)) if os.path.isdir(main_dir) else [main_dir]:
        if not file_name.lower().endswith('.jpg'):
            continue
        
        file_path = os.path.join(main_dir, file_name)

        dtime = extract_exif(file_path,'Exif.Image.DateTime')
        if dtime[4] == dtime[7] == ':':
            dtime = dtime.replace(':', '-', 2)
        dtime = arrow.get(dtime)
        if not dtime:
            logger.info('Plik %s nie ma Exif.Image.DateTime' % file_path)
            continue
        dtime = dtime.replace(tzinfo=arrow.now().tzinfo) + offset
        if True or not extract_exif(file_path, 'Exif.GPSInfo.GPSLatitude'):
            coords = findCoordinates(dtime)
            if coords:
                logger.info('File "%s" updated with coordinates at %s', file_path, coords['time'])
                update_exif(file_path, {k:v for k, v in coords.items() if k != 'time'})


class ConvertionThread (threading.Thread):
    def __init__(self, name, q, queueLock):
        threading.Thread.__init__(self)
        self.name = name
        self.q = q
        self.queueLock = queueLock
        self.params = params
        
    def run(self):
        logging.debug("Starting %s", self.name)
        while True:
            with self.queueLock:
                if not len(self.q):
                    break
                data = self.q.pop(0)
            logging.debug("%s processing %s", self.name, data)
            self.process_path(**data)
        logging.debug("Exiting %s", self.name)

    def delete_if_needed(self, orig_path):
        if self.params.delete:
            os.remove(orig_path)
            logging.info("Remove file: %s", orig_path)

    def process_path(self, orig_path, main_path):
        if self.params.output_dir:
            main_path = os.path.join(self.params.output_dir, os.path.basename(main_path))
        elif self.params.output_path:
            main_path = self.params.output_path
        elif main_path == orig_path:
            logger.error('-o has to be defined for non-patterned paths')
            return

        logger.debug('Processing: %s -> %s', orig_path, main_path)
        
        if os.path.isfile(main_path):
            if not self.params.replace:
                logger.info('File "%s" already exists, skipping', main_path)
                return
            logger.info('File "%s" is about to be deleted', main_path)
    
        if not os.path.isdir(os.path.dirname(main_path)):
            with mkdir_lock:
                try:
                    os.makedirs(os.path.dirname(main_path))
                except FileExistsError:
                    pass

        ext = os.path.splitext(orig_path.lower())[1]
        if ext in ('.png', '.jpg', '.jpeg') and not self.params.skip_image:
            logging.debug('convert(%s, -quality, 60, -resize, 1500x1000>, %s', orig_path, main_path)
            subprocess.call(['convert', orig_path, '-quality', '60', '-resize', '1500x1000>', main_path])
            update_timestamp(orig_path, main_path)
            if not params.skip_gps_update:
                geotagging(main_path, datetime.timedelta(minutes=(int(argv[2]) if len(argv)>2 else 0)))
            
            logger.info('File "%s" converted, old size: %iKB, new size: %iKB', orig_path, os.stat(orig_path).st_size/1024, os.stat(main_path).st_size/1024)
            self.delete_if_needed(orig_path)
        elif ext in ('.gif') and not self.params.skip_image:
            shutil.copy2(orig_path, main_path)
            self.delete_if_needed(orig_path)
            logger.info('File "%s" copied, orig size: %iKB', orig_path, os.stat(orig_path).st_size/1024)
        elif ext in ('.mts', '.vob', '.mp4', '.avi', '.3gp', '.mov') and not self.params.skip_video:
            if os.path.isfile(main_path):
                os.remove(main_path)
            with video_lock:
                logger.warning('File "%s" is video. Converting!', orig_path)
                if self.params.hd_quality:
                    logging.debug('subprocess.call(/bin/bash, /home/simson/bin/video_encoder_hd.sh, %s, %s)', orig_path, os.path.dirname(main_path))
                    subprocess.call(['/bin/bash', '/home/simson/bin/video_encoder_hd.sh', orig_path, os.path.dirname(main_path)])
                else:
                    logging.debug('subprocess.call(/bin/bash, /home/simson/bin/video_encoder.sh, %s, %s)', orig_path, os.path.dirname(main_path))
                    subprocess.call(['/bin/bash', '/home/simson/bin/video_encoder.sh', orig_path, os.path.dirname(main_path)])
#update_timestamp(orig_path, main_path)
            self.delete_if_needed(orig_path)
        else:
            logger.warning('File "%s" skipped', orig_path)


def run_convertion(file_list):
    logging.debug("Entering Main Thread, %s", params)
    threadList = ["Thread-%s" % i for i in range(0,NUM_PROC)]
    queueLock = threading.Lock()
    workQueue = []
    threads = [ConvertionThread(tName, workQueue, queueLock) for tName in threadList]
    
    # Fill the queue
    for files in file_list:
        workQueue.append(files)
    
    # Create new threads
    for t in threads:
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    logging.debug("Exiting Main Thread")

def parse_path(path):
    if re.match(WIN_MAIN_ROOT, path):
        return re.sub(WIN_MAIN_ROOT, MAIN_ROOT, path), re.sub(WIN_MAIN_ROOT, ORIG_ROOT, path)
    elif re.match(WIN_ORIG_ROOT, path):
        return re.sub(WIN_ORIG_ROOT, MAIN_ROOT, path), re.sub(WIN_ORIG_ROOT, ORIG_ROOT, path)

    return path, path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some images and videos.')
    parser.add_argument('-r', '--replace', help='replaces existing files', action='store_true')
    parser.add_argument('-v', '--verbose', help='print debig information', action='store_true')
    parser.add_argument('-g', '--skip-gps-update', help='fix GPS info in existing files', action='store_true')
    parser.add_argument('-w', '--skip-video', help='process only video files', action='store_true')
    parser.add_argument('-i', '--skip-image', help='process only image files', action='store_true')
    parser.add_argument('-H', '--hd-quality', help='save HD quality', action='store_true')
    parser.add_argument('-D', '--delete', help='delete after the process', action='store_true')
    parser.add_argument('-x', '--gpx-file', help='path to the gpx file')
    parser.add_argument('-o', '--output-dir', help='output dir')
    parser.add_argument('-O', '--output-path', help='output path')
    parser.add_argument('-m', '--gps-offset', type=int, help='enter 60 if camera at 1:00pm shows 2:00pm', default=0)
    parser.add_argument('paths', metavar='path', help='folders or files to process (eg. "zdjecia_oryginaly/2015-01-01...")', nargs='+')
    params = parser.parse_args()
    
    if params.verbose:
        logger.setLevel(logging.DEBUG)
    logger.debug('%s', params)

    file_list = []
    for path in params.paths:
        main_path, orig_path = parse_path(path)

        if os.path.isfile(orig_path):
            file_list.append({'orig_path': orig_path, 'main_path': re.sub(JPG_REGEX, '.jpg', re.sub(MOVIE_REGEX, '.mp4', main_path))})
        elif os.path.isdir(orig_path):
            for root, dirs, files in os.walk(orig_path):
                for file in files:
                    main_path, orig_path = parse_path(os.path.join(root, file))
                    file_list.append({'orig_path': orig_path, 'main_path': re.sub(JPG_REGEX, '.jpg', re.sub(MOVIE_REGEX, '.mp4', main_path))})
        else:
            logger.warning('Path "%s" doesn\'t exist. Skipping', orig_path)
            continue
        
    run_convertion(file_list)
