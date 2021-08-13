"""
This module imports the gui_tk or gui_wx module.
"""

import os

_projpicker_gui_env = "PROJPICKER_GUI"

_gui = os.environ.get(_projpicker_gui_env, "wx")

if __package__:
    if _gui == "tk":
        from .gui_tk import *
    else:
        try:
            from .gui_wx import *
        except Exception:
            from .gui_tk import *
else:
    if _gui == "tk":
        from gui_tk import *
    else:
        try:
            from gui_wx import *
        except Exception:
            from gui_tk import *
