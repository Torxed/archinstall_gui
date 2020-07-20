#!/usr/bin/python
import signal
import dependencies.slimHTTP as slimHTTP
import dependencies.slimWS as slimWS

def sig_handler(signal, frame):
	http.close()
	#https.close()
	exit(0)

signal.signal(signal.SIGINT, sig_handler)

websocket = slimWS.WebSocket()
http = slimHTTP.server(slimHTTP.HTTP, host='127.0.0.1', port=80)

@http.configuration
def config(instance):
	return {
		'web_root' : './gui_data/',
		'index' : 'index.html'
	}

@http.on_upgrade
def upgrade(request):
	new_identity = websocket.WS_CLIENT_IDENTITY(request)
	new_identity.upgrade(request) # Sends Upgrade request to client
	return new_identity

http.run()