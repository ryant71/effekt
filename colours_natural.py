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
import array;

if len(sys.argv) < 4:
    sys.exit("USAGE: colors_natural.py <file_in> <reference_in> <file_out>");

# Arguments
input_filename = sys.argv[1]
ref_filename = sys.argv[2]
output_filename = sys.argv[3]

image_rgb = Image.open(ref_filename)
image = image_rgb.convert("L")

# Constants
scale_output = 4
width = image.size[0] * scale_output
height = image.size[1] * scale_output
r255 = 1.0 / 255.0

aspect = height / width;

x = width / 2
y = height / 2

vel_x = 0
vel_y = 0
damp = 0.1
cohesion = 0.000000005
step_size = (2.5 * scale_output) / 65536.0
line_width = (0.01 * scale_output) * 0.02
impulse_amp = (15.0 * scale_output) / 256.0
strokes_in_batch = 4000

# Globals
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
context = cairo.Context(surface) 
surf_data = array.array('B', str(surface.get_data()))

# Functions
def time_str(secs):
    hours = int(math.floor(secs / (60 * 60)))
    secs = secs - (hours * 60 * 60)
    mins = int(math.floor(secs / 60))
    secs = secs - (mins * 60)
    return '%02d:%02d:%02d' % (hours, mins, secs)
    
def clamp(val, lo, hi):
    if(val < lo):
    return lo

    if(val > hi):
    return hi;

    return val;
    
def impulse_from_ref(x, y):
    x = x * image.size[0]
    y = y * image.size[1]
    x = int(clamp(x,  1, image.size[0] - 3))
    y = int(clamp(y,  1, image.size[1] - 3))

    # Compute impulse vector from luminosity gradient (towards darker areas)
    x_imp = (image.getpixel((x-1, y)) - image.getpixel((x+1, y))) * impulse_amp
    y_imp = (image.getpixel((x, y-1)) - image.getpixel((x, y+1))) * impulse_amp

    return (x_imp, y_imp, image.getpixel((x, y)), image_rgb.getpixel((x, y)))

def impulse_from_buf(x, y):
    x = int(clamp(x,  1, width - 3))
    y = int(clamp(y,  1, height - 3))

    offset = (y * width) + x;

    # Compute impulse vector from luminosity gradient (towards darker areas)
    x_imp = (surf_data[offset-1] - surf_data[offset+1]) * impulse_amp
    y_imp = (surf_data[offset-width] - surf_data[offset+width]) * impulse_amp

    return (x_imp, y_imp)

# Entrypoint
fp = open(input_filename, "rb")

random.seed(1234) # Deterministic rand

#context.set_source_rgb(0.0 / 255.0, 0.0 / 255.0, 0.0 / 255.0)
context.set_operator(cairo.OPERATOR_SOURCE)
#context.paint()
context.move_to(x, y)
context.set_line_join(cairo.LINE_JOIN_ROUND)
context.set_line_cap(cairo.LINE_CAP_ROUND)

total_count = os.path.getsize(input_filename)

pos = 0
count = strokes_in_batch # Start with a reset on first interation to serve as initialization
switch = 0
islands = 0
start_time = time.clock();
last_width = 1.0
w = 1.0
size_offset = total_count + (total_count / 2)
width_amp = 0.0

while(pos < total_count):
    if(count < strokes_in_batch):
        b = ord(fp.read(1))

        x_dir = (lambda x: x & 1 and -1.0 or 1.0)(b)
        y_dir = (lambda x: x & 2 and -1.0 or 1.0)(b)

        xd = (width / 2) - x
        yd = (height / 2) - y

        dist = math.sqrt((xd ** 2) + (yd ** 2)) * cohesion
        b2 = (b ** 2) * step_size

        l_imp = impulse_from_ref(x / width, y / height)
        b_imp = impulse_from_buf(x, y)

        vel_x = vel_x + (x_dir * b2) + (xd * dist) + l_imp[0] - b_imp[0]
        vel_y = vel_y + (y_dir * b2) + (yd * dist) + ((l_imp[1] - b_imp[1]) * aspect)

        x = x + vel_x
        y = y + vel_y

        vel_x = vel_x * damp
        vel_y = vel_y * damp

        width_amp = float(size_offset - pos) / float(total_count)
        #w = math.sqrt((l_imp[0] ** 2) + (l_imp[1] ** 2)) * line_width * l_imp[2] * 1.6 * width_amp
        #w = (last_width * 0.9) + (math.sqrt((l_imp[0] ** 2) + (l_imp[1] ** 2)) * line_width * l_imp[2] * 4.0 * width_amp * 0.1)

        if switch == 1:
            w = math.sqrt((l_imp[0] ** 2) + (l_imp[1] ** 2)) * line_width * l_imp[2] * width_amp
        else:
            w = math.sqrt((l_imp[0] ** 2) + (l_imp[1] ** 2)) * line_width * (255 - l_imp[2]) * width_amp
        
        # last_width = w
        context.set_line_width(w)
        context.set_source_rgb(l_imp[3][0] * r255, l_imp[3][1] * r255, l_imp[3][2] * r255)
        context.line_to(x, y)
        context.stroke()
        pos = pos + 1
    else:
        count = 0
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        switch = 1-switch # Alternate strategies between islands
        print "Rendering: %.02f%% %d / %d strokes (%d islands) in %s.\r" % (((float(pos) / float(total_count)) * 100.0), pos, total_count, islands, time_str(time.clock() - start_time)),
        sys.stdout.flush()
        islands = islands + 1

    context.move_to(x, y)
    count = count + 1
    
print "Rendering: %.02f%% %d / %d strokes (%d islands) in %s." % (((float(pos) / float(total_count)) * 100.0), pos, total_count, islands, time_str(time.clock() - start_time))
print "Writing '%s'" % output_filename

surface.write_to_png(output_filename)

print "Done."


