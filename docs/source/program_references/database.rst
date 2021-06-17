Database
========

Requires the PROJ database (e.g., /usr/share/proj/proj.db) only for recreating the provided projpicker.db, if you want.
To recreate projpicker.db, the pyproj module is required.

Creating projpicker.db
----------------------

This step is optional because projpicker.db generated from `pyproj 3.1.0 <https://pypi.org/project/pyproj/3.1.0/>`_ is shipped with the module by default.
Run this step only when you want to recreate this database from your version of PROJ.

Shell
^^^^^

.. code-block:: shell

    projpicker -c

Python
^^^^^^

.. code-block:: python

    import projpicker as ppik
    ppik.create_projpicker_db()

Schema
------

.. code-block:: sql

    CREATE TABLE bbox (
        proj_table TEXT NOT NULL CHECK (length(proj_table) >= 1),
        crs_name TEXT NOT NULL CHECK (length(crs_name) >= 2),
        crs_auth_name TEXT NOT NULL CHECK (length(crs_auth_name) >= 1),
        crs_code TEXT NOT NULL CHECK (length(crs_code) >= 1),
        usage_auth_name TEXT NOT NULL CHECK (length(usage_auth_name) >= 1),
        usage_code TEXT NOT NULL CHECK (length(usage_code) >= 1),
        extent_auth_name TEXT NOT NULL CHECK (length(extent_auth_name) >= 1),
        extent_code TEXT NOT NULL CHECK (length(extent_code) >= 1),
        south_lat FLOAT CHECK (south_lat BETWEEN -90 AND 90),
        north_lat FLOAT CHECK (north_lat BETWEEN -90 AND 90),
        west_lon FLOAT CHECK (west_lon BETWEEN -180 AND 180),
        east_lon FLOAT CHECK (east_lon BETWEEN -180 AND 180),
        bottom FLOAT,
        top FLOAT,
        left FLOAT,
        right FLOAT,
        unit TEXT NOT NULL CHECK (length(unit) >= 2),
        area_sqkm FLOAT CHECK (area_sqkm > 0),
        CONSTRAINT pk_bbox PRIMARY KEY (
            crs_auth_name, crs_code,
            usage_auth_name, usage_code
        ),
        CONSTRAINT check_bbox_lat CHECK (south_lat <= north_lat)
    );
