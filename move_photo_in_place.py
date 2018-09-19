#!/usr/bin/python3

import glob
import exiftool
import time
import os
import shutil
import subprocess

for filepath in glob.glob('[zZ]djecia*/**/File *.*', recursive=True) + glob.glob('[zZ]djecia*/**/Video *.*', recursive=True) + glob.glob('[zZ]djecia*/**/Photo *.*', recursive=True):
	print('Converting:', filepath)

	with exiftool.ExifTool() as e:
		w=e.get_metadata(filepath)

	ext=w['File:FileType'].lower()
	
	timestamp = w.get('EXIF:DateTimeOriginal') or w.get('QuickTime:MediaCreateDate') or w.get('XMP:DateCreated') or w['File:FileModifyDate']
	try:
		date=time.strptime(timestamp[0:19], '%Y:%m:%d %H:%M:%S')
	except:
		date=time.strptime(w['File:FileModifyDate'][0:19], '%Y:%m:%d %H:%M:%S')
	
	dirname=os.path.dirname(filepath)
	basename=os.path.basename(filepath)
	tmppath="/tmp/IMG_{0}.{1}".format(time.strftime('%Y%m%d_%H%m%S', date), ext)
	megapixels=w['Composite:Megapixels']

	shutil.copyfile(filepath, tmppath)
	
	if megapixels > 0.9:
		print("run", os.path.expanduser("~/bin/convert_images.py"), "-HDg", tmppath, "-o", dirname)
		subprocess.run([os.path.expanduser("~/bin/convert_images.py"), "-HDg", tmppath, "-o", dirname], stdout=None)
	else:
		print("move", tmppath, dirname)
		try:
			shutil.move(tmppath, dirname)
		except shutil.Error:
			print ("File exists")

	os.unlink(filepath)
