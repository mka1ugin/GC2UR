import math
import datetime
import transform

transformation = False
base_point, angle = None, None

movel_radius = 0
movel_speed = 0.25
movel_acc = 1.2
movec_radius = 0
movec_speed = 0.25
movec_acc = 1.2

min_radius = 0.00001   # минимальный радиус дуги

analogAffector = False  # если True, то задаём на аналоговом выходе значение analogOutValue
analogOutNumber = 0  # номер аналогового выхода
analogOutValue = 1.05  # в Вольтах
digitalOutNumber = 0  # номер цифрового выхода
delay_before_spindle_start = 0
delay_after_spindle_start = 0
delay_before_spindle_stop = 0
delay_after_spindle_stop = 0

f = 0.001  # это если gcode в миллиметрах

last_x, last_y, last_z = 0, 0, 0
rx, ry, rz = 0, 0, 0


def parse_gcode_string(gcommand):

    """
    Парсит принятую строку gcode, если строка валидная, передаёт её функции process_gcode_string
    """

    if gcommand:

        gcommand = gcommand.split()  # разделяем аргументы в строке по пробелам

        if "N" in gcommand[0]:  # если в строке сначала идёт "N**", то отсекаем этот аргумент, это номер строки
            gcommand.remove(gcommand[0])

        if gcommand:
            return(process_gcode_string(gcommand))

def process_gcode_string(gcommand):

    """
    Разбирает команды в полученной на вход строке
    """

    global last_z, last_y, last_x, rx, ry, rz, movel_speed, movec_speed

    if "F" in gcommand[0]:  # если это установка скорости перемещения
        speed = int(gcommand[0].replace("F", ""))
        return(setSpeed(speed))

    if "M" in gcommand[0]:  # если это M-команда, то
        if gcommand[0] == "M3" or gcommand[0] == "M03" or gcommand[0] == "M4" or gcommand[0] == "M04":
            return spindleOn()
        elif gcommand[0] == "M5" or gcommand[0] == "M05":
            return spindleOff()
        else:
            pass

    if gcommand[0] == "G0" or gcommand[0] == "G1":  # если это команда линейного перемещения

        x, y, z, speed = getLinearMove(gcommand)

        return(movel(x, y, z, rx, ry, rz, movel_acc, speed, movel_radius))

    elif gcommand[0] == "G2" or gcommand[0] == "G3":  # если это команда перемещения по дуге

        x0, y0, z0, x1, y1, z1, x2, y2, z2, R = getCircularMove(gcommand)

        if x0 != None and y0 != None and z0 != None and x1 != None and y1 != None and z1 != None and x2 != None and y2 != None and z2 != None and R != None:

            if R < min_radius:
                first_line = movel(x1, y1, z1, rx, ry, rz, a=1.2, v=0.25, r=0, t=0)
                second_line = movel(x2, y2, z2, rx, ry, rz, a=1.2, v=0.25, r=0, t=0)
                last_x = x2
                last_y = y2
                last_z = z2
                return first_line + "\n" + second_line
            else:
                return movec(x1, y1, z1, rx, ry, rz, x2, y2, z2, rx, ry, rz)
        else:
            return None

def movel(x, y, z, rx, ry, rz, a=1.2, v=0.25, r=0, t=0):
    """
    Создаёт команду линейного перемещения
    """

    x = float("{0:.6f}".format(x))
    y = float("{0:.6f}".format(y))
    z = float("{0:.6f}".format(z))
    rx = float("{0:.6f}".format(rx))
    ry = float("{0:.6f}".format(ry))
    rz = float("{0:.6f}".format(rz))

    return f"movel(p[{x}, {y}, {z}, {rx}, {ry}, {rz}], {a}, {v}, {t}, {r})"

def movec(x1, y1, z1, rx1, ry1, rz1, x2, y2, z2, rx2, ry2, rz2, a=1.2, v=0.25, r=0, mode=0):
    """
    Создаёт команду кругового перемещения
    """
    x1 = float("{0:.6f}".format(x1))
    y1 = float("{0:.6f}".format(y1))
    z1 = float("{0:.6f}".format(z1))
    rx1 = float("{0:.6f}".format(rx1))
    ry1 = float("{0:.6f}".format(ry1))
    rz1 = float("{0:.6f}".format(rz1))
    x2 = float("{0:.6f}".format(x2))
    y2 = float("{0:.6f}".format(y2))
    z2 = float("{0:.6f}".format(z2))
    rx2 = float("{0:.6f}".format(rx2))
    ry2 = float("{0:.6f}".format(ry2))
    rz2 = float("{0:.6f}".format(rz2))

    return f"movec(p[{x1}, {y1}, {z1}, {rx1}, {ry1}, {rz1}], p[{x2}, {y2}, {z2}, {rx2}, {ry2}, {rz2}], {a}, {v}, {r}, {mode})"

