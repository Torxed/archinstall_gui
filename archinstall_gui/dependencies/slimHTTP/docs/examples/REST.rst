.. _REST:

REST
====

| By leveraging `@app.route` we can setup mock endpoints.
| These endpoints will get one parameter, the :class:`~slimHTTP.HTTP_REQUEST` object.

.. code-block:: py

    @http.route('/')
    def main_entry(request):
        print(request)

        return request.build_headers() + b'<html><body>Test body</body></html>

This is a minimal example of how to respond with some default basic headers and a default content.

REST with JSON
--------------

| By default, slimHTTP will *try* to parse incoming data labled with `Content-Type: application/json` as JSON.
| But ultimately it's up to the developer to verify.

To convert and work with the request data, you could do something along the lines of:

.. code-block:: py

    @http.route('/')
    def main_entry(request):
        data = json.loads(request.payload.decode('UTF-8'))
        print(data['key'])

And to respond, you could build ontop of it by doing:

.. code-block:: py

    @http.route('/')
    def main_entry(request):
        data = json.loads(request.payload.decode('UTF-8'))
        print(data['key'])
        
        return request.build_headers({'Content-Type' : 'application/json'}) + bytes(json.dumps({"key" : "a value"}, 'UTF-8')

Which would instruct slimHTTP to build a basic header response with one additional header, the `Content-Type` and utilize `json.dumps <https://docs.python.org/3/library/json.html#json.dumps>`_ to dump a dictionary structure.