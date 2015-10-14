#!/usr/bin/python
from ledmatrixbase import LEDMatrixBase
import logging

import base64, os, time, web
from PIL import Image

class LEDMatrixImage(LEDMatrixBase):
	def __init__(self, name, callback_function, rgbmatrix, imagebase64):
		LEDMatrixBase.__init__(self, name=name, callback_function=callback_function, rgbmatrix=rgbmatrix)
		self.imagebase64 = imagebase64

	def run(self):
		self.SetMatrixFromImgBase64()
		LEDMatrixBase.finalize(self)

	def SetMatrixFromImgBase64(self): #rgbmatrix, self.imagebase64, callback_func=None, stop_event=None):
		'''Sets rgbmatrix to image based on HTML inline image format'''
		ext = None
		if self.imagebase64.find('data:image/png;base64,') != -1:
			ext = 'png'
			imgdatacleanb64 = self.imagebase64.replace('data:image/png;base64,', '')
		if self.imagebase64.find('data:image/gif;base64,') != -1:
			ext = 'gif'
			imgdatacleanb64 = self.imagebase64.replace('data:image/gif;base64,', '')
		if ext == None:
			logging.info('invalid image data: ' + self.imagebase64)
			return
		if ext in ['png', 'jpg', 'jpeg']:
			logging.info('displaying ' + ext)
			imgdata = base64.decodestring(imgdatacleanb64)
			open('/tmp/matrix.temp.'+ext, 'wb').write(imgdata)
			os.system('convert /tmp/matrix.temp.' + ext + ' png32:/tmp/matrix.temp.32.png')
			image = Image.open('/tmp/matrix.temp.32.png')
			image.load()
			img = image.resize((32,32))
			# If image has an alpha channel
			if image.mode == 'RGBA':
				logging.debug('converting RGBA image')
				img = pure_pil_alpha_to_color_v2(img) #remove alpha layer
			self.rgbmatrix.SetImage(img.im.id, 0, 0)
		elif ext == 'gif':
			logging.info('displaying gif')
			imgdata = base64.decodestring(imgdatacleanb64)
			open('/tmp/matrix.temp.'+ext, 'wb').write(imgdata)
			image = Image.open('/tmp/matrix.temp.'+ext)
			frame=1
			while self.stop_event == None or not self.stop_event.is_set():
				logging.debug('frame: ' + str(frame))
				img = image.resize((32,32))
				animframe_in='/tmp/matrix.animframe%d.png' %(frame)
				animframe_out='/tmp/matrix.animframe%d.out.png' %(frame)
				img.save('/tmp/matrix.animframe%d.png' %(frame) )
				os.system('convert ' + animframe_in + ' png32:' + animframe_out)
				img = Image.open(animframe_out)
				img.load()
				self.rgbmatrix.SetImage(img.im.id, 0, 0)
				time.sleep(0.05)
				try: image.seek(image.tell() + 1)
				except:
					logging.debug('detected end at frame: ' + str(frame))
					break
				frame+=1

def alpha_to_color(image, color=(255, 255, 255)):
    """Set all fully transparent pixels of an RGBA image to the specified color.
    This is a very simple solution that might leave over some ugly edges, due
    to semi-transparent areas. You should use alpha_composite_with color instead.

    Source: http://stackoverflow.com/a/9166671/284318

    Keyword Arguments:
    image -- PIL RGBA Image object
    color -- Tuple r, g, b (default 255, 255, 255)

    """ 
    x = np.array(image)
    r, g, b, a = np.rollaxis(x, axis=-1)
    r[a == 0] = color[0]
    g[a == 0] = color[1]
    b[a == 0] = color[2] 
    x = np.dstack([r, g, b, a])
    return Image.fromarray(x, 'RGBA')

def alpha_composite(front, back):
    """Alpha composite two RGBA images.

    Source: http://stackoverflow.com/a/9166671/284318

    Keyword Arguments:
    front -- PIL RGBA Image object
    back -- PIL RGBA Image object

    """
    front = np.asarray(front)
    back = np.asarray(back)
    result = np.empty(front.shape, dtype='float')
    alpha = np.index_exp[:, :, 3:]
    rgb = np.index_exp[:, :, :3]
    falpha = front[alpha] / 255.0
    balpha = back[alpha] / 255.0
    result[alpha] = falpha + balpha * (1 - falpha)
    old_setting = np.seterr(invalid='ignore')
    result[rgb] = (front[rgb] * falpha + back[rgb] * balpha * (1 - falpha)) / result[alpha]
    np.seterr(**old_setting)
    result[alpha] *= 255
    np.clip(result, 0, 255)
    # astype('uint8') maps np.nan and np.inf to 0
    result = result.astype('uint8')
    result = Image.fromarray(result, 'RGBA')
    return result

def alpha_composite_with_color(image, color=(255, 255, 255)):
    """Alpha composite an RGBA image with a single color image of the
    specified color and the same size as the original image.

    Keyword Arguments:
    image -- PIL RGBA Image object
    color -- Tuple r, g, b (default 255, 255, 255)

    """
    back = Image.new('RGBA', size=image.size, color=color + (255,))
    return alpha_composite(image, back)

def pure_pil_alpha_to_color_v1(image, color=(255, 255, 255)):
    """Alpha composite an RGBA Image with a specified color.

    NOTE: This version is much slower than the
    alpha_composite_with_color solution. Use it only if
    numpy is not available.

    Source: http://stackoverflow.com/a/9168169/284318

    Keyword Arguments:
    image -- PIL RGBA Image object
    color -- Tuple r, g, b (default 255, 255, 255)

    """ 
    def blend_value(back, front, a):
        return (front * a + back * (255 - a)) / 255

    def blend_rgba(back, front):
        result = [blend_value(back[i], front[i], front[3]) for i in (0, 1, 2)]
        return tuple(result + [255])

    im = image.copy()  # don't edit the reference directly
    p = im.load()  # load pixel array
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            p[x, y] = blend_rgba(color + (255,), p[x, y])

    return im

def pure_pil_alpha_to_color_v2(image, color=(255, 255, 255)):
    """Alpha composite an RGBA Image with a specified color.

    Simpler, faster version than the solutions above.

    Source: http://stackoverflow.com/a/9459208/284318

    Keyword Arguments:
    image -- PIL RGBA Image object
    color -- Tuple r, g, b (default 255, 255, 255)

    """
    image.load()  # needed for split()
    background = Image.new('RGB', image.size, color)
    background.paste(image, mask=image.split()[3])  # 3 is the alpha channel
    return background
