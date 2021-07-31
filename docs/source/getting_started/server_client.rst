Server / client
===============

ProjPicker supports different web technologies to provide its query capabilities on the internet.
It implements its own standalone web server, the Web Server Gateway Interface (WSGI), and the Common Gateway Interface (CGI).
`ProjPicker Web <https://projpicker.pythonanywhere.com/>`_ runs as a WSGI application instance.

Standalone web server
---------------------

The standalone web server is only recommended for desktop usage because of its limited security checks and lack of HTTPS support.
A local server can be started capable of performing ProjPicker queries with the **-S** flag.

.. code-block::

   projpicker -cS

In the above example, the **-c** flag is used together to start the client automatically.
Without this flag, it is the user's responsibility to browse to the correct local URL that the server responds to.

As a WSGI application
---------------------

A WSGI instance can be started using any Python web framework that supports this web technology.
For example, using `bottle <https://bottlepy.org/docs/dev/>`_:

.. code-block:: python

   import bottle
   import web

   bottle.run(web.application, port=8000)

The following command line starts ProjPicker as a WSGI application running on a new HTTP server provided by uwsgi.

.. code-block::

    uwsgi --http :8000 --wsgi-file web.py

If there is already an HTTP server that is configured to use its uwsgi module, a server can be started as follows:

.. code-block::

   uwsgi --socket :8000 --wsgi-file web.py

As a CGI script
---------------

ProjPicker can also be used as a CGI script.
For example, with Apchae, the following .htaccess file turns ProjPicker's `web.py` into a CGI script.

.. code-block:: shell

    <Files "web.py">
        SetHandler cgi-script
    </Files>

    SetEnv PYTHONPATH /home/user/usr/local/src/projpicker/projpicker

    RewriteEngine On
    RewriteRule ^query$ web.py