def setSpeed(speed):
    """
    Устанавливает скорость перемещений
    """
    global movel_speed, movec_speed
    movel_speed = speed * 0.001
    movec_speed = speed * 0.001
    return "#set speed to {} mm/s".format(speed)

def spindleOn():
    """
    Включает исполнительный механизм
    """
    global analogOutValue, delay_before_spindle_start, delay_after_spindle_start
    response = ""

    if delay_before_spindle_start:
        response += f"sleep({delay_before_spindle_start})\n"

    if analogAffector:
        analogOutValue = "%.2f" % (analogOutValue * 0.1)
        response += f"set_analog_out({analogOutNumber}, {analogOutValue})"
    else:
        response += f"set_digital_out({digitalOutNumber}, True)"

    if delay_after_spindle_start:
        response += f"\nsleep({delay_after_spindle_start})"

    return response

def spindleOff():
    """
    Выключает исполнительный механизм
    """
    global delay_before_spindle_stop, delay_after_spindle_stop
    response = ""

    if delay_before_spindle_stop:
        response += f"sleep({delay_before_spindle_stop})\n"

    if analogAffector:
        response += f"set_analog_out({analogOutNumber}, 0)"
    else:
        response += f"set_digital_out({digitalOutNumber}, False)"

    if delay_after_spindle_stop:
        response += f"\nsleep({delay_after_spindle_stop})"

    return response

def getLinearMove(gcommand):
    """
    Генерирует параметры команды линейного перемещения
    """

    gcommand.remove(gcommand[0])
    global last_z, last_y, last_x
    x, y, z, speed = None, None, None, None

    for k in range(len(gcommand)):

        if "X" in gcommand[k]:
            gcommand[k] = gcommand[k].replace('X', '')
            if gcommand[k]:
                x = float(gcommand[k]) * f
            else:
                x = float(gcommand[k + 1]) * f
            last_x = x

        if "Y" in gcommand[k]:
            gcommand[k] = gcommand[k].replace('Y', '')
            if gcommand[k]:
                y = float(gcommand[k]) * f
            else:
                y = float(gcommand[k + 1]) * f
            last_y = y

        if "Z" in gcommand[k]:
            gcommand[k] = gcommand[k].replace('Z', '')
            if gcommand[k]:
                z = float(gcommand[k]) * f
            else:
                z = float(gcommand[k + 1]) * f
            last_z = z

        if "F" in gcommand[k]:
            speed = int(gcommand[k].replace("F", ""))

    if x != None and y != None and transformation == True:
        x, y = transform.transform_point(x, y)
        last_x, last_y = transform.transform_point(last_x, last_y)

    if x == None:
        x = last_x
    if y == None:
        y = last_y
    if z == None:
        z = last_z
    if speed == None:
        speed = movel_speed



    return x, y, z, speed

