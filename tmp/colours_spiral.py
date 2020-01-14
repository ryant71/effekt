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

        if l_imp[0] > b_imp[0] or l_imp[1] > b_imp[1]:
            w = math.sqrt((l_imp[0] ** 2) + (l_imp[1] ** 2)) * line_width * l_imp[2] * width_amp
        else:
            w = math.sqrt((l_imp[0] ** 2) + (l_imp[1] ** 2)) * line_width * (255 - l_imp[2]) * width_amp
        
        # last_width = w
        context.line_to(x, y)
        context.set_line_width(w)
        context.set_source_rgb(l_imp[3][0] * r255, l_imp[3][1] * r255, l_imp[3][2] * r255)
        context.line_to(x, y)
        context.stroke()
        
        pos = pos + 1
    else:
        count = 0
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        # switch = 1-switch # Alternate strategies between islands
        print "Rendering: %.02f%% %d / %d strokes (%d islands) in %s.\r" % (((float(pos) / float(total_count)) * 100.0), pos, total_count, islands, time_str(time.clock() - start_time)),
        sys.stdout.flush()
        islands = islands + 1

    context.move_to(x, y)
    count = count + 1
    
print "Rendering: %.02f%% %d / %d strokes (%d islands) in %s." % (((float(pos) / float(total_count)) * 100.0), pos, total_count, islands, time_str(time.clock() - start_time))
print "Writing '%s'" % output_filename

surface.write_to_png(output_filename)

print "Done."


