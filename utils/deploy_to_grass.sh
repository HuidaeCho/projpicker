#!/bin/sh
set -e

GRASS_DIR=~/usr/grass/grass
CORE_DIR=$GRASS_DIR/python/grass/projpicker
GUI_DIR=$GRASS_DIR/gui/wxpython/projpicker_gui
GETOSM_DIR=$GRASS_DIR/python/grass/projpicker

cd ../projpicker
cp VERSION __init__.py common.py projpicker.db $CORE_DIR

for i in coor_latlon.py coor_xy.py; do
sed '
/^if __package__:$/,/^else:$/{s/^    //}
/^if __package__:$/d
/^else:$/i\

/^else:$/,/^$/d
' $i > $CORE_DIR/$i
done

sed '
/^import argparse$/d
/^has_web = True$/a\
try:\
    from grass.script.setup import set_gui_path\
    set_gui_path()\
    from projpicker_gui import gui\
except Exception:\
    has_gui = False
/^if __package__:$/,/^else:$/{s/^    //}
/^if __package__:$/d
/^else:$/i\

/^else:$/,/^$/d
/^try:$/,/^    has/d
/^has_web = True$/d
/^# https:\/\/stackoverflow/d
/^# command-line interface$/,/^##########/d
/^set_latlon()$/i\
set_latlon()
/^set_latlon()$/,$d
' projpicker.py > $CORE_DIR/projpicker.py

sed '
/^if __package__:$/i\
import grass.projpicker as ppik\

/^if __package__:$/,/^$/d
' gui_common.py > $GUI_DIR/gui_common.py

sed '
/^if __package__:$/i\
import grass.projpicker as ppik\
from grass.getosm import OpenStreetMap\

/^if __package__:$/,/^else:$/{s/^    //}
/^if __package__:$/d
/^else:$/i\

/^else:$/,/^$/d
/import \(projpicker\|OpenStreetMap\)/d
' gui_wx.py > $GUI_DIR/gui.py

# $GUI_DIR/panel.py, derived from wxwidgets.py, is highly modified for GRASS
# GIS; do not copy it anymore
#sed '
#/^if __package__:$/i\
#import grass.projpicker as ppik
#/import projpicker as ppik/d
#' wxwidgets.py > $GUI_DIR/wxwidgets.py

cp getosm.py $GETOSM_DIR
