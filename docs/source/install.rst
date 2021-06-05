Install
=======

Requirements
------------

If installed with pip, ProjPicker uses the standard modules

- collections
- argparse
- os
- sys
- sqlite3
- re
- math
- json
- pprint

The projpicker sqlite databse (``projpicker.db``) will
come packaged when installed with pip.
However, if any problems should arise and the ``projpicker.db`` should need to
be recreated the additional dependency of `pyproj 3.1.0 <https://pypi.org/project/pyproj/3.1.0/>`_ will be needed.
For more information about ``projpicker.db`` see :doc:`here <./database>`.

PIP
---

- `Python package <https://pypi.org/project/projpicker/>`_

Installation with pip is the recommended way to install both the CLI appliction
and the python module.

::

    pip3 install projpicker

    # or if you're not a root
    pip3 install --user projpicker

    # to install development versions
    pip3 install --pre projpicker

    # or if you're not a root
    pip3 install --pre --user projpicker


From Source
-----------

The current development version of ProjPicker can be downloaded and installed from source `here <https://github.com/HuidaeCho/projpicker>`_.

Pip can be used to install from the source directory with

::

    pip install -e .



