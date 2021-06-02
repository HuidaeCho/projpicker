#!/usr/bin/env python3
import projpicker as ppik
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_crs_info

# https://pyproj4.github.io/pyproj/stable/examples.html#find-utm-crs-by-latitude-and-longitude
aoi = [42.032974, -93.581543]

bbox_list = ppik.listify_bbox(ppik.query_bbox(aoi[0], aoi[0], aoi[1], aoi[1]))
bbox_codes = sorted(bbox_list, key=lambda x: x["crs_auth_name"]+x["crs_code"])

crs_list = query_crs_info(
    area_of_interest=AreaOfInterest(
        west_lon_degree=aoi[1],
        south_lat_degree=aoi[0],
        east_lon_degree=aoi[1],
        north_lat_degree=aoi[0],
    ),
)
crs_codes = sorted(crs_list, key=lambda x: x.auth_name+x.code)

b = []
for x in bbox_codes:
    y = x["crs_auth_name"] + ':' + x["crs_code"]
    if y not in b:
        b.append(y)
        print('projpi', y)

c = []
for x in crs_codes:
    y = x.auth_name + ':' + x.code
    if y not in c:
        c.append(y)
        print('pyproj', y)

for x in b:
    if x not in c:
        auth, code = x.split(":")
        print("not in pyproj", x)
        for xx in filter(lambda y: y["crs_auth_name"]==auth and
                                   y["crs_code"]==code, bbox_list):
            print(f"\tusage {xx['usage_auth_name']}:{xx['usage_code']}\n"
                  f"\texten {xx['extent_auth_name']}:{xx['extent_code']}\n"
                  f"\t{xx['south_lat']}, {xx['north_lat']}, "
                  f"{xx['west_lon']}, {xx['east_lon']}")

for x in c:
    if x not in b:
        print("not in projpi", x)
