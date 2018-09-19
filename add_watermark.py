#!/usr/bin/python3

from PIL import Image, ImageDraw, ImageFont
import sys
import os
import shutil

origname=sys.argv[1]
copyname=origname + '.bak'

text='biletpowrotny.com'
fontpath='/home/simson/public_html/biletpowrotny/tmp/Marker Felt.ttf'

if not os.path.isfile(copyname):
	shutil.copy(origname, copyname)

base = Image.open(copyname).convert('RGBA')
if min(base.size)<400:
	base.save(origname, quality=85)
	sys.exit(0)

print("Process: " + origname)

txt = Image.new('RGBA', base.size, (255,255,255,0))

fnt = ImageFont.truetype(fontpath, min(base.size)//30)
d = ImageDraw.Draw(txt)
textsize = list(e//2 for e in d.textsize(text, font=fnt))
center= (base.size[0]//2, base.size[1]//2 )
yoffset = min(base.size) * 4 // 10

#d.text((center[0] - textsize[0] + 5, center[1] - yoffset - textsize[1] + 5), text, font=fnt, fill=(0,0,0,32))
d.text((center[0] - textsize[0], center[1] + yoffset - textsize[1]), text, font=fnt, fill=(255,255,255,64))
#d.text((center[0] - textsize[0] + 5, center[1] + yoffset - textsize[1] + 5), text, font=fnt, fill=(255,255,255,32))
d.text((center[0] - textsize[0], center[1] - yoffset - textsize[1]), text, font=fnt, fill=(0,0,0,64))

out = Image.alpha_composite(base, txt.rotate(45, Image.BILINEAR))

out.save(origname, quality=85)
