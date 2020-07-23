slimHTTP Documentation
======================

| **slimHTTP** is a simple, minimal and flexible HTTP server.
| It supports REST api routes, WebSocket [1]_ traffic and native Python imports as vhost endpoints.
| 
| Here's a `demo <https://hvornum.se/>`_ using minimal setup: 

.. code-block:: py

    import slimHTTP
    
    http = slimHTTP.server(slimHTTP.HTTP)
    http.run()

Some of the features of slimHTTP are:

* **No external dependencies or installation requirements.** Runs without any external requirements or installation processes.

* **Single threaded.** slimHTTP takes advantage of `select.epoll()` *(select.select() on Windows)* to achieve blazing speeds without threading the service. Threads are allowed and welcome, but the core code relies on using as few threads and overhead as possible.

.. [1] WebSocket support is provided by using a `@app.on_upgrade` hook and parsed by a separate library, like spiderWeb_
.. _spiderWeb: https://github.com/Torxed/spiderWeb

.. toctree::
   :maxdepth: 3
   :caption: Programming Guide

   programming_guide/installation
   programming_guide/configuration
   programming_guide/websockets

.. toctree::
   :maxdepth: 3
   :caption: Examples

   examples/basic
   examples/REST
   examples/vhosts

.. toctree::
   :maxdepth: 3
   :caption: Getting help

   help/discord
   help/issues

.. toctree::
   :maxdepth: 3
   :caption: API Reference

   slimHTTP/host
   slimHTTP/HTTP_SERVER
   slimHTTP/HTTPS_SERVER
   slimHTTP/HTTP_REQUEST
   slimHTTP/HTTP_RESPONSE
   slimHTTP/ROUTE_HANDLER
   slimHTTP/HTTP_CLIENT_IDENTITY
   slimHTTP/Events

.. toctree::
   :maxdepth: 3
   :caption: Internal Functions

   slimHTTP/handle_py_request
   slimHTTP/get_file
   slimHTTP/CertManager
   slimHTTP/slimHTTP_Error
   slimHTTP/ConfError
   slimHTTP/NotYetImplemented
   slimHTTP/UpgradeIssue