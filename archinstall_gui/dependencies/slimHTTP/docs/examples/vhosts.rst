.. _vhosts:

Virtual Hosts
=============

.. note::
    `SNI <https://en.wikipedia.org/wiki/Server_Name_Indication>`_ is Currently, as of v1.0.1rc3, not supported

| slimHTTP supports working with hosts.
| The vhosts have three different modes, which we'll try to explain here.

Static content mode
-------------------

| Normal operation mode for slimHTTP is to statically deliver anything under `web_root` using `index` whenever directory listing is attempted.
| This mode is there for the **default** unless no other mode is specified, and thus one configuration option is required, and that is :ref:`_web_root`.

.. code-block:: py

    import slimHTTP
    
    http = slimHTTP.server(slimHTTP.HTTP)
    
    @http.configuration
    def config(instance):
        return {
            'vhosts' : {
                'slimhttp.hvornum.se' : {
                    'web_root' : './vhosts/hvornum.se'
                }
            }
        }

This will deliver anything under `./vhosts/hvornum.se` and jail all requests to that folder [1]_.

.. [1] Security issues aside.

reverse proxy mode
------------------

| To configure a reverse proxy, the proxy definitions **must** consist of two things,
| an `addr` and a `port` in the format: `"addr:port"`.
| A simple example would be:

.. code-block:: py

    import slimHTTP
    
    http = slimHTTP.server(slimHTTP.HTTP)
    
    @http.configuration
    def config(instance):
        return {
            'vhosts' : {
                'internal.hvornum.se' : {
                    'proxy' : '192.168.10.10:80'
                }
            }
        }

| Which will allow outside clients to connect to a internal resource on the `192.168.10.10` IP, via slimHTTP.

.. note::
    There's an optional flag to `proxy` definitions, which can be seen under :ref:`_modules`.

module mode
-----------

| The module is a special python import mechanic.
| It supports absolute or relative paths to a module.
| The module itself will be `import <module>` imported with a bit of trickery.

| Some more information regarding module entry points can be found under :ref:`_modules`.
| But to specify a vhost as a module, simply configure the following:

.. code-block:: py

    import slimHTTP
    
    http = slimHTTP.server(slimHTTP.HTTP)
    
    @http.configuration
    def config(instance):
        return {
            'vhosts' : {
                'slimhttp.hvornum.se' : {
                    'module' : './vhosts/hvornum.se/vhost_slimhttp.py'
                }
            }
        }

.. note::
    | module mode is also activated when a client requests a URL that ends with `.py`.

Entry point
^^^^^^^^^^^

| There's no requirements on the module itself.
| It can be any valid Python code and it will be executed as if someone did `import module`. However, there are a optional entry point.

.. code-block:: py

    def on_request(request).
        print(request)

| `on_request` will be called if it's defined, otherwise it won't.
| To access current service instances for decorators, simply import slimHTTP and access the :ref:`~slimHTTP.instances`.

.. code-block:: py

    import slimHTTP
    print(slimHTTP.instances)

    http = slimHTTP.instances[':80']

    @http.route('/', vhost='example.com')
    def handler(request):
        print(request)

.. warning::
    Just make sure you define a `vhost=...`, otherwise you'll replace the default context handler.