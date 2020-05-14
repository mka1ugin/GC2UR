import gcodetools as ur
import visualisation as vis

base_point = "p[0.0, 0.0, 0.0, 0.0, 0.0, 0.0]"  # координаты в системе координат робота, которые будут соответствовать нулевой точке GCode
angle = 0                                  # угол поворота

gcode_filename = 'gcode.nc'
urscript_filename = 'script.urscript'


ur.set_transform(base_point, angle)
ur.convert(gcode_filename, urscript_filename)
vis.draw_all(urscript_filename)
