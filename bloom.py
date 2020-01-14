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
scale_output = 2
exposure = 10.0
min_exposure = 0.0
blur = 15.0

# Execution predicate
if len(sys.argv) < 3:
    sys.exit("USAGE: bloom.py <entrophy_file> <file_in> <file_out>");

# Arguments
ent_filename = sys.argv[1]
ref_filename = sys.argv[2]
output_filename = sys.argv[3]

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

print "Opening entrophy source '%s'." % (ent_filename)

fp = open(ent_filename, "rb")
ent_count = os.path.getsize(ent_filename)
total_count = width * height
count = 0

if ent_count < 4:
    print "The entrophy file must be at least four bytes in length."
    sys.exit()

print "Entrophy pool is %d bytes %.2f%% of req. samples." % (ent_count, (float(ent_count) / float(total_count)) * 100.0)
print "Exposure = %f" % (exposure)
print "Min. Exposure = %f" % (min_exposure)
print "Tracing %d photons." % (total_count)

start_time = time.clock()
random.seed(start_time)
salt = random.randint(0, 65535)

# Disable the cursor
sys.stdout.write("\x1b[?25l") 

emit_limit = 2000
emit_count = emit_limit
x = 0
y = 0

blur_coef = 255 / (blur + 1.0)
two_pi = math.pi * 2.0

try:
    while(count < total_count):
        e_sample = fp.read(2)
        
        if(len(e_sample) < 2):
            fp.seek(0, os.SEEK_SET)
            salt = random.randint(0, 65535)
            e_sample = fp.read(2)
        
        e_sample = map(lambda x: (ord(x) - 128) / blur_coef, e_sample)

        loc = (x / scale_output, y / scale_output)
        
        p = image_rgb.getpixel(loc)
        p_l = image.getpixel(loc)
        
        radius = (p_l / 255.0) * exposure
        
        if(radius < min_exposure):
            radius = min_exposure
        
        context.move_to(x + e_sample[0], y + e_sample[1])
        context.set_source_rgba(float(p[0]) / 255.0, float(p[1]) / 255.0, float(p[2]) / 255.0, (p_l / 128.0) / exposure)
        context.arc(x, y, radius, 0.0, two_pi)
        context.fill()
        
        count = count + 1
        emit_count = emit_count + 1
        
        if(emit_count >= emit_limit):
            print "Blooming: %.02f%% in %s.\r       " % (((float(count) / float(total_count)) * 100.0), time_str(time.clock() - start_time)),
            sys.stdout.flush()
            emit_count = 0
        
        x = x + 1
        
        if(x >= width):
            x = 0
            y = y + 1
finally:
    print " (%d,%d)/(%d,%d)/(%d,%d) - %d / %d = %f%%" % (x, y, width, height, image.size[0], image.size[1], count, total_count, (count / total_count) * 100.0)
    # Enable the cursor
    sys.stdout.write("\x1b[?12l\x1b[?25h")

print "Blooming: 100%% in %s.                 " % (time_str(time.clock() - start_time))
print "Writing '%s'" % output_filename

surface.write_to_png(output_filename)

print "Done."

