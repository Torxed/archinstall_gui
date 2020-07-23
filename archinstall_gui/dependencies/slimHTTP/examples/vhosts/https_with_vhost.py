import slimHTTP

https = slimHTTP.host(slimHTTP.HTTPS)

@https.configuration
def config(instance):
	return {
		'web_root' : './vhosts/default',
		'index' : 'index.html',
		'ssl' : {
			'cert' : 'cert.pem',
			'key' : 'key.pem',
		},
		'vhosts' : {
			'example.com' : {
				'module' : './example.com/vhost.py'
			}
		}
	}

while 1:
	for event, *event_data in https.poll():
		pass
