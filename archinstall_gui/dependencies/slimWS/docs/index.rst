slimWS Documentation
======================

WebSocket framework writtein in Python.<br>
Works standalone but is preferred as `@upgrader` [1]_.

Some of the features of slimWS are:

* **No external dependencies or installation requirements.** Runs without any external requirements or installation processes.

* **Single threaded.** slimWS takes advantage of `select.epoll()` *(`select.select` on Windows)* to achieve blazing speeds without threading the service.

.. [1] Can function as a handler for `Connection: upgrade` requests to slimHTTP

.. _slimHTTP: https://github.com/Torxed/slimHTTP

.. toctree::
   :maxdepth: 3
   :caption: Programming Guide

   programming_guide/installation

.. toctree::
   :maxdepth: 3
   :caption: Getting help

   help/discord
   help/issues

.. toctree::
   :maxdepth: 3
   :caption: API Reference

   slimWS/WS_CLIENT_IDENTITY