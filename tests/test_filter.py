#!/usr/bin/env python3
#shell
# ../projpicker/projpicker.py 34.2348,-83.8677 33.7490,-84.3880 | grep "^projected_crs"
# ../projpicker/projpicker.py 34.2348,-83.8677 33.7490,-84.3880 | grep ",meter,"
#end

import sys
sys.path.insert(0, "../projpicker")
import projpicker as ppik

# sorted by area to find the most local CRS first
bbox = ppik.query_points([[34.2348, -83.8677], [33.7490, -84.3880]])

# projected CRSs only
bbox_proj = list(filter(lambda x: x.proj_table=="projected_crs", bbox))
ppik.print_bbox(bbox_proj, header=False)

# CRSs in meter only
bbox_meter = list(filter(lambda x: x.unit=="meter", bbox))
ppik.print_bbox(bbox_meter, header=False)
