import json
from rtree import index
from .const import RTREE


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
    return str(bbox_geom)


def get_geom(cursor, table: str, geom_col: str, code: str) -> list:

    sql = f'''SELECT {geom_col} from {table}
              where auth_code = {code}'''

    cursor.execute(sql)
    geom = cursor.fetchall()[0]

    return json.loads(geom[0])


def get_bounds(cursor, code: str) -> tuple:
    sql = f'''SELECT south_latitude, west_longitude,
                    north_latitude, east_longitude from projbbox
                    where auth_code = {code}'''
    cursor.execute(sql)
    coordinates = cursor.fetchall()[0]
    return coordinates


def intersect(geometry: tuple) -> tuple:
    idx = index.Index(RTREE)
    query = list(idx.intersection((geometry), objects=True))
    bboxs = [(item.id, item.bbox) for item in query]
    return bboxs

