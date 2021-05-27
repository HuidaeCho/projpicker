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
# read coordinates from arguments
projpicker.py 34.2348,83.8677 33.7490,84.3880

# read coordinates from stdin
projpicker.py -i- <<EOT
34.2348,83.8677
33.7490,84.3880
EOT
```

From Python,
```python
import projpicker as ppik

bbox = ppik.arrayify_bbox(ppik.query_points([[34.2348, 83.8677], [33.7490, 84.3880]]))
```

## TODO

* Polylines, polygons => Convex hull => Completely contained CRSs
* Smallest CRSs
* CRSs closest to query centroid
