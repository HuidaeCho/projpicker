"""
This module implements common functions for the gui modules.
"""

import os

projpicker_latitude_env = "PROJPICKER_LATITUDE"
projpicker_longitude_env = "PROJPICKER_LONGITUDE"
projpicker_zoom_env = "PROJPICKER_ZOOM"
projpicker_dzoom_env = "PROJPICKER_DZOOM"


def get_lat():
    """
    Get the initial latitude in decimal degrees from the PROJPICKER_LATITUDE
    environment variable. If this environment variable is not available, return
    0.

    Returns:
        float: Initial latitude in decimal degrees.
    """
    return min(max(float(os.environ.get(projpicker_latitude_env, 0)),
                   -85.0511), 85.0511)


def get_lon():
    """
    Get the initial longitude in decimal degrees from the PROJPICKER_LONGITUDE
    environment variable. If this environment variable is not available, return
    0.

    Returns:
        float: Initial longitude in decimal degrees.
    """
    return min(max(float(os.environ.get(projpicker_longitude_env, 0)),
                   -180), 180)


def get_zoom():
    """
    Get the initial zoom level from the PROJPICKER_ZOOM environment variable.
    If this environment variable is not available, return 0.

    Returns:
        float: Delta zoom level.
    """
    return min(max(int(os.environ.get(projpicker_zoom_env, 0)), 0), 18)


def get_dzoom():
    """
    Get the delta zoom level from the PROJPICKER_DZOOM environment variable. If
    this environment variable is not available, return 1.

    Returns:
        float: Delta zoom level.
    """
    return min(max(float(os.environ.get(projpicker_dzoom_env, 1)), -18), 18)


def parse_geoms(geoms):
    """
    Parse geometries and create a query string.

    Args:
        geoms (list or str): Parsable geometries.

    Returns:
        list, str: List of parsed geometries and query string.
    """
    query_string = ""
    if geoms:
        geoms = ppik.parse_mixed_geoms(geoms)
        geom_type = "point"
        for geom in geoms:
            if geom in ("point", "poly", "bbox"):
                line = geom_type = geom
            elif type(geom) == str:
                line = geom
            else:
                line = ""
                if geom_type == "poly":
                    for coor in geom:
                        line += (" " if line else "") + f"{coor[0]},{coor[1]}"
                else:
                    for coor in geom:
                        line += ("," if line else "") + f"{coor}"
            query_string += line + "\n"
        bbox = ppik.query_mixed_geoms(geoms, projpicker_db)
    else:
        geoms = []
    return geoms, query_string


def adjust_lon(prev_x, x, prev_lon, lon):
    """
    Adjust the current longitude (lon) at x in pixels relative to the previous
    one (prev_lon) at prev_x in pixels such that it becomes between lon - 360
    and lon + 360. This function is used to draw geometries that cross the
    antimeridian.

    Args:
        prev_x (int): Previous x in pixels.
        x (int): Current x in pixels.
        prev_lon (float): Previous longitude in decimal degrees.
        lon (float): Current longitude in decimal degrees.

    Returns:
        float: Adjusted longitude in decimal degrees.
    """
    dlon = lon - prev_lon
    if x > prev_x:
        if dlon < 0:
            lon += 360
        elif dlon > 360:
            lon -= 360
    elif dlon > 0:
        lon -= 360
    elif dlon < -360:
        lon += 360
    return lon


def calc_geoms_bbox(geoms):
    """
    Calculate the union bbox in south, north, west, and east floats in decimal
    degrees that contains all the geometries in geoms.

    Args:
        geoms (list): List of parsed geometries.

    Returns:
        float, float, float, float: South, north, west, and east in decimal
        degrees.
    """
    s = n = w = e = None
    geom_type = "point"
    g = 0
    ngeoms = len(geoms)
    while g < ngeoms:
        geom = geoms[g]
        if geom in ("point", "poly", "bbox"):
            geom_type = geom
            g += 1
            geom = geoms[g]
        if type(geom) == list:
            if geom_type == "point":
                lat, lon = geom
                if s is None:
                    s = n = lat
                    w = e = lon
                else:
                    if lat < s:
                        s = lat
                    elif lat > n:
                        n = lat
                    if lon < w:
                        w = lon
                    elif lon > e:
                        e = lon
            elif geom_type == "poly":
                for coor in geom:
                    lat, lon = coor
                    if s is None:
                        s = n = lat
                        w = e = lon
                    else:
                        if lat < s:
                            s = lat
                        elif lat > n:
                            n = lat
                        if lon < w:
                            w = lon
                        elif lon > e:
                            e = lon
            else:
                b, t, l, r = geom
                if s is None:
                    s = b
                    n = t
                    w = l
                    e = r
                else:
                    if b < s:
                        s = b
                    if t > n:
                        n = t
                    if l < w:
                        w = l
                    if r > e:
                        e = r
        g += 1
    if None not in (s, n, w, e):
        if s == n:
            s -= 0.0001
            n += 0.0001
        if w == e:
            w -= 0.0001
            e += 0.0001
    return s, n, w, e
