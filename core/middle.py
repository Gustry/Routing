__author__ = 'etienne'
from math import sqrt, pow

def get_distance(p1, p2):
    delta_x = p2[0] - p1[0]
    delta_y = p2[1] - p1[1]
    return sqrt(pow(delta_x, 2) + pow(delta_y, 2))

def get_distances(line):
    segments_length = []
    for p1, p2 in zip(line[0:], line[1:]):
        segments_length.append(get_distance(p1, p2))
    return segments_length

def get_middle(p1, p2):
    x = float(p1[0] + p2[0]) / 2
    y = float(p1[1] + p2[1]) / 2
    return x, y

def split_middle(line):
    distances = get_distances(line)
    half_distance = sum(distances) / 2
    iter_sum = 0
    for i, dist in enumerate(distances):
        if iter_sum < half_distance:
            iter_sum += dist
        elif iter_sum > half_distance:
            point_1 = line[i-1]
            point_2 = line[i]
            middle = get_middle(point_1, point_2)
            line.insert(i, middle)
            return line[0:i+1], line[i:]
        else:
            return line[0:(i+1)], line[i:]


#a_line = [(0, 0), (1, 1), (3, 3), (4, 4)]
#a_line = [(20.4473,-34.017), (20.4473,-34.017), (20.447,-34.0167), (20.4461,-34.0164)]
#print a_line
#print split_middle(a_line)


