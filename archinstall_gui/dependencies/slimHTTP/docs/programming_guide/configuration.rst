.. _configuration:

*************
Configuration
*************

| Configuration is done by supplying slimHTTP with a `dict` of options.
| A complete example can be found under `Example configuration`_.

.. warning::
    | There's startup-sensitive configuration options.
    | Those are `addr` and `port` to set the listening interface.

    To delcare `addr` and `port` - you have to do it from the startup code:

    .. code-block:: py

        import slimHTTP
        
        http = slimHTTP.server(slimHTTP.HTTP, addr='127.0.0.1', port=8080)
        http.run()

    Trying to set it in the runtime configuration will fail, as the server has already setup the `socket.bind((addr, port))`

.. note
..    | Also note that configuration is done from the developers code that imported slimHTTP.
..    | It's there for up to the developer if the config should be stored on disk in a particular format or in the code itself.

.. note::
    All following config options are runtime friendly, they can be changed whenever during normal operation without needing to reload the server.
    The format for the configuration is a valid python `dict`:

    .. code-block:: py

        {
            'key-one' : 'value',
            'key-two' : 'value'
        }

    Where the `key` is any of the below options, and the value is whatever corresponds to that particular key or option.

Example configuration
=====================

.. code-block:: py

    import slimHTTP
    
    http = slimHTTP.server(slimHTTP.HTTP)
    
    @http.configuration
    def config(instance):
        return {
            'web_root' : './vhosts/default',
            'index' : 'index.html',
            'vhosts' : {
                'hvornum.se' : {
                    'web_root' : './vhosts/hvornum.se',
                    'index' : 'index.html'
                },
                'slimhttp.hvornum.se' : {
                    'module' : './vhosts/internal_tests/vhost.py'
                }
            }
        }
    
    http.run()

| Here, configuration changes after the server has finished starting up.
| The same configuration *could* be given on startup, but is not mandatory.
|
| The configuration changes the default web-root as well as some minor changes
| to `vhost` specific resources.

Global configuration options
============================

| Below follows some of the configuration options that are available at all configuration levels.
| These can there for be set in `vhost` scope as well as the `base`/`global` scope.

web_root
--------

| As all other variables, Web roots can be configured in the global and `vhost` scope.
| The paths them selves can be relative or absolute, they will be resolved in runtime.

    .. code-block:: py

        {'web_root' : './path'}

index
-----

| `index` can be either a single `str` of a filename, or
| it can be a `list` of files in which slimHTTP will try them in cronological order.

    .. code-block:: py

        {'index' : ['index.html', 'main.py']}

Vhost specific configuration
============================

vhosts
------

| `vhosts` key should be placed in the *base* configuration and be directly followed by a `key` representing the name of the domain *(FQDN)* that slimHTTP should react to.
| And the value should be a `dict` containing any valid slimHTTP configuration.
| For instance, for the *FQDN* `https://slimhttp.hvornum.se/ <https://slimhttp.hvornum.se/>`_ the config would be:

    .. code-block:: py

        {
            'vhosts' : {
                'slimhttp.hvornum.se' : {
                    // config options for slimhttp.hvornum.se
                }
            }
        }

| Where the configuration specifics for that domain would be placed instead of the "comment".
| for instance `'index' : 'index.html'` could be added.

.. _modules:

module
------

.. note::
    | module mode is also activated when a client requests a URL that ends with `.py`.

| The `module` is a key which can tell slimHTTP that instead of using `reverse proxy` mode or a normal `look for a index` mode.
| slimHTTP should import the script in question, and return the data given by that module. Here's an example:

    .. code-block:: py

        {
            'vhosts' : {
                'slimhttp.hvornum.se' : {
                    'module' : './vhosts/hvornum.se/vhost_slimhttp.py'
                }
            }
        }

| The exact structure of the module can be anything.
| But there are two main entry functions slimHTTP will look for.

.. warning::
    | The module is **reloaded** each request.
    | This means that persistant data or information has to be stored away on each request.
    | To use a in-memory storage, you *could* altho not recommended, use something like this in `vhost_slimhttp.py` from the above example.

    .. code-block:: py

        if not 'MyMemStorage' in __builtins__: __builtins__['MyMemStorage'] = {}
        if not 'counter' in MyMemStorage: MyMemStorage['counter'] = 0
        
        print(f"The module ran with counter value {MyMemStorage['counter']}. Incremeting value!"")
        
        MyMemStorage['counter'] += 1

    Or you could use `pickle.dumps <https://docs.python.org/3/library/pickle.html#pickle.dumps>`_ or a database to store the data you need between sessions. Although they will be a bit slower considering they're not working within the application memory space.

on_request
^^^^^^^^^^

**if the function** `on_request` is defined *(using `hasattr('on_request', <module>)`)*, slimHTTP will automatically call it upon each request to that vhost.

.. warning::
    if `@app.route('/...', vhost='example.com')` is defined, that will take precedence over the `on_request` **if** `on_request` returns data. Otherwise the `@app.route` will be a fallback.

@app.route
^^^^^^^^^^

| It's possible to set up `vhost` specific routes. These acts as normal :ref:`REST`-like endpoints.
| The key difference is that `@app.route` takes a additional keyword, `vhost=:str`. And to access it,
| you need to get the current server instance so you can decorate it.

.. code-block:: py

    import slimHTTP
    
    http = slimHTTP.instances[':80']
    
    @http.route('/', vhost='example.com')
    def route_handler(request).
        print(request)

| This will server `/` but only for the given `vhost`.
| And this could serve as a entry-point for vhost specific modules.

.. note::
    Note that the instance depends on the `addr` and `port` used, a *"listening on every interface on port 80"* would be `:80` in this case.

.. _proxy:

proxy
-----

| Reverse proxy support can be enabled in any vhost.
| The reverse proxy will kick in once a valid HTTP header with the `Host: <host>` field defined.
| Upon which slimHTTP will switch from a :class:`~slimHTTP.HTTP_REQUEST` to a :class:`~slimHTTP.HTTP_PROXY_REQUEST`.

.. warning::
    The :class:`~slimHTTP.HTTP_REQUEST` object has two pitfalls. One, if the proxy is slow to respond all concurrent HTTP requests to slimHTTP will become slow, since we're single threaded, it means that the proxy response has to be parsed in full before other requests can come in. The second pitfall being `Issue #11 <https://github.com/Torxed/slimHTTP/issues/11>`_.

.. code-block:: py

    {
        'vhosts' : {
            'internal.hvornum.se' : {
                'proxy' : '192.168.10.10:80',
                'ssl' : False
            }
        }
    }

| Here, `http://internal.hvornum.se` requests are proxied down to `192.168.10.10` on port `80`.

.. note::
    The `'ssl' : False'` is optional and the default behavior.