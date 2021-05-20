import pprint
from rtree import index
from connection import projpicker_connection
from geom import get_geom

POINT = (32.5398672, -82.9042053)

con = projpicker_connection('./projpicker.db')
cur = con.cursor()

idx = index.Index('rtree')

inter_crs = list(idx.intersection((POINT)))


def json_entry(cursor, code):
    epsg = code
    extent = get_geom(cursor, 'densbbox', 'geom', code)
    extent = extent[0][:-1]

    entry = {'epsg': epsg,
             'extent': extent,
             'products': [
                 {}
                 ],
             }
    return entry


output = []
for i in inter_crs:
    output.append(json_entry(cur, i))

pprint.pprint(output)

