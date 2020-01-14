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

# Constants
scale_output = 4
grain = 0.7
iso = 0.7
exposure = 1.0

# Execution predicate
if len(sys.argv) < 2:
    sys.exit("USAGE: regrain.py <file_in> <file_out>");

# Arguments
ref_filename = sys.argv[1]
output_filename = sys.argv[2]

print "Loading '%s'." % (ref_filename)

image_rgb = Image.open(ref_filename)
image = image_rgb.convert("L")

width = image.size[0] * scale_output
height = image.size[1] * scale_output

aspect = height / width;

# Globals
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
context = cairo.Context(surface) 

# Functions
def time_str(secs):
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    
    return '%02d:%02d:%02d' % (hours, mins, secs)
    
# Entrypoint
context.set_operator(cairo.OPERATOR_SOURCE)
context.set_source_rgb(0.0 / 255.0, 0.0 / 255.0, 0.0 / 255.0)
context.paint()
context.set_operator(cairo.OPERATOR_ADD)

total_count = width * height
count = 0

total_count = total_count * exposure

print "Max grain size (in weightened pixels) = %f" % (grain * 2.0)
print "ISO (1.0 = perfect light absorbtion) = %f" % (iso)
print "Exposure (1.0 = sample count eq. pixels in output) = %f" % (exposure)
print "Computing %d samples." % (total_count)

start_time = time.clock()
random.seed(start_time)
salt = random.randint(0, 65535)

# Disable the cursor
sys.stdout.write("\x1b[?25l") 

emit_limit = int(float(total_count) / 10000.0)
emit_count = emit_limit

try:
    while(count < total_count):
        x = random.random() * width
        y = random.random() * height
        
        p = image_rgb.getpixel((x / scale_output, y / scale_output))
        
        radius = (random.random() + 1.0) * grain
        
        r = float(p[0]) / 255.0
        g = float(p[1]) / 255.0
        b = float(p[2]) / 255.0
        
        context.move_to(x, y)
        context.set_source_rgba(r, 0.0, 0.0, iso * random.random())
        context.arc(x, y - 0.5, radius * r, 0.0, math.pi * 2.0)
        context.fill()
        context.set_source_rgba(0.0, g, 0.0, iso * random.random())
        context.arc(x - 0.5, y + 0.5, radius * g, 0.0, math.pi * 2.0)
        context.fill()
        context.set_source_rgba(0.0, 0.0, b, iso * random.random())
        context.arc(x + 0.5, y + 0.5, radius * b, 0.0, math.pi * 2.0)
        context.fill()
        
        count = count + 1
        emit_count = emit_count + 1

        if(emit_count >= emit_limit):
            print "Regraining: %.02f%% in %s.\r       " % (((float(count) / float(total_count)) * 100.0), time_str(time.clock() - start_time)),
            sys.stdout.flush()
            emit_count = 0
finally:
    # Enable the cursor
    sys.stdout.write("\x1b[?12l\x1b[?25h")

print "Regraining: 100%% in %s.                 " % (time_str(time.clock() - start_time))
print "Writing '%s'" % output_filename

surface.write_to_png(output_filename)

print "Done."

