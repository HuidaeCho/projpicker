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

Correcting shapefiles with missing projection data in ArcGIS Pro
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With the logical operators detailed in within the :doc:`query_syntax`, the projection information of spatial data which is missing such information can be guessed.
This process can also be seen using the main library api outside of ArcGIS Pro at :doc:`finding_missing_projection`.
The tool titled ``ProjPicker Guess Projection`` provides this functionality with the Tkinter GUI.

Following a similar example as in :doc:`finding_missing_projection`, we create data in and around Atlanta Ga in the CRS NAD 27 / Georgia West (EPSG:26767).
The .prj file is then deleted.
When viewed in its new undefied coordinate system, the data is placed in west Africa where the borders of Benin, Nigeria, and Niger touch.

.. figure:: https://user-images.githubusercontent.com/55674113/121760974-6d0b6f00-cafb-11eb-8335-3ecb2761aeba.png
   :width: 500
   :height: 500
   :align: center

   Created data with original projection


.. figure:: https://user-images.githubusercontent.com/55674113/121760481-084f1500-caf9-11eb-9449-7451ac061c40.png
   :alt: missing projection
   :width: 500
   :height: 500
   :align: center

   Data with projection information missing

Knowing the data is supposed to be in and around Atlanta, Ga - ``ProjPicker Guess Projection`` allows the user to draw either a polygon or point to query the believed "correct" location.
The tool then constructs the :doc:`query_syntax` to use both current location of the data and the belived loction to generate a list of possible CRS's.
Again, this generated list will be sorted to show localized projections first.

.. figure:: https://user-images.githubusercontent.com/55674113/121760900-14d46d00-cafb-11eb-8102-c194c31b71e2.png
   :alt: mising proj gui
   :width: 800
   :height: 800
   :align: center

   Projpicker GUI output

We can see that ProjPicker is able to guess the projection along with a number of other localized guesses.
With the proper CRS selected we can press select and the projection information is now defined for the data placing it in the correct spatial location.
