import re
import json
import numpy as np


def _replace_closure(input: str) -> str:

    if any(x in input for x in ['(', ')']):
        input = input.replace('(', '').replace(')', '')
    if any(x in input for x in ['[', ']']):
        input = input.replace('[', '').replace(']', '')
    return input


def POLYGON(input: (tuple, list)) -> str:
    if input[0] != input[-1]:
        raise Exception("Polygon geometry does not close!")

    geom_str = re.sub(',([^,]*,?)', r'\1', str(input))

    geom_str = _replace_closure(geom_str)

    return f'POLYGON(({geom_str}))'


def POINT(input: (tuple, list)) -> str:

    geom_str = str(input).replace(',', ' ')

    geom_str = _replace_closure(geom_str)

    return f'POINT(({geom_str}))'


def bbox_coors(bbox: list) -> list:
    bbox_geom = [
        [bbox[1], bbox[2]],
        [bbox[3], bbox[2]],
        [bbox[3], bbox[0]],
        [bbox[1], bbox[0]],
    ]

    return bbox_geom


def bbox_poly(bbox: list) -> str:
    bbox_geom = bbox_coors(bbox)
    bbox_geom.append(bbox_geom[0])
    return POLYGON(bbox_geom)


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


def get_geom(cursor, table: str, geom_col: str, code: str):

    sql = f'''SELECT AsGeoJson({geom_col}) from {table}
              where auth_code = {code}'''

    cursor.execute(sql)
    geom = cursor.fetchall()[0]
    geom = json.loads(geom[0])
    return geom.get('coordinates')


def get_bounds(cursor, code):
    sql = f'''SELECT south_latitude, west_longitude,
                    north_latitude, east_longitude from projbbox
                    where auth_code = {code}'''
    cursor.execute(sql)
    coordinates = cursor.fetchall()[0]
    return coordinates
