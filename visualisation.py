import pylab
import matplotlib.patches
import matplotlib.lines
import matplotlib.path
import math

urscript_filename = 'script.urscript'

line_color = "#34ebc0"
line_width = 1.6
x_min = 0
x_max = 0
y_min = 0
y_max = 0
last_x = None
last_y = None

canvas_size = 1.1

def find_limits(line):
    global x_min, y_min, x_max, y_max

    if "movel" in line:

        line = line[line.find("[") + 1:line.find("]")]
        line = line.replace(', ', ' ')
        line = line.split()
        x = float(line[0]) * 1000
        y = float(line[1]) * 1000

        if x > x_max:
            x_max = x
        if x < x_min:
            x_min = x
        if y > y_max:
            y_max = y
        if y < y_min:
            y_min = y

    if "movec" in line:

        line = line[line.find("[") + 1:line.rfind("]")]
        line = line.replace(', ', ' ')
        line = line.replace('] p[', ' ')
        line = line.split()

        x1 = float(line[0]) * 1000
        y1 = float(line[1]) * 1000
        x2 = float(line[6]) * 1000
        y2 = float(line[7]) * 1000

        if x1 > x_max:
            x_max = x1
        if x1 < x_min:
            x_min = x1
        if x2 > x_max:
            x_max = x2
        if x2 < x_min:
            x_min = x2
        if y1 > y_max:
            y_max = y1
        if y1 < y_min:
            y_min = y1
        if y2 > y_max:
            y_max = y2
        if y2 < y_min:
            y_min = y2

def find_center(x0, y0, x1, y1, x2, y2):
    A = x1 - x0
    B = y1 - y0
    C = x2 - x0
    D = y2 - y0
    E = A * (x0 + x1) + B * (y0 + y1)
    F = C * (x0 + x2) + D * (y0 + y2)
    G = 2 * (A * (y2 - y1) - B * (x2 - x1))
    # Если G = 0, это значит, что через данный набор точек провести окружность нельзя.
    x_r = (D * E - B * F) / G
    y_r = (A * F - C * E) / G

    return(x_r, y_r)

def find_angle(x0, y0, x1, y1):
    if x0 == x1 and y1 > y0:
        angle = 90
    elif x0 == x1 and y1 < y0:
        angle = 270
    elif y0 == y1 and x1 > x0:
        angle = 0
    elif y0 == y1 and x1 < x0:
        angle = 180
    else:
        if x1 > x0 and y1 > y0:
            angle = math.degrees(math.atan((y1 - y0) / (x1 - x0)))
        elif x1 < x0 and y1 > y0:
            angle = 180 - math.degrees(math.atan((y1 - y0) / (x0 - x1)))
        elif x1 < x0 and y1 < y0:
            angle = 180 + math.degrees(math.atan((y1 - y0) / (x1 - x0)))
        else:
            angle = 360 - math.degrees(math.atan((y1 - y0) / (x0 - x1)))

    return angle

def set_limits(xmin, ymin, xmax, ymax):

    global axes

    pylab.xlim(xmin, xmax)
    pylab.ylim(ymin, ymax)

    axes = pylab.gca()
    axes.set_aspect("equal")
    axes.set_xlabel('mm')
    axes.set_ylabel('mm')
    axes.set_facecolor('0.15')
    axes.grid()

    fig = pylab.gcf()
    fig.canvas.set_window_title('URScript preview')

def drawLine(x0, y0, x1, y1):

    line = matplotlib.lines.Line2D ([x0, x1], [y0, y1],
                                    linewidth = line_width,
                                    color = line_color)
    axes.add_line(line)

def drawArc(x0, y0, x1, y1, x2, y2):

    arc_x, arc_y = find_center(x0, y0, x1, y1, x2, y2)

    R = ((x0 - arc_x) ** 2 + (y0 - arc_y) ** 2) ** 0.5

    arc_width = R * 2
    arc_height = R * 2

    arc_theta1 = find_angle(arc_x, arc_y, x0, y0)
    center_theta = find_angle(arc_x, arc_y, x1, y1)
    arc_theta2 = find_angle(arc_x, arc_y, x2, y2)

    if arc_theta1 < center_theta < arc_theta2 or arc_theta1 > center_theta > arc_theta2:    # если дуга меньше 180 градусов
        arc_theta1, arc_theta2 = min(arc_theta1, arc_theta2), max(arc_theta1, arc_theta2)
    else:
        arc_theta1, arc_theta2 = max(arc_theta1, arc_theta2), min(arc_theta1, arc_theta2)

    arc = matplotlib.patches.Arc ((arc_x, arc_y),
                                  arc_width,
                                  arc_height,
                                  theta1 = arc_theta1,
                                  theta2 = arc_theta2,
                                  linewidth = line_width,
                                  color = line_color)
    axes.add_patch(arc)

def parse_linear(line):
    global last_x, last_y

    line = line[line.find("[") + 1:line.find("]")]
    line = line.replace(', ', ' ')
    line = line.split()
    x = float(line[0]) * 1000
    y = float(line[1]) * 1000

    if last_x == None and last_y == None:
        last_x = x
        last_y = y
        return

    else:
        drawLine(last_x, last_y, x, y)
        last_x = x
        last_y = y

def parse_circular(line):
    global last_x, last_y

    line = line[line.find("[") + 1:line.rfind("]")]
    line = line.replace(', ', ' ')
    line = line.replace('] p[', ' ')
    line = line.split()

    x1 = float(line[0]) * 1000
    y1 = float(line[1]) * 1000
    x2 = float(line[6]) * 1000
    y2 = float(line[7]) * 1000

    if last_x == None and last_y == None:
        last_x = x2
        last_y = y2
        return

    else:
        drawArc(last_x, last_y, x1, y1, x2, y2)
        last_x = x2
        last_y = y2

def draw_all(filename):
    urscript = open(filename, 'r')

    for line in urscript:
        if "movel" in line or "movec" in line:
            find_limits(line)

    set_limits(x_min * canvas_size, y_min * canvas_size, x_max * canvas_size, y_max * canvas_size)

    urscript.close()

    urscript = open(filename, 'r')

    for line in urscript:
        if "movel" in line:
            parse_linear(line)
        if "movec" in line:
            parse_circular(line)

    pylab.show()

if __name__ == "__main__":
    draw_all(urscript_filename)

