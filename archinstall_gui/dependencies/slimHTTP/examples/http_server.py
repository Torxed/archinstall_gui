import slimHTTP

http = slimHTTP.host(slimHTTP.HTTP)

while 1:
	for event, *event_data in http.poll():
		pass