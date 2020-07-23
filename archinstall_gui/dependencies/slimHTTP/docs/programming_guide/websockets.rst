.. _websockets:

Websockets
==========

| WebSockets are supported by slimHTTP, but enabled by a plugin.
| You'll need to install `slimWS <https://slimws.readthedocs.io/en/latest/>`_ one way or another.
| After that, simply plug in the upgrader to slimHTTP:

.. code-block:: py

    import slimHTTP
    import slimWS

    http = slimHTTP.host(slimHTTP.HTTP)
    websocket = spiderWeb.WebSocket()

    @http.on_upgrade
    def upgrade(request):
        new_identity = websocket.WS_CLIENT_IDENTITY(request)
        new_identity.upgrade(request) # Sends Upgrade request to client
        return new_identity

    http.run()

.. note:: slimWS has a rudimentary API support, which can be viewed on the `slimWS <https://slimws.readthedocs.io/en/latest/>`_ documentation.

| The following example will catch any `Connection: upgrade <https://en.wikipedia.org/wiki/HTTP/1.1_Upgrade_header>`_ request,
| and then proceed to in-memory replace the :class:`~slimHTTP.HTTP_CLIENT_IDENTITY` with a `slimWS.WS_CLIENT_IDENTITY <https://slimws.readthedocs.io/en/latest/>`_.
|
| Identities are usually one-shot-sessions, but since WebSockets in general are a session based connection, the `slimWS.WS_CLIENT_IDENTITY <https://slimws.readthedocs.io/en/latest/>`_ persists over requests - as there are no `socket.close()` event for that protocol. slimHTTP honors the `keep-alive` in the identity and doesn't touch the socket after each response.