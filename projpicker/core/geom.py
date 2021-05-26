import json
from rtree import index
from .const import RTREE
from .db_operations import query_auth_code


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


def get_geom(pp_con: object, table: str, geom_col: str, code: str) -> list:

    sql = f'''SELECT {geom_col} from {table}
              where auth_code = {code}'''

    geom = pp_con.query(sql)[0]
    return json.loads(geom[0])


def get_bounds(pp_con: object, code: str) -> tuple:
    sql = f'''SELECT south_latitude, west_longitude,
                    north_latitude, east_longitude from projbbox
                    where id = {code}'''
    coordinates = pp_con.query(sql)[0]
    return coordinates


def intersect(pp_con: object, geometry: tuple) -> tuple:
    idx = index.Index(RTREE)
    query = list(idx.intersection((geometry), objects=True))
    bboxs = [(query_auth_code(pp_con, item.id), item.bbox) for item in query]
    return bboxs

