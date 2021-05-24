#!/usr/bin/env python3

import pprint
import argparse
import json
from utils.connection import projpicker_connection
from utils.geom import bbox_coors, intersect


def json_entry(cursor, code, bbox):
    epsg = code
    extent = bbox_coors(bbox)
    entry = {'epsg': epsg,
             'extent': extent,
             'products': [
                 ],
             }
    return entry


def main():
    parser = argparse.ArgumentParser(description="ProjPicker")
    parser.add_argument('coordinates', type=float, nargs=2,
                        help="Point coordinates in lat/lon")
    parser.add_argument('-o', '--output', type=str,
                        help='Create output file of intersection')
    args = parser.parse_args()

    con = projpicker_connection()
    cur = con.cursor()

    inter_crs = intersect(args.coordinates)

    output = {}
    for i in inter_crs:
        output[i[0]] = json_entry(cur, i[0], i[1])

    if args.output:
        with open(args.output, 'w') as file:
            json.dump(output, file, indent=2)
        return

    pprint.pprint(output)


if __name__ == '__main__':
    main()