def getCircularMove(gcommand):
    """
    Генерирует параметры команды кругового перемещения
    """

    if gcommand[0] == "G2":
        direction = "CW"  # дуга по часовой стрелке
    else:
        direction = "CCW"  # дуга против часовой стрелки

    gcommand.remove(gcommand[0])

    global last_z, last_y, last_x

    x0 = last_x
    y0 = last_y
    z0 = last_z
    z2, speed = None, None

    for k in range(len(gcommand)):

        if "X" in gcommand[k]:
            gcommand[k] = gcommand[k].replace('X', '')
            if gcommand[k]:
                x2 = float(gcommand[k]) * f
            else:
                x2 = float(gcommand[k + 1]) * f
            last_x = x2

        if "Y" in gcommand[k]:
            gcommand[k] = gcommand[k].replace('Y', '')
            if gcommand[k]:
                y2 = float(gcommand[k]) * f
            else:
                y2 = float(gcommand[k + 1]) * f
            last_y = y2

        if "Z" in gcommand[k]:
            gcommand[k] = gcommand[k].replace('Z', '')
            if gcommand[k]:
                z = float(gcommand[k]) * f
            else:
                z = float(gcommand[k + 1]) * f
            last_z = z2

        if "I" in gcommand[k]:  # смещение центра по оси X
            gcommand[k] = gcommand[k].replace('I', '')
            if gcommand[k]:
                i = float(gcommand[k]) * f
            else:
                i = float(gcommand[k + 1]) * f

        if "J" in gcommand[k]:  # смещение центра по оси Y
            gcommand[k] = gcommand[k].replace('J', '')
            if gcommand[k]:
                j = float(gcommand[k]) * f
            else:
                j = float(gcommand[k + 1]) * f

        if "F" in gcommand[k]:
            speed = int(gcommand[k].replace("F", ""))

    if speed == None:
        speed = movec_speed
    if z2 == None:
        z2 = last_z

    if transformation == True:
        x2, y2 = transform.transform_point(x2, y2)
        last_x, last_y = transform.transform_point(last_x, last_y)
        i, j = transform.transform_point(i, j, 0, 0, 0, 0)

    x_center = x0 + i
    y_center = y0 + j
    z1 = (z0 + z2) / 2

    quad = calcQuad(x0, x2, y0, y2, direction)

    x1, y1, R = arcCenter(x0, y0, x2, y2, x_center, y_center, direction, quad)

    if x1 != None and y1 != None and R != None:

        return x0, y0, z0, x1, y1, z1, x2, y2, z2, R

    else:

        return None, None, None, None, None, None, None, None, None, None

def arcCenter(x0, y0, x2, y2, x_r, y_r, direction, quad):  # точка начала дуги, точка конца дуги, точка центра дуги
    """
    Определяет точку середины дуги
    """

    # найдём длину хорды:
    l = ((x2 - x0) ** 2 + (y2 - y0) ** 2) ** 0.5

    if l != 0.0:    # если длина хорды ненулевая

        # найдём координаты середины хорды:
        x1 = (x0 + x2) / 2
        y1 = (y0 + y2) / 2
        # найдём расстояние от середины хорды до центра дуги:
        l_1 = ((x1 - x_r) ** 2 + (y1 - y_r) ** 2) ** 0.5

        # найдём радиус дуги:
        R = (((x0 - x_r) ** 2 + (y0 - y_r) ** 2) ** 0.5 + ((x2 - x_r) ** 2 + (y2 - y_r) ** 2) ** 0.5) / 2

        # найдём отрезок медианы от точки середины дуги до хорды:
        l_2 = R - l_1
        # найдём угол дуги:
        angle = calcAngle(x0, x1, x2, y0, y1, y2, x_r, y_r, quad, l, R, direction)

        if angle == None:
            return None, None, None

        if angle < 179.95:

            dx = (x1 - x_r) * R / l_1
            dy = (y1 - y_r) * R / l_1

            x = x_r + dx
            y = y_r + dy

            return x, y, R

        elif angle > 180.05:

            dx = (x1 - x_r) * R / l_1
            dy = (y1 - y_r) * R / l_1

            x = x_r - dx
            y = y_r - dy

            return x, y, R

        else:

            return (halfCicle(x0, x1, x2, y0, y1, y2, l, R, quad))

    else:
        x = (x0 + x2) / 2
        y = (y0 + y2) / 2
        R = 0.0

        return x, y, R

def halfCicle(x0, x1, x2, y0, y1, y2, l, R, quad):
    """
    Определяет точку середины дуги, если эта дуга - полукруг
    """

    if quad == 12:  # если наш полкруг лежит в двух квадратах сразу
        x = (x0 + x2) / 2
        y = y0 + abs((x2 - x0) / 2)
        return x, y, R
    elif quad == 14:
        y = (y0 + y2) / 2
        x = x0 + abs((y2 - y0) / 2)
        return x, y, R
    elif quad == 23:
        y = (y0 + y2) / 2
        x = x0 - abs((y2 - y0) / 2)
        return x, y, R
    elif quad == 34:
        x = (x0 + x2) / 2
        y = y0 - abs((x2 - x0) / 2)
        return x, y, R
    elif quad == 1:
        sin_a = abs(y2 - y0) / l
        cos_a = abs(x2 - x0) / l
        y = y1 + R * sin_a
        x = x1 + R * cos_a
        return x, y, R
    elif quad == 2:
        sin_a = abs(y2 - y0) / l
        cos_a = abs(x2 - x0) / l
        y = y1 + R * sin_a
        x = x1 - R * cos_a
        return x, y, R
    elif quad == 3:
        sin_a = abs(y2 - y0) / l
        cos_a = abs(x2 - x0) / l
        y = y1 - R * sin_a
        x = x1 - R * cos_a
        return x, y, R
    elif quad == 4:
        sin_a = abs(y2 - y0) / l
        cos_a = abs(x2 - x0) / l
        y = y1 - R * sin_a
        x = x1 + R * cos_a
        return x, y, R

