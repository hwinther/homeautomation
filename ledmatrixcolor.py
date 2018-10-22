#!/usr/bin/python
# coding=utf-8
import math


def EnhanceColor(normalized):
    """Softening the colors?"""
    if normalized > 0.04045:
        return math.pow((normalized + 0.055) / (1.0 + 0.055), 2.4)
    else:
        return normalized / 12.92


# EnhanceColor and RGBtoXY are based on original code from http://stackoverflow.com/a/22649803

def RGBtoXY(r, g, b):
    """Convert RGB to Philips hue XY format"""
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0

    r_final = EnhanceColor(r_norm)
    g_final = EnhanceColor(g_norm)
    b_final = EnhanceColor(b_norm)

    X = r_final * 0.649926 + g_final * 0.103455 + b_final * 0.197109
    Y = r_final * 0.234327 + g_final * 0.743075 + b_final * 0.022598
    Z = r_final * 0.000000 + g_final * 0.053077 + b_final * 1.035763

    if X + Y + Z == 0:
        return 0, 0
    else:
        x_final = X / (X + Y + Z)
        y_final = Y / (X + Y + Z)
    return x_final, y_final


def clamp(n, minn, maxn):
    """Clamp value within minimum and maximum values. E.g. 256 -> 255, -1 -> 0"""
    return max(min(maxn, n), minn)


def clampX(n, minn, maxn):
    """Flip clamped max value to min value, not sure if this is very useful"""
    x = clamp(n, minn, maxn)
    if x == maxn:
        return minn
    return x


def CreateColormap(num_steps=None, start_red=None, start_green=None, start_blue=None, end_red=None,
                   end_green=None, end_blue=None):
    """
    Creates a color map based on starting and ending points for each color in the RGB format
    Default values for most will do, they are 0-255 (max-min) and 32 steps
     (32 pixel height for screen when using this with an audio visualizer)
    """
    if num_steps is None:
        num_steps = 32

    if start_red is None:
        start_red = 0
    if start_green is None:
        start_green = 255
    if start_blue is None:
        start_blue = 0

    if end_red is None:
        end_red = 255
    if end_green is None:
        end_green = 0
    if end_blue is None:
        end_blue = 0

    # TEST set, blue to purple to orange
    # if start_red == None: start_red = 0 #0
    # if start_green == None: start_green = 0 #255
    # if start_blue == None: start_blue = 255 #0
    # if end_red == None: end_red = 255 #255
    # if end_green == None: end_green = 127 #0
    # if end_blue == None: end_blue = 0 #0

    red_diff = end_red - start_red
    green_diff = end_green - start_green
    blue_diff = end_blue - start_blue

    # Note: This is all integer division
    red_step = red_diff / num_steps
    green_step = green_diff / num_steps
    blue_step = blue_diff / num_steps

    current_red = start_red
    current_green = start_green
    current_blue = start_blue

    colormap = []
    for i in range(0, num_steps):
        current_red += red_step
        current_green += green_step
        current_blue += blue_step
        # print color
        # print i, current_red, current_green, current_blue
        # i+=1
        colormap.append([clamp(current_red, 0, 255), clamp(current_green, 0, 255), clamp(current_blue, 0, 255)])
    return colormap
