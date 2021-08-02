#!/bin/sh
set -e

GRASS_DIR=~/usr/grass/grass
CORE_DIR=$GRASS_DIR/python/grass/projpicker
GUI_DIR=$GRASS_DIR/gui/wxpython/projpicker_gui

cd ../projpicker
cp VERSION __init__.py common.py coor_*.py projpicker.db $CORE_DIR

sed '
/^has_web = True$/a\
\
try:\
    from grass.script.setup import set_gui_path\
    set_gui_path()\
    from projpicker_gui import gui\
except:\
    hsa_gui = False
/^    from . import coor_xy$/i\
    from . import coor_xy
/^    from . import coor_xy$/,+4d
/^    import coor_xy$/i\
    import coor_xy
/^    import coor_xy$/,+4d
' projpicker.py > l

cp getosm.py $GUI_DIR

sed '
/^if __package__:$/i\
import grass.projpicker as ppik
/^if __package__:$/,+3d
' gui_common.py > $GUI_DIR/gui_common.py

sed '
/^if __package__:$/i\
import grass.projpicker as ppik
/import projpicker as ppik/d
' gui_wx.py > $GUI_DIR/gui.py

sed '
/^if __package__:$/i\
import grass.projpicker as ppik
/import projpicker as ppik/d
' wxwidgets.py > $GUI_DIR/wxwidgets.py
