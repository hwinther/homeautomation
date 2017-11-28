from django.http import Http404, HttpResponse
from django.shortcuts import render, render_to_response, redirect, get_object_or_404
from homeautomation.models import *
import math, time, datetime, urllib, urllib2, json
import numpy as np
import matplotlib
matplotlib.use("Pdf")
import matplotlib.pyplot as plt


# This is based on original code from http://stackoverflow.com/a/22649803
def EnhanceColor(normalized):
    if normalized > 0.04045:
        return math.pow((normalized + 0.055) / (1.0 + 0.055), 2.4)
    else:
        return normalized / 12.92


def RGBtoXY(r, g, b):
    rNorm = r / 255.0
    gNorm = g / 255.0
    bNorm = b / 255.0

    rFinal = EnhanceColor(rNorm)
    gFinal = EnhanceColor(gNorm)
    bFinal = EnhanceColor(bNorm)

    X = rFinal * 0.649926 + gFinal * 0.103455 + bFinal * 0.197109
    Y = rFinal * 0.234327 + gFinal * 0.743075 + bFinal * 0.022598
    Z = rFinal * 0.000000 + gFinal * 0.053077 + bFinal * 1.035763

    if X + Y + Z == 0:
        return (0, 0)
    else:
        xFinal = X / (X + Y + Z)
        yFinal = Y / (X + Y + Z)

        return (xFinal, yFinal)


def index(request):
    return render_to_response('homeautomation/index.html', {'lights': Light.objects.all()})


def test(request):
    return render_to_response('homeautomation/test.html', {})


def switch(request, lightid, state):
    light = get_object_or_404(Light, pk=lightid)
    bState = state == 'on'
    LightAction(light=light, state=bState).save()
    return HttpResponse('OK')


def color(request, lightid, colortype, x, y, z):
    light = get_object_or_404(Light, name=lightid)
    retry = 0
    while 1:
        try:
            if colortype == "hsl":
                # they come as percentage of the max, so lets calculate those resulting values
                hue = int(65280 * (int(x) / 100.0))
                sat = int(254 * (int(y) / 100.0))
                bri = int(254 * (int(z) / 100.0))
                LightAction(light=light, state=True, hue=x, saturation=y, brightness=z).save()
            elif colortype == "rgb":
                xy = RGBtoXY(int(x), int(y), int(z))
                LightAction(light=light, state=True, x=xy[0], y=xy[1]).save()
            break
        except:
            # print 'retrying',retry
            time.sleep(0.2)
            retry += 1
    return HttpResponse('OK')


def tv_remote(request, command):
    url = 'http://192.168.1.9:1925/1/input/key'
    data = json.dumps({'key': str(command)})
    # data = urllib.urlencode(cmd)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    the_page = response.read()
    return HttpResponse(the_page)


def plotdata(request):
    filepath = '/usr/wsh/plotdata/' + time.strftime('%d.%m.%y.plotdata')
    figfilepath = '/tmp/fig.output.png'

    data = open(filepath, 'r').read().split('\n')
    if '' in data:
        data.remove('')

    ts_list = []
    temp_list = []
    hum_list = []
    for x in data:
        parts = x.split('\t')
        if len(parts) == 3:
            ts, temp, hum = parts
            ts = datetime.datetime.strptime(ts, '%d.%m.%y %H:%M:%S')
            # ts = time.strptime(ts, '%H:%M:%S')
            # ts = datetime.datetime(*ts[:6])
            temp = float(temp)
            hum = float(hum)
            ts_list.append(ts)
            temp_list.append(temp)
            hum_list.append(hum)

    plt.title = 'Temperature/humidity over time'
    plt.plot(ts_list, temp_list, label='temperature')
    plt.plot(ts_list, hum_list, label='humidity')
    plt.legend(loc='upper right')
    plt.savefig(figfilepath)
    plt.close()
    response = HttpResponse(content_type="image/png")
    response.write(open(figfilepath, 'r').read())
    return response
