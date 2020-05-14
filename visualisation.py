import pylab
import matplotlib.patches
import matplotlib.lines
import matplotlib.path
import math

urscript_filename = 'script.urscript'

canvas_size = 1.1
background_color = "#333333"
grid_color = "#666666"
line_color = "#00cccc"
jog_color = "#9999cc"
line_width = 1.6
jog_line_width = 1

jog = False # True, когда идёт холостое перемещение
jog_z_threshold = 10 # Минимальное смещение по оси Z, после которого начинается/заканчивается холостое перемещение

x_min = 0
x_max = 0
y_min = 0
y_max = 0
last_x = None
last_y = None
last_z = None
total_path = 0

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

    if G != 0:
        # Если G = 0, это значит, что через данный набор точек провести окружность нельзя.
        x_r = (D * E - B * F) / G
        y_r = (A * F - C * E) / G

        return(x_r, y_r)

    else:
        return(None, None)

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
    axes.set_xlabel('mm', color = grid_color)
    axes.set_ylabel('mm', color = grid_color)
    axes.set_facecolor(background_color)

    axes.spines['bottom'].set_color(grid_color)
    axes.spines['top'].set_color(grid_color)
    axes.spines['right'].set_color(grid_color)
    axes.spines['left'].set_color(grid_color)

    axes.grid(which = 'major',
            color = grid_color)
    axes.tick_params(axis='both',
                   which='major',
                   color = grid_color,
                   labelcolor = grid_color)

    fig = pylab.gcf()
    fig.set(facecolor = background_color)
    fig.canvas.set_window_title('URScript preview')

def drawLine(x0, y0, x1, y1):

    if x0 == None or y0 == None or x1 == None or y1 == None:
        return

    global jog, total_path

    if jog == True:

        line = matplotlib.lines.Line2D ([x0, x1], [y0, y1],
                                        linewidth = jog_line_width,
                                        color = jog_color)


    else:
        line = matplotlib.lines.Line2D([x0, x1], [y0, y1],
                                       linewidth=line_width,
                                       color=line_color)

    axes.add_line(line)

    total_path += ((x0 - x1) ** 2 + (y0 - y1) ** 2) ** 0.5

def drawArc(x0, y0, x1, y1, x2, y2):

    if x0 == None or y0 == None or x1 == None or y1 == None or x2 == None or y2 == None:
        return

    global total_path

    arc_x, arc_y = find_center(x0, y0, x1, y1, x2, y2)

    if arc_x == None or arc_y == None:
        return

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

    total_path += (R * math.pi * abs(arc_theta2 - arc_theta1)) / 180

def parse_linear(line):
    global last_x, last_y, last_z, jog

    line = line[line.find("[") + 1:line.find("]")]
    line = line.replace(', ', ' ')
    line = line.split()
    x = float(line[0]) * 1000
    y = float(line[1]) * 1000
    z = float(line[2]) * 1000

    if last_x == None and last_y == None and last_z == None:
        last_x = x
        last_y = y
        last_z = z
        jog = True
        return

    else:

        if x == last_x and y == last_y and abs(z - last_z) > jog_z_threshold:
            jog = not jog

        drawLine(last_x, last_y, x, y)
        last_x = x
        last_y = y
        last_z = z

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

    axes.text((x_min + (x_max - x_min) * 0.1), (y_min + (y_max - y_min) * 0.1), f'Total path: {int(total_path)} mm',
            fontsize=8,
            color = jog_color)

    pylab.show()

if __name__ == "__main__":
    draw_all(urscript_filename)

