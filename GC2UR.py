import gcodetools as ur

gcode_filename = 'gcode.nc'
urscript_filename = 'script.urscript'

gcode = open(gcode_filename, 'r')
urscript = open(urscript_filename, 'w')

for line in gcode:
    script_line = ur.parse_gcode_string(line)
    if script_line:
        print(script_line)
        urscript.write(script_line + '\n')

urscript.close()


