#import Image
from PIL import Image
import sys, operator

#filename='running.gif'
#filename='jy.png'
#filename='GTA.jpg'
filename = sys.argv[1]

im = Image.open(filename)
rgb_im = im.convert('RGB')

useCapLimit=False
caplimit=1
useAbsLimit=False
abslimit=0
useBGLimit=True

def findbgcolor(img):
	d={}
	for x in range(0,32):
		for y in range(0,32):
			rgb = rgb_im.getpixel((x, y))
			if not rgb in d.keys(): d[rgb]=0
			d[rgb]+=1
	max_key = max(d.iteritems(), key=operator.itemgetter(1))[0]
	print max_key, d[max_key]
	return max_key

f=open('imgcode.c', 'w')
if useBGLimit:
	bg = findbgcolor(rgb_im)
	print 'bg color:', bg
	f.write('matrix.fillScreen( matrix.Color333(%d, %d, %d) );\n\n' %(bg[0], bg[1], bg[2]) )

i=0
for x in range(0,32):
	for y in range(0,32):
		r, g, b = rgb_im.getpixel((x, y))
		if useCapLimit and (r < caplimit and g < caplimit and b < caplimit): continue
		if useAbsLimit and (r == abslimit and g == abslimit and b == abslimit): continue
		if useBGLimit and (r,g,b) == bg: continue
		f.write('matrix.drawPixel(%d, %d, matrix.Color333(%d, %d, %d) );\n' %(x, y, r, g, b) )
		i+=1
f.close()
print 'wrote %d lines' %(i)