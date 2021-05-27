#!/bin/sh
# Script to generate both sqlite db and RTree index for ProjPicker.
# Files will be located at ../projpicker/data/

# stop on any error
set -e

cd ../projpicker

python3 build_db.py
python3 build_rtree.py
