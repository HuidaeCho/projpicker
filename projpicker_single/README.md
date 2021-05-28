# Single-file ProjPicker

## Command-line usage

```
usage: projpicker.py [-h] [-c] [-O] [-a] [-d PROJPICKER_DB] [-p PROJ_DB]
                     [-g {point,poly,bbox}] [-q {and,or}] [-f {plain,json}]
                     [-n] [-s SEPARATOR] [-i INPUT] [-o OUTPUT]
                     [geometry [geometry ...]]

ProjPicker: Find coordinate reference systems (CRSs) whose bounding box
contains given geometries

positional arguments:
  geometry              query geometry in latitude,longitude (point and poly)
                        or s,n,w,e (bbox); points, points in a poly, or bboxes
                        are separated by a space and polys are separated by
                        any non-coordinate character such as a comma

optional arguments:
  -h, --help            show this help message and exit
  -c, --create          create ProjPicker database
  -O, --overwrite       overwrite output files; applies to both projpicker.db
                        and query output file
  -a, --append          append to output file if any; applies only to query
                        output file
  -d PROJPICKER_DB, --projpicker-db PROJPICKER_DB
                        projPicker database path (default: projpicker.db); use
                        PROJPICKER_DB environment variable to skip this option
  -p PROJ_DB, --proj-db PROJ_DB
                        proj database path (default: /usr/share/proj/proj.db);
                        use PROJ_DB or PROJ_LIB (PROJ_LIB/proj.db) environment
                        variables to skip this option
  -g {point,poly,bbox}, --geometry-type {point,poly,bbox}
                        geometry type (default: point)
  -q {and,or}, --query-mode {and,or}
                        query mode for multiple points (default: and)
  -f {plain,json}, --format {plain,json}
                        output format
  -n, --no-header       do not print header for plain output format
  -s SEPARATOR, --separator SEPARATOR
                        separator for plain output format (default: comma)
  -i INPUT, --input INPUT
                        input geometries path (default: stdin); use - for
                        stdin; not used if geometries are given as arguments
  -o OUTPUT, --output OUTPUT
                        output path (default: stdout); use - for stdout
```

## Creating the ProjPicker database

From shell,
```bash
projpicker.py -c
```

From Python,
```python
import projpicker as ppik
ppik.create_projpicker_db()
```

## Querying points

From shell,
```bash
# read latitude,longitude from arguments
projpicker.py 34.2348,83.8677 33.7490,84.3880

# read latitude,longitude from stdin
projpicker.py <<EOT
34.2348,83.8677
33.7490,84.3880
EOT
```

From Python,
```python
import projpicker as ppik
bbox = ppik.arrayify_bbox(ppik.query_points([[34.2348, 83.8677], [33.7490, 84.3880]]))
```

## Querying polylines/polygons

From shell,
```bash
# read latitude,longitude from arguments
projpicker.py -g poly -- -10,0 10,0 10,10 10,0 , 10,20 30,40

# read latitude,longitude from stdin
projpicker.py -g poly <<EOT
# poly 1
-10,0
10,0
10,10
10,0

# poly 2
10,20
30,40
EOT
```

From Python,
```python
import projpicker as ppik
bbox = ppik.arrayify_bbox(ppik.query_polys([[[-10, 0], [10, 0], [10, 10], [10, 0]], [[10, 20], [30, 40]]]))
```

## Querying bboxes

From shell,
```bash
# read s,n,w,e from arguments
projpicker.py -g bbox 0,0,10,10 20,20,50,50

# read s,n,w,e from stdin
projpicker.py -g bbox <<EOT
0,0,10,10
20,20,50,50
EOT
```

From Python,
```python
import projpicker as ppik
bbox = ppik.arrayify_bbox(ppik.query_bboxes([[0, 0, 10, 10], [20, 20, 50, 50]]))
```

## TODO

1. GUI
   * Desktop
   * Web
