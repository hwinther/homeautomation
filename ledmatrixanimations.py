#!/usr/bin/python
import logging, time

def CylonScan(rgbmatrix):
	xstart = 0
	xend = 32
	for r in range(0, 8):
		if r == 4:
			xstart = xstart + 8
			xend = xend - 8
		for x in range(xstart, xend):
			for y in range(0, 32):
				if r % 2 == 0: rgbmatrix.SetPixel(x, y, 255, 0, 0)
				else: rgbmatrix.SetPixel(32-x, y, 255, 0, 0)
			time.sleep(0.025)
			rgbmatrix.Clear()
	rgbmatrix.Clear()

def SplashScreen(rgbmatrix):
	for b in range(16):
		for g in range(8):
			for r in range(8):
				rgbmatrix.SetPixel(
				  (b / 4) * 8 + g,
				  (b & 3) * 8 + r,
				  (r * 0b001001001) / 2,
				  (g * 0b001001001) / 2,
				   b * 0b00010001)
	time.sleep(0.5)
	rgbmatrix.Clear()
	from PIL import Image
	image = Image.open("ledmatrix.png")
	image.load()          # Must do this before SetImage() calls
	#rgbmatrix.Fill(0x6F85FF) # Fill screen to sky color
	for n in range(32, -image.size[0], -1): # Scroll R to L
		rgbmatrix.SetImage(image.im.id, n, 0)
		time.sleep(0.015)
	rgbmatrix.Clear()
	
def ScreensaverA(rgbmatrix):
	from PIL import Image, ImageDraw
	image = Image.new("1", (32, 32)) # Can be larger than matrix if wanted!!
	draw  = ImageDraw.Draw(image)    # Declare Draw instance before prims
	# Draw some shapes into image (no immediate effect on matrix)...
	draw.rectangle((0, 0, 31, 31), fill=0, outline=1)
	draw.line((0, 0, 31, 31), fill=1)
	draw.line((0, 31, 31, 0), fill=1)
	# Then scroll image across matrix...
	for n in range(-32, 33): # Start off top-left, move off bottom-right
		rgbmatrix.Clear()
		# IMPORTANT: *MUST* pass image ID, *NOT* image object!
		rgbmatrix.SetImage(image.im.id, n, n)
		time.sleep(0.05)
