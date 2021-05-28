# Single-file ProjPicker

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
