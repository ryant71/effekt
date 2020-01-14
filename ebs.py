#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Lasse Nielsen 2011 (CC-BY-NC, http://www.creativecommons.org/licenses/by-nc/3.0/)
# Web: http://www.effekts.dk

import cairo
import PIL
from PIL import Image
import sys
import math
import random
import os.path
import time
import array
from vector2 import Vector2

# Execution predicate
if len(sys.argv) < 4:
    sys.exit("USAGE: ebs.py <reference_in> <file_out> <density>");

# Arguments
ref_filename = sys.argv[1]
output_filename = sys.argv[2]
density = int(sys.argv[3])

image_rgb = Image.open(ref_filename)
image = image_rgb.convert("L")

# Constants
scale_output = 1
width = image.size[0] * scale_output
height = image.size[1] * scale_output
r255 = 1.0 / 255.0

aspect = height / width;

x = width / 2
y = height / 2

line_width = 0.250 * float(scale_output)
impulse_amp = 5.0 / 256.0
vel_scale = 0.5
strokes_in_batch = 25

# Globals
surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
context = cairo.Context(surface)
surf_data = array.array('B', str(surface.get_data()))

# Functions
def time_str(secs):
    hours = int(math.floor(secs / (60.0 * 60.0)))
    secs = secs - (hours * 60 * 60)
    mins = int(math.floor(secs / 60.0))
    secs = secs - (mins * 60)
    return '%02d:%02d:%02d' % (hours, mins, secs)

def clamp(val, lo, hi):
    if(val < lo):
        return lo
    elif(val > hi):
        return hi;

    return val;

def impulse_from_ref(x, y):
    x = x * image.size[0]
    y = y * image.size[1]
    x = int(clamp(x,  1, image.size[0] - 3))
    y = int(clamp(y,  1, image.size[1] - 3))

    # Compute impulse vector from luminosity gradient (towards lighter areas)
    x_imp = (image.getpixel((x+1, y)) - image.getpixel((x-1, y))) * impulse_amp
    y_imp = (image.getpixel((x, y+1)) - image.getpixel((x, y-1))) * impulse_amp

    return (x_imp, y_imp, x_imp + y_imp + 32.0, image_rgb.getpixel((x, y)))

def impulse_from_buf(x, y):
    x = int(clamp(x,  1, width - 3))
    y = int(clamp(y,  1, height - 3))

    offset = (y * width) + x;

    # Compute impulse vector from luminosity gradient (towards lighter areas)
    x_imp = (surf_data[offset+1] - surf_data[offset-1]) * impulse_amp
    y_imp = (surf_data[offset+width] - surf_data[offset-width]) * impulse_amp

    return (x_imp, y_imp)

class Entity:
    def __init__(self):
        self.last_position = Vector2(0.0,  0.0)
        self.position = Vector2(0.0,  0.0)
        self.velocity = Vector2(0.0,  0.0)
        self.last_width = 1.0

class EntitySet:
    def __init__(self, count, img_luma, img_rgb):
        self.img_luma = img_luma
        self.img_rgb = img_rgb
        self.entities = []

        for i in range(count):
            self.entities.append(Entity())

    def spawn(self, _x, _y, scatter):
        for i in range(len(self.entities)):
            e = self.entities[i]
            bias = lambda: (random.random() * scatter) - (scatter * 0.5)

            e.color = e.last_color = (0, 0, 0)
            e.width = e.last_width = 0
            e.last_position.x = e.position.x = _x + bias()
            e.last_position.y = e.position.y = _y + bias()
            e.velocity.x = bias()
            e.velocity.y = bias()

    def update(self):
        size = len(self.entities)

        if size < 1:
            return

        centroid = Vector2(0.0,  0.0)
        r_size = 1.0 / float(size)

        for i in range(size):
            centroid += self.entities[i].position * r_size

        for i in range(size):
            avoidance = Vector2(0.0,  0.0)
            vel_match = Vector2(0.0,  0.0)
            ent = self.entities[i]

            ent.velocity += (ent.position - centroid) * 0.001

            for c in range(size):
                if c == i:
                    continue

                diff = self.entities[c].position - ent.position
                d = diff.length

                if d < 0.01:
                    d = 0.01

                avoidance += diff * (1.0 / d)

                diff = ent.velocity - self.entities[c].velocity
                d = diff.length

                if d < 0.01:
                    d = 0.01

                vel_match += diff * (1.0 / d)

            ent.velocity += avoidance + vel_match
            ent.last_position.x = ent.position.x
            ent.last_position.y = ent.position.y
            ent.position += ent.velocity * float(scale_output) * vel_scale
            ent.velocity *= 0.95

            x = ent.position.x
            y = ent.position.y

            l_imp = impulse_from_ref(x / width, y / height)
            b_imp = impulse_from_buf(x, y)

            ent.width = math.sqrt((l_imp[0] ** 2) + (l_imp[1] ** 2)) * line_width * l_imp[2]
            ent.width = (ent.last_width * 0.9) + (ent.width * 0.1)
            ent.last_width = ent.width

            ent.last_color = ent.color
            ent.color = (l_imp[3][0] * r255, l_imp[3][1] * r255, l_imp[3][2] * r255)

            # For that added funkyness
            ent.velocity.x += l_imp[0] + b_imp[0]
            ent.velocity.y += l_imp[1] + b_imp[1]

    def render(self):
        for i in range(len(self.entities)):
            e = self.entities[i]

            # Use this instead if interpolation is desired.
            g = cairo.LinearGradient(e.last_position.x, e.last_position.y, e.position.x, e.position.y)

            g.add_color_stop_rgb(0.0, e.last_color[0], e.last_color[1], e.last_color[2])
            g.add_color_stop_rgb(1.0, e.color[0], e.color[1], e.color[2])

            context.set_source(g)
            # context.set_source_rgb(e.color[0], e.color[1], e.color[2])
            context.set_line_width(e.width)
            context.move_to(e.last_position.x, e.last_position.y)
            context.line_to(e.position.x, e.position.y)
            context.stroke()

# Entrypoint
random.seed(986473288) # Deterministic rand

#context.set_source_rgb(0.0 / 255.0, 0.0 / 255.0, 0.0 / 255.0)
context.set_operator(cairo.OPERATOR_SOURCE)
#context.paint()
context.move_to(x, y)
context.set_line_join(cairo.LINE_JOIN_ROUND)
context.set_line_cap(cairo.LINE_CAP_SQUARE)

pos = 0
count = strokes_in_batch # Start with a reset on first interation
islands = 0
start_time = time.clock();
es = EntitySet(20, image, image_rgb)

while(pos < density):
    if(count < strokes_in_batch):

        es.update()
        es.render()

        pos = pos + 1
    else:
        count = 0
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        es.spawn(x, y, random.random() * 10.0)
        print("Rendering: %.02f%% %d / %d strokes (%d islands) in %s.\r" % (((float(pos) / float(density)) * 100.0), pos, density, islands, time_str(time.clock() - start_time)), end=' ')
        sys.stdout.flush()
        islands = islands + 1

    count = count + 1

print("Rendering: %.02f%% %d / %d strokes (%d islands) in %s." % (((float(pos) / float(density)) * 100.0), pos, density, islands, time_str(time.clock() - start_time)))
print("Writing '%s'" % output_filename)

surface.write_to_png(output_filename)

print("Done.")

