import signal, time, json
import shlex, pty, os
import sys, traceback
from os import walk, urandom, getcwd
from os.path import splitext, basename, isdir, isfile, abspath
from hashlib import sha512
from json import JSONEncoder, dumps, loads
from collections import OrderedDict as oDict


from lib.loghandler import LOG_LEVELS # log() gets imported automatically.
from lib.helpers import _importer, _gen_uid, _safedict, _sys_command
from lib.worker import _spawn
from lib.websocket import pre_parser
from dependencies.archinstall import archinstall as _archinstall

def sig_handler(signal, frame):
	http.close()
	https.close()
	exit(0)
signal.signal(signal.SIGINT, sig_handler)

## Set up globals that can be used in this project (including sub modules)
__builtins__.__dict__['LOG_LEVEL'] = LOG_LEVELS.INFO
## Setup some global functions:
#  (that can be accessed without importing)
__builtins__.__dict__['importer'] = _importer
__builtins__.__dict__['gen_uid'] = _gen_uid
__builtins__.__dict__['safedict'] = _safedict
__builtins__.__dict__['spawn'] = _spawn
__builtins__.__dict__['sys_command'] = _sys_command
__builtins__.__dict__['archinstall'] = _archinstall
__builtins__.__dict__['modules'] = oDict()
__builtins__.__dict__['storage'] = safedict()
__builtins__.__dict__['progress'] = oDict()
__builtins__.__dict__['sockets'] = safedict()
__builtins__.__dict__['config'] = safedict({
	'slimhttp': {
		'web_root': abspath('./web_content'),
		'index': 'index.html',
		'vhosts': {
			'archinstall.local': {
				'web_root': abspath('./web_content'),
				'index': 'index.html'
			}
		}
	}
})

## Import sub-modules after configuration setup.
from dependencies.slimHTTP import slimhttpd
from dependencies.spiderWeb import spiderWeb

websocket = spiderWeb.upgrader({'default': pre_parser()})
http = slimhttpd.http_serve(upgrades={b'websocket': websocket}, host='127.0.0.1', port=80)
https = slimhttpd.https_serve(upgrades={b'websocket': websocket}, host='127.0.0.1', port=443, cert='cert.pem', key='key.pem')

while 1:
	for handler in [http, https]:
		client = handler.accept()

		#for fileno, client in handler.sockets.items():
		for fileno, event in handler.poll().items():
			if fileno in handler.sockets:  # If not, it's a main-socket-accept and that will occur next loop
				sockets[fileno] = handler.sockets[fileno]
				client = handler.sockets[fileno]
				if client.recv():
					response = client.parse()
					if response:
						try:
							client.send(response)
						except BrokenPipeError:
							pass
						client.close()