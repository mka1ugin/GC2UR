import gcodetools as ur

filename = 'gcode.nc'

gcode = open(filename, 'r')

for line in gcode:
    script_line = ur.parse_gcode_string(line)
    if script_line:
        print(script_line)