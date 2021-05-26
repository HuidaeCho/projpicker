import sys
import sqlite3
from dataclasses import dataclass
from distutils.spawn import find_executable
from pathlib import Path
from .const import PROJPICKER_DB


def _validate_proj(data_dir):
    if data_dir is not None and Path(data_dir, "proj.db").exists():
        return True
    return False


def proj_connection():
    try:
        # Returns '/usr/bin/proj' on native Linux install.
        # Resource files, i.e. proj.db, are installed at '/usr/share/proj'
        find_executable("proj")
    except:
        raise Exception("No PROJ installation detected")

    # Need dynamic solution to account for different OS's,
    # proj installations, and potential conda installs.
    # See https://github.com/pyproj4/pyproj/pyproj/datadir.py for
    # example implementation.

    # However, dynamic solution would only be needed if we plan on making our
    # connection reproducible.
    resource_path = Path(sys.prefix, "share", "proj")
    if _validate_proj(resource_path):
        proj_db = Path(resource_path, "proj.db")
    else:
        raise Exception("No proj.db")

    return sqlite3.connect(proj_db)


def projpicker_connection():
    con = sqlite3.connect(PROJPICKER_DB)
    return con


class ProjPickCon:
    '''
    Loose wrapper for the projpicker database
    '''
    def __init__(self):
        self.__db = projpicker_connection()
        self.cur = self.__db.cursor()

    def close(self, commit=False):
        if commit:
            self.__db.commit()
        self.__db.close()

    def query(self, sql):
        self.cur.execute(sql)
        return self.cur.fetchall()
