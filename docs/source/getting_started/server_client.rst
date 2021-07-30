Server / Client
===============

A server can be started capable of performing ProjPicker Queries with the **-S** flag.
It can be accessed either through a local client at the specified local host or used as a public facing site such as is available at `projpicker.pythonanywhere.com <https://projpicker.pythonanywhere.com/>`_


Server uses
-----------

Local desktop
^^^^^^^^^^^^^

.. code-block::

   projpicker -S

Python web framework
^^^^^^^^^^^^^^^^^^^^

With `bottle <https://bottlepy.org/docs/dev/>`_

.. code-block:: python

   import bottle
   import web

   bottle.run(web.application, port=8000)


With uwsgi
^^^^^^^^^^

.. code-block::

    uwsgi --http :8000 --wsgi-fe web.py

or with a web server and its uwsgi module

.. code-block::

   uwsgi --socket :8000 --wsgi-file web.py

As a CGI script with Apache
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: shell

    <Files "web.py">
        SetHandler cgi-script
    </Files>

    SetEnv PYTHONPATH /home/user/usr/local/src/projpicker/projpicker

    RewriteEngine On
    RewriteRule ^query$ web.py


Client
------

The local server can be started and opened with

.. code-block::

   projpicker -c