def calcQuad(x0, x2, y0, y2, direction):
    """
    Вычисляет четверть, в которой лежит дуга
    """

    if direction == "CW" and x2 == x0 and y2 < y0:
        quad = 14
    elif direction == "CW" and x2 == x0 and y2 > y0:
        quad = 23
    elif direction == "CW" and y2 == y0 and x2 > x0:
        quad = 12
    elif direction == "CW" and y2 == y0 and x2 < x0:
        quad = 34
    elif direction == "CCW" and x2 == x0 and y2 > y0:
        quad = 14
    elif direction == "CCW" and x2 == x0 and y2 < y0:
        quad = 23
    elif direction == "CCW" and y2 == y0 and x2 < x0:
        quad = 12
    elif direction == "CCW" and y2 == y0 and x2 > x0:
        quad = 23
    elif direction == "CW" and x2 > x0 and y2 < y0:
        quad = 1
    elif direction == "CW" and x2 > x0 and y2 > y0:
        quad = 2
    elif direction == "CW" and x2 < x0 and y2 > y0:
        quad = 3
    elif direction == "CW" and x2 < x0 and y2 < y0:
        quad = 4
    elif direction == "CCW" and x2 < x0 and y2 > y0:
        quad = 1
    elif direction == "CCW" and x2 < x0 and y2 < y0:
        quad = 2
    elif direction == "CCW" and x2 > x0 and y2 < y0:
        quad = 3
    elif direction == "CCW" and x2 > x0 and y2 > y0:
        quad = 4
    else:
        quad = 0

    return quad

def calcAngle(x0, x1, x2, y0, y1, y2, x_r, y_r, quad, l, R, direction):
    """
    Вычисляет угол дуги
    """

    angle = 2 * math.asin(0.5 * l / R)
    angle = math.degrees(angle)

    if quad == 1:
        if x_r < x1 and y_r < y1:
            return angle
        else:
            return 360 - angle

    if quad == 12:
        if y_r < y1:
            return angle
        else:
            return 360 - angle

    if quad == 14:
        if x_r < x1:
            return angle
        else:
            return 360 - angle

    if quad == 2:
        if x_r > x1 and y_r < y1:
            return angle
        else:
            return 360 - angle

    if quad == 23:
        if x_r > x1:
            return angle
        else:
            return 360 - angle

    if quad == 3:
        if x_r > x1 and y_r > y1:
            return angle
        else:
            return 360 - angle

    if quad == 34:
        if y_r > y1:
            return angle
        else:
            return 360 - angle

    if quad == 4:
        if x_r < x1 and y_r > y1:
            return angle
        else:
            return 360 - angle

def print_header():
    now = datetime.datetime.now()

    if transformation == True:
        return ("# This URScript file was generated by GC2UR tool coded by M.Kalugin at %s. Have fun!" % str(now) + '\n' "# Target gcode was moved, zero point of gcode now is %s" % base_point + ", rotation angle is %.2f" %math.degrees(angle) + " degrees" + '\n' + '\n')

    return("# This URScript file was generated by GC2UR tool coded by M.Kalugin at %s. Have fun!" % str(now) + '\n' + '\n' + '\n')

def convert(gcode_filename, urscript_filename):

    gcode = open(gcode_filename, 'r')
    urscript = open(urscript_filename, 'w')
    urscript.write(print_header())

    for line in gcode:
        script_line = parse_gcode_string(line)
        if script_line:
            print(script_line)
            urscript.write(script_line + '\n')

    urscript.close()

def set_transform(anchor, rotation):
    global transformation, base_point, angle

    if rotation != 0 or anchor != "p[0.0, 0.0, 0.0, 0.0, 0.0, 0.0]":
        transformation = True
    else:
        transformation = False
    base_point = anchor
    angle = math.radians(rotation)

    transform.set_params(base_point, angle)

    if transformation == True:
        transform.set_axis(base_point)

