ArcGIS Pro toolbox
==================

Getting started
---------------

Installation
^^^^^^^^^^^^

Installation script: `install.bat <https://raw.githubusercontent.com/HuidaeCho/projpicker/main/guis/arcgispro/install.bat>`_

The ArcGIS Pro toolbox can be installed with the batch script.
The installation script provides a GUI interface which allows the user to install the toolbox and the required Python module in a given folder.
The link to the install script will direct you to the raw file.
Right click on the page when there and click save as to save a local copy of the script.

.. figure:: https://user-images.githubusercontent.com/55674113/121754165-e4340980-cae1-11eb-8972-0d0b0ec076fb.png
   :align: center

    Manual 'save as' from web browser

One can also use ``cUrl`` or ``Wget`` to retrieve the install script

cUrl
____

.. code-block:: bash

   curl https://raw.githubusercontent.com/HuidaeCho/projpicker/main/guis/arcgispro/install.bat -o install.bat


wget
____
.. code-block:: bash

   wget https://raw.githubusercontent.com/HuidaeCho/projpicker/main/guis/arcgispro/install.bat


Included tools
^^^^^^^^^^^^^^

- ``ProjPicker Create Feature Class``
- ``ProjPicker Guess Projection``

Additional GUI
^^^^^^^^^^^^^^

An additional GUI created with `tkinter <https://docs.python.org/3/library/tkinter.html>`_ and integrated into the ArcGIS Pro toolbox allows the user to sort through and view available projections for their data.

.. figure:: https://user-images.githubusercontent.com/55674113/121754753-6244e000-cae3-11eb-8aee-a860da0caebc.png
   :align: center

   ProjPicker GUI

Usage examples
--------------

ProjPicker aided feature class creation in ArcGIS Pro
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``ProjPicker Create Feature Class`` provides a tool to aid in the creation of new data.
The tool allows the user to draw a spatial query area and get projection recommendations for the a feature class.
This functionality is particularly useful when useful when a new project is undertaken and new data must be generated.

.. image:: https://user-images.githubusercontent.com/55674113/121751862-fd868700-cadc-11eb-9c4d-e32a3c3349d7.png
   :width: 800
   :height: 800

ProjPicker will query available CRS's based on the spatial query and sort them to show the most localized projections first.
Additionaly, the user is able to sort by unit and projection type to quickly make better decisions for the data.



