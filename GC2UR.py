import gcodetools as ur
import visualisation as vis

gcode_filename = 'gcode.nc'
urscript_filename = 'script.urscript'

gcode = open(gcode_filename, 'r')
urscript = open(urscript_filename, 'w')
urscript.write(ur.print_header())

for line in gcode:
    script_line = ur.parse_gcode_string(line)
    if script_line:
        print(script_line)
        urscript.write(script_line + '\n')

urscript.close()
vis.draw_all(urscript_filename)