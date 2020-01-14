#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright Lasse Nielsen 2011 (CC-BY-NC, http://www.creativecommons.org/licenses/by-nc/3.0/)
# Web: http://www.effekts.dk

import cairo
import PIL
import Image
import sys
import math
import random
import os.path
import time
import array
import numpy

# Execution predicate
if len(sys.argv) < 3:
    sys.exit("USAGE: quant.py <file_in> <file_out>");

# Arguments
ref_filename = sys.argv[1]
output_filename = sys.argv[2]

print "Loading '%s'." % (ref_filename)

image_rgb = Image.open(ref_filename)
image = image_rgb.convert("L")

# Constants
scale_output = 4
threeshold = 0.0

width = image.size[0] * scale_output
height = image.size[1] * scale_output

aspect = height / width;

# Globals
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
context = cairo.Context(surface) 
surf_data = array.array('B', str(surface.get_data()))
img_diff = numpy.zeros(image.size[0]*image.size[1], numpy.uint8)

# Functions
def time_str(secs):
    hours = int(math.floor(secs / (60 * 60)))
    secs = secs - (hours * 60 * 60)
    mins = int(math.floor(secs / 60))
    secs = secs - (mins * 60)
    return '%02d:%02d:%02d' % (hours, mins, secs)
    
def sum_diff(x, y, w, h):
    total = 0.0
    r255 = 1.0 / 255.0
        
    print "Summing %d, %d, %d, %d" % (x, y, w, h)
    
    for iy in xrange(y * image.size[0], (y + h) * image.size[0], image.size[0]+1):
        for ix in xrange(x + iy, x + w + iy):
            total += img_diff[ix] * r255

    return total / (w * h)

    
def render(x, y, w, h):
    print "Rendering %d, %d, %d, %d" % (x, y, w, h)
    r255 = 1.0 / 255.0
    p = image_rgb.getpixel((x, y))
    context.set_source_rgb(p[0] * r255, p[1] * r255, p[2] * r255)
    context.set_line_width(w * scale_output)
    context.line_to(x * scale_output, y * scale_output)
    context.stroke()

def recurse(x, y, w, h):
    if w < 2 or h < 2:
        return
    
    print "Processing %d / %d, %d / %d, %d, %d" % (x, width, y, height, w, h)
    
    sd = sum_diff(x, y, w, h)
    
    if sd > threeshold:
        context.move_to(x * scale_output, y * scale_output)
        w2 = w >> 1
        h2 = h >> 1
        w4 = w >> 2
        h4 = h >> 2
        render(x + w4, y + h4, w2, h2)
        render(x + w2 + w4, y + h2 + h4, w2, h2)
        render(x + w4, y + h2 + h4, w2, h2)
        render(x + w2 + w4, y + h4, w2, h2)
        recurse(x, y, w2, h2)
        recurse(x + w2, y + h2, w2, h2)
        recurse(x, y + h2, w2, h2)
        recurse(x + w2, y, w2, h2)
    
def clamp(x, high): 
    if x > high: return high
    return x


# Entrypoint
context.set_operator(cairo.OPERATOR_SOURCE)
#context.set_source_rgb(0.0 / 255.0, 0.0 / 255.0, 0.0 / 255.0)
#context.paint()
context.set_line_join(cairo.LINE_JOIN_ROUND)
context.set_line_cap(cairo.LINE_CAP_ROUND)

# Precalc diff map (the right-most column and row are not computable and will be filled in with zero below)
off = 0

print "Precalculating %d bytes of difference map" % (image.size[0] * image.size[1])

for y in xrange(image.size[1]-1):
    for x in xrange(image.size[0]-1):
        val = image.getpixel((x, y))
        img_diff[off] = clamp((((abs(val - image.getpixel((x+1, y))) + abs(val - image.getpixel((x, y+1)))) >> 1) * 10), 255)
        off = off + 1
    
    print "Row %d / %d.     \r" % (y, image.size[1]-2),
    img_diff[off] = 0;
    off = off + 1

for x in xrange(image.size[0]-1):
    img_diff[off] = 0;
    off = off + 1
        
print ""
print "Rendering."

recurse(0, 0, image.size[0]-1, image.size[1]-1)
 
print ""
print "Writing '%s'" % output_filename

surface.write_to_png(output_filename)

print "Done."
