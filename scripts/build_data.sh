#!/bin/sh
# Script to generate both sqlite db and RTree index for ProjPicker.
# Files will be located at ../projpicker/data/

cd ../projpicker &&

python _build_db.py &&
python _build_rtree.py

