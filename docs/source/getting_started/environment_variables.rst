Environment variables
=====================

Database creation
-----------------

PROJ_DB
^^^^^^^

ProjPicker needs to know where the PROJ database file ``proj.db`` is to be able to extract necessary information and create its own ``projpicker.db`` database file.
``PROJ_DB`` can be used to specify the full path to ``proj.db``.
However, since `the ProjPicker github repository <https://github.com/HuidaeCho/projpicker>`_ and `its PyPI package <https://pypi.org/project/projpicker/>`_ already provide a ``projpicker.db`` created from `pyproj <https://pypi.org/project/pyproj/>`_ 3.1.0, this variable is only needed when one wants to recreate it for some reason.

PROJ_LIB
^^^^^^^^

This variable is defined by `PROJ <https://proj.org/usage/environmentvars.html>`_ to locate its ``proj.db`` database file.
By definition, it is ``PROJ_DB`` less the filename part ``/proj.db`` or the dirname part of ``PROJ_DB``.
ProjPicker uses this variable only when ``PROJ_DB`` is not defined.
Again, this variable is only useful when a new ``projpicker.db`` needs to be created.

General usage
-------------

PROJPICKER_DB
^^^^^^^^^^^^^

This variable can be used to locate ``projpicker.db`` when it is not in the default location with the ProjPicker module.
It can also be used when a new ``projpicker.db`` is created.
In most cases, it should be not needed.

PROJPICKER_VERBOSE
^^^^^^^^^^^^^^^^^^

The GUI and standalone web server support verbose message printing mainly for debugging purposes.
If this variable is set to ``YES``, debugging messages are printed to ``stderr``.

GUI
---

PROJPICKER_GUI
^^^^^^^^^^^^^^

ProjPicker implements the wxPython-based and tkinter-based GUIs.
If this variable is set to ``tk`` or the wxPython module is not availble, the tkinter-based GUI is used.

PROJPICKER_LATITUDE
^^^^^^^^^^^^^^^^^^^

This variable is used to set the initial latitude for the GUI.
If it is not set or outside -85.0511 and 85.0511, which are the minimum and maximum limits supported by OpenStreetMap, 0 is used.

PROJPICKER_LONGITUDE
^^^^^^^^^^^^^^^^^^^^

This variable is used to set the initial longitude for the GUI.
If it is not set or outside -180 and 180, 0 is used.

PROJPICKER_ZOOM
^^^^^^^^^^^^^^^

This integer varaible is used to set the initial zoom level for the GUI.
If it is not set or outside 0 and 18, which are the minimum and maximum zoom levels supported by OpenStreetMap, 0 is used.

PROJPICKER_DZOOM
^^^^^^^^^^^^^^^^

The mouse wheel usually provides clicking feedback when scrolled, so it feels natural when a zoom event takes place per scroll.
However, TrackPoint lacks such feedback and one can easily produce too many zoom events in a short period of time.
This variable can be used to control the sensitivity of the mouse wheel or TrackPoint for zooming, called the delta zoom level or dzoom.
For the mouse wheel, the default dzoom of 1 works perfectly fine.
For the TrackPoint, a dzoom of 0.1 is recommended for better zooming experience.
