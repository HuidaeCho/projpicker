import numpy as np
from connection import proj_connection


def fill_line(pnt1, pnt2, num_points) -> list:
    xs = np.linspace(pnt1[0], pnt2[0], num_points)
    ys = np.linspace(pnt1[1], pnt2[1], num_points)
    return list(zip(list(xs), list(ys)))


def densified_bbox(bbox, num_points) -> list:
    '''
    Generate densified bbox for a CRS extent
    '''
    poly = []
    for i in range(1, len(bbox) + 1):
        if i > len(bbox) - 1:
            i = 0
        line = fill_line(bbox[i - 1], bbox[i], num_points)
        poly.extend(line)
    return poly

