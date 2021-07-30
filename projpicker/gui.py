"""
TODO
"""
# https://stackoverflow.com/a/49480246/16079666
if __package__:
    try:
        from .gui_wx import *
    except:
        from .gui_tk import *
else:
    try:
        from gui_wx import *
    except:
        from gui_tk import *
