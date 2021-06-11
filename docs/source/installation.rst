Installation
============

Requirements
------------

If installed with pip, ProjPicker uses the following standard modules:

- collections
- argparse
- os
- sys
- sqlite3
- re
- math
- json
- pprint
- ttkinter
- textwrap

The projpicker sqlite databse (``projpicker.db``) will come packaged when
installed with pip. However, if any problems should arise and the
``projpicker.db`` should need to be recreated the additional dependency of
`pyproj 3.1.0 <https://pypi.org/project/pyproj/3.1.0/>`_ will be needed. For
more information about ``projpicker.db`` see :doc:`here <./database>`.

Using pip
---------

- `Python package <https://pypi.org/project/projpicker/>`_

Installation with pip is the recommended way to install both the CLI appliction
and the python module.

.. code-block:: shell

    pip3 install projpicker

    # or if you're not a root
    pip3 install --user projpicker

    # to install development versions
    pip3 install --pre projpicker

    # or if you're not a root
    pip3 install --pre --user projpicker

From source
-----------

The current development version of ProjPicker can be downloaded and installed
from source `here <https://github.com/HuidaeCho/projpicker>`_.

pip can be used to install from the source directory with

.. code-block:: shell

    git clone https://github.com/HuidaeCho/projpicker.git
    cd projpicker
    pip3 install -e .

ArcGIS Pro Toolbox
------------------

The ArcGIS Pro toolbox can be isntalled with the batch script.

- :download:`install.bat <../../guis/arcgispro/install.bat>`
