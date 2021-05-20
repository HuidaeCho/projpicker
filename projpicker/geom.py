import re
import json


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


def bbox_coors(bbox):
    bbox_geom = [
        [bbox[2], bbox[1]],
        [bbox[3], bbox[1]],
        [bbox[3], bbox[0]],
        [bbox[2], bbox[0]],
    ]

    return bbox_geom


def bbox_poly(bbox):
    bbox_geom = bbox_coors(bbox)
    bbox_geom.append(bbox_geom[0])
    return POLYGON(bbox_geom)


def get_geom(cursor, table: str, geom_col: str, code: str):

    sql = f'''SELECT AsGeoJson({geom_col}) from {table}
              where auth_code = {code}'''

    cursor.execute(sql)
    geom = cursor.fetchall()[0]
    geom = json.loads(geom[0])
    return geom.get('coordinates')


