import slimHTTP

# Fetch an active server instance
https = slimHTTP.instances[':443']

@https.route('/', vhost='example.com')
def main(request):
	"""
	This is only called if / is requested.
	"""
	return request.build_headers() + b'<html><body>Welcome to the front page</body></html>'

def on_request(request):
	"""
	All other requests will be routed to this function,
	including if @app.route functions doesn't return anything.
	"""
	return request.build_headers() + b'<html><body>The default page for example.com</body></html>'