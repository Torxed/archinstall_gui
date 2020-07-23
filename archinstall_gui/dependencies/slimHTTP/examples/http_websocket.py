import slimHTTP
import spiderWeb # Requires https://github.com/Torxed/spiderWeb

http = slimHTTP.host(slimHTTP.HTTP)
websocket = spiderWeb.WebSocket()

@websocket.route('/auth/login')
def auth_handler(request):
	print('Auth:', request)

@http.on_upgrade
def upgrade(request):
	print('Upgrading to WS_CLIENT_IDENTITY')
	new_identity = websocket.WS_CLIENT_IDENTITY(request)
	new_identity.upgrade(request)
	return new_identity

while 1:
	for event, *event_data in http.poll():
		pass
