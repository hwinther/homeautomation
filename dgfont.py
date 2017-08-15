#!/usr/bin/python
import logging
from datetime import datetime

letters = {
    '0': [
        [0, 1, 1, 0],
        [1, 0, 0, 1],
        [1, 0, 0, 1],
        [1, 0, 0, 1],
        [0, 1, 1, 0],
    ],
    '1': [
        [0, 0, 1, 1],
        [0, 1, 0, 1],
        [0, 0, 0, 1],
        [0, 0, 0, 1],
        [0, 0, 0, 1],
    ],
    '2': [
        [0, 1, 1, 0],
        [1, 0, 0, 1],
        [0, 0, 1, 1],
        [0, 1, 0, 0],
        [1, 1, 1, 1],
    ],
    '3': [
        [0, 1, 1, 1],
        [0, 0, 0, 1],
        [0, 1, 1, 1],
        [0, 0, 0, 1],
        [0, 1, 1, 1],
    ],
    '4': [
        [0, 0, 1, 1],
        [0, 1, 0, 1],
        [1, 0, 0, 1],
        [1, 1, 1, 1],
        [0, 0, 0, 1],
    ],
    '5': [
        [1, 1, 1, 1],
        [1, 0, 0, 0],
        [1, 1, 1, 0],
        [0, 0, 0, 1],
        [1, 1, 1, 0],
    ],
    '6': [
        [0, 1, 1, 1],
        [1, 0, 0, 0],
        [1, 1, 1, 1],
        [1, 0, 0, 1],
        [0, 1, 1, 0],
    ],
    '7': [
        [1, 1, 1, 1],
        [0, 0, 0, 1],
        [0, 1, 1, 1],
        [0, 0, 0, 1],
        [0, 0, 0, 1],
    ],
    '8': [
        [1, 1, 1, 1],
        [1, 0, 0, 1],
        [1, 1, 1, 1],
        [1, 0, 0, 1],
        [1, 1, 1, 1],
    ],
    '9': [
        [1, 1, 1, 1],
        [1, 0, 0, 1],
        [1, 1, 1, 1],
        [0, 0, 0, 1],
        [0, 0, 0, 1],
    ],
    ':': [
        [0, 1, 1, 0],
        [0, 1, 1, 0],
        [0, 0, 0, 0],
        [0, 1, 1, 0],
        [0, 1, 1, 0],
    ],

    ' ': [  # empty, sample
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ],
}


def displayLetter(matrix, letter, x_rel, y_rel, r, g, b):
    '''Display letter with RBGmatrix instance, starting at x_rel/y_rel and using colors r, g, b
    Returns new relative position that is clear off the letter'''
    # print 'displaying letter ' + letter + ' at ' + str(x_rel) + ', ' + str(y_rel)
    y = y_rel
    firstRun = True
    iteration = 0
    for rows in letters[letter]:
        x = x_rel
        for col in rows:
            # print col
            if col == 1:
                matrix.SetPixel(x, y, r, g, b)
            x += 1
        y += 1
    return x, y


def displayText(matrix, text, x_rel, y_rel, r, g, b):
    '''Display series of letters with RGBmatrix instance, starting at x_rel/y_rel and using colors r, g, b
    Returns new relative position that is clear off the text'''
    x = x_rel
    y = y_rel
    for letter in text:
        x, y = displayLetter(matrix, letter, x, y, r, g, b)
        y = y_rel  # one line
        x += 1
    return x, y_rel + 6  # last is y, calculate one line height with 1 pixel spacer


def displayCurrentTime(matrix, x_rel, y_rel, r, g, b):
    '''Displays current hour and minute with RBGmatrix instance at x_rel/y_rel and using colors r, g, b'''
    dtime = datetime.now().strftime('%H:%M')
    y = y_rel
    x, y = displayText(matrix, dtime, x_rel, y, r, g, b)

# print datetime.now(), rnd, x, y
