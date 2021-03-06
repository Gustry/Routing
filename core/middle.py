from math import sqrt, pow, cos, sin, atan2, pi


def get_distance(p1, p2):
    delta_x = p2[0] - p1[0]
    delta_y = p2[1] - p1[1]
    return sqrt(pow(delta_x, 2) + pow(delta_y, 2))


def get_distances(line):
    segments_length = []
    for p1, p2 in zip(line[0:], line[1:]):
        segments_length.append(get_distance(p1, p2))
    return segments_length


def azimuth(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    rads = atan2(dy, dx)
    rads %= 2*pi
    return rads


def get_middle(p1, p2, distance):
    teta = azimuth(p1, p2)
    x = distance * cos(teta) + p1[0]
    y = distance * sin(teta) + p1[1]
    return x, y


def split_middle(line):
    distances = get_distances(line)
    half_distance = sum(distances) / 2
    iter_sum = 0
    for i, dist in enumerate(distances):
        if iter_sum < half_distance < iter_sum + dist:
            point_1 = line[i]
            point_2 = line[i+1]
            d = half_distance - iter_sum
            middle = get_middle(point_1, point_2, d)
            line.insert(i+1, middle)
            return line[0:i+2], line[i+1:]
        elif half_distance == iter_sum + dist:
            return line[0:i+2], line[i+1:]
        else:
            iter_sum += dist
