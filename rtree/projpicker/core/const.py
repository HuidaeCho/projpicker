# CONSTANTS
from pathlib import Path

# Get file path for const.py
file = Path(__file__)

# Create file path within package directory for data
data_dir = file.parent.parent / 'data'
if not data_dir.exists():
    Path.mkdir(data_dir)

# Ancillary data will be created and read from within the package directory
PROJPICKER_DB = str(data_dir / 'projpicker.db')
RTREE = str(data_dir / "projpicker_rtree")

