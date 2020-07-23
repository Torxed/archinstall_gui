import ssl, os, sys, random, json, glob
import ipaddress
import importlib.util, traceback
from datetime import date, datetime
from os.path import isfile, abspath
from hashlib import sha512
from json import dumps
from time import time, sleep
from mimetypes import guess_type # TODO: issue consern, doesn't handle bytes,
								 # requires us to decode the string before guessing type.
try:
	from OpenSSL.crypto import load_certificate, SSL, crypto, load_privatekey, PKey, FILETYPE_PEM, TYPE_RSA, X509, X509Req, dump_certificate, dump_privatekey
	from OpenSSL._util import ffi as _ffi, lib as _lib
except:
	class MOCK_CERT_STORE():
		def __init__(self):
			pass
		def add_cert(self, *args, **kwargs):
			pass
	class SSL():
		"""
		This is *not* a crypto implementation!
		This is a mock function to get ssl lib to behave like PyOpenSSL.SSL
		"""
		TLSv1_2_METHOD = 0b110
		VERIFY_PEER = 0b1
		VERIFY_FAIL_IF_NO_PEER_CERT = 0b10
		MODE_RELEASE_BUFFERS = 0b10000
		def __init__(self):
			self.key = None
			self.cert = None
		def Context(*args, **kwargs):
			return SSL()
		def set_verify(self, *args, **kwargs):
			pass
		def set_verify_depth(self, *args, **kwargs):
			pass
		def use_privatekey_file(self, path, *args, **kwargs):
			self.key = path
		def use_certificate_file(self, path, *args, **kwargs):
			self.cert = path
		def set_default_verify_paths(self, *args, **kwargs):
			pass
		def set_mode(self, *args, **kwargs):
			pass
		def load_verify_locations(self, *args, **kwargs):
			pass
		def get_cert_store(self, *args, **kwargs):
			return MOCK_CERT_STORE()
		def Connection(context, socket):
			if type(context) == SSL:
				new_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
				new_context.load_cert_chain(context.cert, context.key)
				context = new_context
			return context.wrap_socket(socket, server_side=True)

from socket import *
try:
	from select import epoll, EPOLLIN
except:
	import select
	EPOLLIN = None
	class epoll():
		""" #!if windows
		Create a epoll() implementation that simulates the epoll() behavior.
		This so that the rest of the code doesn't need to worry weither we're using select() or epoll().
		"""
		def __init__(self):
			self.sockets = {}
			self.monitoring = {}

		def unregister(self, fileno, *args, **kwargs):
			try:
				del(self.monitoring[fileno])
			except:
				pass

		def register(self, fileno, *args, **kwargs):
			self.monitoring[fileno] = True

		def poll(self, timeout=0.5, *args, **kwargs):
			try:
				return [[fileno, 1] for fileno in select.select(list(self.monitoring.keys()), [], [], timeout)[0]]
			except OSError:
				return []

HTTP = 0b0001
HTTPS = 0b0010
instances = {}
def server(mode=HTTPS, *args, **kwargs):
	"""
	server() is essentially just a router.
	It creates a instance of a selected mode (either `HTTP_SERVER` or `HTTPS_SERVER`).
	It also saves the instance in a shared instance variable for access later.
	"""
	if mode == HTTPS:
		instance = HTTPS_SERVER(*args, **kwargs)
	elif mode == HTTP:
		instance = HTTP_SERVER(*args, **kwargs)
		
	instances[f'{instance.config["addr"]}:{instance.config["port"]}'] = instance
	return instance

def host(*args, **kwargs):
	"""
	Legacy function, re-routes to server()
	"""
	print('[Warn] Deprecated function host() called, use server(mode=<mode>) instead.')
	return server(*args, **kwargs)

def drop_privileges():
	#TODO: implement
	return True

def uniqueue_id(seed_len=24):
	"""
	Generates a unique identifier in 2020.
	TODO: Add a time as well, so we don't repeat the same 24 characters by accident.
	"""
	return sha512(os.urandom(seed_len)).hexdigest()

imported_paths = {}
def handle_py_request(request):
	"""
		Handles the import of a specific python file.
	"""
	path = abspath('{}/{}'.format(request.web_root, request.headers[b'URL']))
	old_version = False
	request.CLIENT_IDENTITY.server.log(f'Request to "{path}"', level=4, origin='slimHTTP', function='handle_py_request')
	if path not in imported_paths:
		## https://justus.science/blog/2015/04/19/sys.modules-is-dangerous.html
		try:
			request.CLIENT_IDENTITY.server.log(f'Loading : {path}', level=4, origin='slimHTTP')
			spec = importlib.util.spec_from_file_location(path, path)
			imported_paths[path] = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(imported_paths[path])
			sys.modules[path] = imported_paths[path]
		except (SyntaxError, ModuleNotFoundError) as e:
			request.CLIENT_IDENTITY.server.log(f'Failed to load file ({e}): {path}', level=2, origin='slimHTTP', function='handle_py_request')
			return None
	else:
		request.CLIENT_IDENTITY.server.log(f'Reloading: {path}', level=4, origin='slimHTTP', function='handle_py_request')
		try:
			raise SyntaxError('https://github.com/Torxed/ADderall/issues/11')
		except SyntaxError as e:
			old_version = True
			request.CLIENT_IDENTITY.server.log(f'Failed to reload requested file ({e}): {path}', level=2, origin='slimHTTP', function='handle_py_request')
	return old_version, imported_paths[f'{path}']

def get_file(request, ignore_read=False):
	"""
	Read a local file.
	"""
	real_path = abspath('{}/{}'.format(request.web_root, request.headers[b'URL']))
	request.CLIENT_IDENTITY.server.log(f'Opening local file "{real_path}"')
	if b'range' in request.headers:
		_, data_range = request.headers[b'range'].split(b'=',1)
		start, stop = [int(x) for x in data_range.split(b'-')]
		request.CLIENT_IDENTITY.server.log(f'Limiting to range: {start}-{stop}')
	else:
		start, stop = None, None

	extension = os.path.splitext(real_path)[1]

	if isfile(real_path) and extension != '.py':
		if ignore_read is False:
			with open(real_path, 'rb') as fh:
				if start:
					fh.seek(start)
				if stop:
					data = fh.read(stop-start)
				else:
					data = fh.read()
		else:
			data = b''
		
		filesize = os.stat(real_path).st_size
		request.CLIENT_IDENTITY.server.log(f'Returning file content: {len(data)} (actual size: {filesize})')
		return 200, real_path, filesize, data

	request.CLIENT_IDENTITY.server.log(f'404 - Could\'t locate file {real_path}', level=3, source='get_file')
	return 404, '404.html', -1, b'<html><head><title>404 - Not found</title></head><body>404 - Not found</body></html>'

def json_serial(obj):
	"""
	A helper function to being able to `json.dumps()` most things.
	Especially `bytes` data needs to be converted to a `str` object.

	Use this with `default=json_serial` in `json.dumps(default=...)`.

	:param obj: A dictionary object (not the `dict` itself)
	:type obj: Any `dict` compatible `key` or `value`.

	:return: `key` or `value` converted to a `JSON` friendly type.
	:rtype: Any `JSON` compatible `key` or `value`.
	"""
	if isinstance(obj, (datetime, date)):
		return obj.isoformat()
	elif type(obj) is bytes:
		return obj.decode('UTF-8')
	elif getattr(obj, "__dump__", None): #hasattr(obj, '__dump__'):
		return obj.__dump__()
	else:
		return str(obj)

	raise TypeError('Type {} is not serializable: {}'.format(type(obj), obj))

class CertManager():
	"""
	CertManager() is a class to handle creation of certificates.
	It attempts to use the *optional* PyOpenSSL library, if that fails,
	the backup option is to attempt a subprocess.Popen() call to openssl.

	Warning: WIP!
	"""
	def generate_key_and_cert(key_file, **kwargs):
		# TODO: Fallback is to use subprocess.Popen('openssl ....')
		#       since installing additional libraries isn't always possible.
		#       But a return of None is fine for now.
		try:
			from OpenSSL.crypto import load_certificate, SSL, crypto, load_privatekey, PKey, FILETYPE_PEM, TYPE_RSA, X509, X509Req, dump_certificate, dump_privatekey
			from OpenSSL._util import ffi as _ffi, lib as _lib
		except:
			return None

		# https://gist.github.com/kyledrake/d7457a46a03d7408da31
		# https://github.com/cea-hpc/pcocc/blob/master/lib/pcocc/Tbon.py
		# https://www.pyopenssl.org/en/stable/api/crypto.html
		a_day = 60*60*24
		if not 'cert_file' in kwargs: kwargs['cert_file'] = None
		if not 'country' in kwargs: kwargs['country'] = 'SE'
		if not 'sate' in kwargs: kwargs['state'] = 'Stockholm'
		if not 'city' in kwargs: kwargs['city'] = 'Stockholm'
		if not 'organization' in kwargs: kwargs['organization'] = 'Evil Scientist'
		if not 'unit' in kwargs: kwargs['unit'] = 'Security'
		if not 'cn' in kwargs: kwargs['cn'] = 'server'
		if not 'email' in kwargs: kwargs['email'] = 'evil@scientist.cloud'
		if not 'expires' in kwargs: kwargs['expires'] = a_day*365
		if not 'key_size' in kwargs: kwargs['key_size'] = 4096
		if not 'ca' in kwargs: kwargs['ca'] = None

		priv_key = PKey()
		priv_key.generate_key(TYPE_RSA, kwargs['key_size'])
		serialnumber=random.getrandbits(64)

		if not kwargs['ca']:
			# If no ca cert/key was given, assume that we're trying
			# to set up a CA cert and key pair.
			certificate = X509()
			certificate.get_subject().C = kwargs['country']
			certificate.get_subject().ST = kwargs['state']
			certificate.get_subject().L = kwargs['city']
			certificate.get_subject().O = kwargs['organization']
			certificate.get_subject().OU = kwargs['unit']
			certificate.get_subject().CN = kwargs['cn']
			certificate.set_serial_number(serialnumber)
			certificate.gmtime_adj_notBefore(0)
			certificate.gmtime_adj_notAfter(kwargs['expires'])
			certificate.set_issuer(certificate.get_subject())
			certificate.set_pubkey(priv_key)
			certificate.sign(priv_key, 'sha512')
		else:
			# If a CA cert and key was given, assume we're creating a client
			# certificate that will be signed by the CA.
			req = X509Req()
			req.get_subject().C = kwargs['country']
			req.get_subject().ST = kwargs['state']
			req.get_subject().L = kwargs['city']
			req.get_subject().O = kwargs['organization']
			req.get_subject().OU = kwargs['unit']
			req.get_subject().CN = kwargs['cn']
			req.get_subject().emailAddress = kwargs['email']
			req.set_pubkey(priv_key)
			req.sign(priv_key, 'sha512')

			certificate = X509()
			certificate.set_serial_number(serialnumber)
			certificate.gmtime_adj_notBefore(0)
			certificate.gmtime_adj_notAfter(kwargs['expires'])
			certificate.set_issuer(kwargs['ca'].cert.get_subject())
			certificate.set_subject(req.get_subject())
			certificate.set_pubkey(req.get_pubkey())
			certificate.sign(kwargs['ca'].key, 'sha512')

		cert_dump = dump_certificate(FILETYPE_PEM, certificate)
		key_dump = dump_privatekey(FILETYPE_PEM, priv_key)

		if not os.path.isdir(os.path.abspath(os.path.dirname(key_file))):
			os.makedirs(os.path.abspath(os.path.dirname(key_file)))

		if not kwargs['cert_file']:
			with open(key_file, 'wb') as fh:
				fh.write(cert_dump)
				fh.write(key_dump)
		else:
			with open(key_file, 'wb') as fh:
				fh.write(key_dump)
			with open(kwargs['cert_file'], 'wb') as fh:
				fh.write(cert_dump)

		return priv_key, certificate

class InvalidFrame(BaseException):
	pass

class slimHTTP_Error(BaseException):
	pass

class ModuleError(BaseException):
	pass

class ConfError(BaseException):
	def __init__(self, message):
		print(f'[Warn] {message}')

class NotYetImplemented(BaseException):
	def __init__(self, message):
		print(f'[Warn] {message}')

class UpgradeIssue(BaseException):
	def __init__(self, message):
		print(f'[Error] {message}')

class Events():
	"""
	Events.<CONST> is a helper class to indicate which event is triggered.
	Events are passed up through the event chain deep from within slimHTTP.

	These events can be caught in your main `.poll()` loop, and react to different events.
	"""
	SERVER_ACCEPT = 0b10000000
	SERVER_CLOSE = 0b10000001
	SERVER_RESTART = 0b00000010

	CLIENT_DATA = 0b01000000
	CLIENT_REQUEST = 0b01000001
	CLIENT_RESPONSE_DATA = 0b01000010
	CLIENT_UPGRADED = 0b01000011
	CLIENT_UPGRADE_ISSUE = 0b01000100
	CLIENT_URL_ROUTED = 0b01000101
	CLIENT_DATA_FRAGMENTED = 0b01000110
	CLIENT_RESPONSE_PROXY_DATA = 0b01000111

	WS_CLIENT_DATA = 0b11000000
	WS_CLIENT_REQUEST = 0b11000001
	WS_CLIENT_COMPLETE_FRAME = 0b11000010
	WS_CLIENT_INCOMPLETE_FRAME = 0b11000011
	WS_CLIENT_ROUTING = 0b11000100
	WS_CLIENT_ROUTED = 0b11000101
	WS_CLIENT_RESPONSE = 0b11000110

	NOT_YET_IMPLEMENTED = 0b00000000
	INVALID_DATA = 0b00000001

	DATA_EVENTS = (CLIENT_RESPONSE_DATA, CLIENT_URL_ROUTED, CLIENT_RESPONSE_PROXY_DATA, WS_CLIENT_RESPONSE)

	def convert(_int):
		def_map = {v: k for k, v in Events.__dict__.items() if not k.startswith('__') and k != 'convert'}
		return def_map[_int] if _int in def_map else None

class _Sys():
	modules = {}
class VirtualStorage():
	def __init__(self):
		self.sys = _Sys()
virtual = VirtualStorage()

class Imported():
	"""
	A wrapper around absolute-path-imported via string modules.
	Supports context wrapping to catch errors.

	Will partially reload *most* of the code in the module in runtime.
	Certain things won't get reloaded fully (this is a slippery dark slope)
	"""
	def __init__(self, server, path, import_id, spec, imported):
		self.server = server
		self.path = path
		self.import_id = import_id # For lookups in virtual.sys.modules
		self.spec = spec
		self.imported = imported
		self.instance = None

	def __enter__(self, *args, **kwargs):
		"""
		It's important to know that it does cause a re-load of the module.
		So any persistant stuff **needs** to be stowewd away.

		Session files *(`pickle.dump()`)* is a good option, or god forbig `__builtin__['storage'] ...` is an option for in-memory stuff.
		"""
		try:
			self.instance = self.spec.loader.exec_module(self.imported)
		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			self.server.log(f'Gracefully handled module error in {self.path}: {e}')
			self.server.log(traceback.format_exc())
			raise ModuleError(traceback.format_exc())
		return self

	def __exit__(self, *args, **kwargs):
		# TODO: https://stackoverflow.com/questions/28157929/how-to-safely-handle-an-exception-inside-a-context-manager
		if len(args) >= 2 and args[1]:
			raise args[1]

class ROUTE_HANDLER():
	"""
	Stub function that will act as a gateway between
	@http.<function> and the in-memory route that is stored.

	I might be using annotations wrong, but this will store
	a route (/url/something) and connect it with a given function
	by the programmer.
	"""
	def __init__(self, route):
		self.route = route
		self.parser = None

	def gateway(self, f):
		self.parser = f

class HTTP_RESPONSE():
	def __init__(self, headers={}, payload=b'', *args, **kwargs):
		self.headers = headers
		self.payload = payload
		self.args = args
		self.kwargs = kwargs
		if not 'ret_code' in self.kwargs: self.kwargs['ret_code'] = 200

		self.ret_code_mapper = {200 : b'HTTP/1.1 200 OK\r\n',
								206 : b'HTTP/1.1 206 Partial Content\r\n',
								301 : b'HTTP/1.0 301 Moved Permanently\r\n',
								307 : b'HTTP/1.1 307 Temporary Redirect\r\n',
								302 : b'HTTP/1.1 302 Found\r\n',
								404 : b'HTTP/1.1 404 Not Found\r\n',
								418 : b'HTTP/1.0 I\'m a teapot\r\n'}

	def build_headers(self):
		x = b''
		if 'ret_code' in self.kwargs and self.kwargs['ret_code'] in self.ret_code_mapper:
			x += self.ret_code_mapper[self.kwargs['ret_code']]
		else:
			return b'HTTP/1.1 500 Internal Server Error\r\n\r\n'

		if not 'content-length' in [key.lower() for key in self.headers.keys()]:
			self.headers['Content-Length'] = str(len(self.payload))

		for key, val in self.headers.items():
			if type(key) != bytes: key = bytes(key, 'UTF-8')
			if type(val) != bytes: val = bytes(val, 'UTF-8')
			x += key + b': ' + val + b'\r\n'
		
		return x + b'\r\n'

	def clean_payload(self):
		tmp = {k.lower(): v for k,v in self.headers.items()}
		if 'content-type' in tmp and tmp['content-type'] == 'application/json' and type(self.payload) not in (bytes, str):
			self.payload = json.dumps(self.payload)
		if type(self.payload) != bytes:
			self.payload = bytes(self.payload, 'UTF-8') # TODO: Swap UTF-8 for a configurable encoding..

	def build(self):
		self.clean_payload()
		ret = self.build_headers()
		ret += self.payload
		return ret

class HTTP_SERVER():
	"""
	HTTP_SERVER is normally instanciated with :py:meth:`slimhttpd.host` which would
	safely spin up a HTTP / HTTPS server with all the correct arguments.

	In case of manual control, this class is the main server instance in charge
	of keeping the `"addr":port` open and accepting new connections. It contains a main
	event loop, which can be polled in order to accept new clients.

	It's also in charge of polling client identities for new events and lift them up
	to the caller of :py:func:`slimhttpd.HTTP_SERVER.poll`.
	"""
	def __init__(self, *args, **kwargs):
		"""
		`__init__` takes ambigious arguments through `**kwargs`.
		They are passed down to `HTTP_SERVER.config` transparently and used later.

		Some values are used upon `__init__` however, since they are part of the
		initiation process, those arguments are:

		:param addr: Address to listen on, default `0.0.0.0`.
		:type addr: str
		:param port: Port to listen on, default `80` unless HTTPS mode, in which case default is `443`.
		:type port: int
		"""
		self.default_port = 80
		if not 'port' in kwargs: kwargs['port'] = self.default_port
		if not 'addr' in kwargs: kwargs['addr'] = ''

		self.config = {**self.default_config(), **kwargs}
		self.allow_list = None
		## If config doesn't pass inspection, raise the error message given by check_config()
		if (config_error := self.check_config(self.config)) is not True:
			raise config_error

		self.sockets = {}
		self.setup_socket()
		self.main_sock_fileno = self.sock.fileno()
		
		self.pollobj = epoll()
		self.pollobj.register(self.main_sock_fileno, EPOLLIN)

		self.sock.listen(10)

		self.upgraders = {}
		self.on_upgrade_pre_func = None
		self.methods = {
			b'GET' : self.GET_func
		}
		self.routes = {
			None : {} # Default vhost routes
		}

		# while drop_privileges() is None:
		# 	log('Waiting for privileges to drop.', once=True, level=5, origin='slimHTTP', function='http_serve')

	def setup_socket(self):
		self.sock = socket()
		self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		try:
			self.sock.bind((self.config['addr'], self.config['port']))
			self.log(f"Bound to {self.config['addr']}:{self.config['port']}")
		except:
			raise slimHTTP_Error(f'Address already in use: {":".join((self.config["addr"], str(self.config["port"])))}')

	def log(self, *args, **kwargs):
		"""
		A simple print wrapper, placeholder for more advanced logging in the future.
		Joins any `*args` together and safely calls :func:'str' on each argument.
		"""
		print('[LOG] '.join([str(x) for x in args]))

		# TODO: Dump raw requests/logs to a .pcap:  (Optional, if scapy is precent)
		# 
		# from scapy.all import wrpcap, Ether, IP, UDP
		# packet = Ether() / IP(dst="1.2.3.4") / UDP(dport=123)
		# wrpcap('foo.pcap', [packet])

	def check_config(self, conf):
		"""
		Makes sure that the given configuration *(either upon startup via `**kwargs` or
		during annotation override of configuration (`@http.configuration`))* is correct.

		#TODO: Verify that 'proxy' mode endpoints aren't ourself, because that **will** hand slimHTTP. (https://github.com/Torxed/slimHTTP/issues/11)

		:param conf: Dictionary representing a valid configuration. #TODO: Add a doc on documentation :P
		:type conf: dict
		"""
		if not 'web_root' in conf: return ConfError('Missing "web_root" in configuration.')
		if not 'index' in conf: return ConfError('Missing "index" in configuration.')
		if not 'port' in conf: conf['port'] = self.default_port
		if not 'addr' in conf: conf['addr'] = ''
		if 'vhosts' in conf:
			for host in conf['vhosts']:
				if 'proxy' in conf['vhosts'][host]:
					if not ':' in conf['vhosts'][host]['proxy']: return ConfError(f'Missing port number in proxy definition for vhost {host}: "{conf["vhosts"][host]["proxy"]}"')
					continue
				if 'module' in conf['vhosts'][host]:
					if not os.path.isfile(conf['vhosts'][host]['module']): return ConfError(f"Missing module for vhost {host}: {os.path.abspath(conf['vhosts'][host]['module'])}")
					if not os.path.splitext(conf['vhosts'][host]['module'])[1] == '.py': return ConfError(f"vhost {host}'s module is not a python module: {conf['vhosts'][host]['module']}")
					continue
				if not 'web_root' in conf['vhosts'][host]: return ConfError(f'Missing "web_root" in vhost {host}\'s configuration.')
				if not 'index' in conf['vhosts'][host]: return ConfError(f'Missing "index" in vhost {host}\'s configuration.')
		return True

	def unregister(self, identity):
		"""
		Unregisters a :py:class:`slimhttpd.HTTP_CLIENT_IDENTITY`  s socket by calling `self.pollobj.unregister`
		on the client identity socket fileno.

		:param identity: Any valid `*_CLIENT_IDENTITY` handler.
		:type identity: :py:class:`slimhttpd.HTTP_CLIENT_IDENTITY` or :py:class:`spiderWeb.WS_CLIENT_IDENTITY`
		"""
		self.pollobj.unregister(identity.fileno)

	def default_config(self):
		"""
		Returns a simple but sane default configuration in case no one is given.
		Defaults to hosting the `web_root` to the `/srv/http` folder.

		:return: {'web_root' : '/srv/http', 'index' : 'index.html', 'vhosts' : { }, 'port' : 80}
		:rtype: dict
		"""
		return {
			'web_root' : '/srv/http',
			'index' : 'index.html',
			'vhosts' : {
				
			},
			'port' : 80
		}

	def configuration(self, config=None, *args, **kwargs):
		"""
		A decorator which can be set with a `@http.configuration` annotation as well as directly called.
		Using the decorator leaves some room for processing configuration before being returned
		to this function, in cases where configuration-checks needs to be isolated to a function
		in order to make the code neat.::


			@app.configuration
			def config():
				return {
					"web_root" : "./web-root",
					"index" : "index.html"
				}

		.. warning::
			The following hook would be called after socket setup.
			There is there for no point in adding `addr` or `port` to this configuration as the socket
			layer has already been set up.

		:param config: Dictionary representing a valid configuration which will be checked with :py:func:`slimhttpd.HTTP_SERVER.check_config`.
		:type config: dict
		"""
		# TODO: Merge instead of replace config?
		if type(config) == dict:
			self.config = config
		elif config:
			staging_config = config(instance=self)
			if self.check_config(staging_config) is True:
				self.config = staging_config

	def GET(self, f, *args, **kwargs):
		self.methods[b'GET'] = f

	def GET_func(self, request):
		return self.local_file(request)

	def REQUESTED_METHOD(self, request):
		# If the request *ends* on a /
		# replace it with the index file from either vhosts or default to anything if vhosts non existing.
		if request.headers[b'URL'][-1] == '/':
			if request.vhost and 'index' in self.config['vhosts'][request.vhost]:
				index_files = self.config['vhosts'][self.vhost]['index']
				if (_ := request.locate_index_file(index_files, return_any=False)):
					self.headers[b'URL'] += _
		if request.headers[b'URL'][-1] == '/':
			request.headers[b'URL'] += request.locate_index_file(self.config['index'], return_any=True)

		if request.headers[b'METHOD'] in self.methods:
			return self.methods[request.headers[b'METHOD']](request)

	def local_file(self, request):
		path = request.headers[b'URL']
		extension = os.path.splitext(path)[1]
		if extension == '.py':
			if isfile(f'{request.web_root}/{path}'):
				if (handle := handle_py_request(f'{request.web_root}/{path}')):

					response = handle.process(request)
					if response:
						if len(response) == 1: response = {}, response # Assume payload, and pad with headers
						respond_headers, response = response

						if respond_headers:
							if b'_code' in respond_headers:
								request.ret_code = respond_headers[b'_code']
								del(respond_headers[b'_code']) # Ugly hack.. Don't like.. TODO! Fix!
							for header in respond_headers:
								request.response_headers[header] = respond_headers[header]

							if not b'Content-Type' in respond_headers:
								request.response_headers[b'Content-Type'] = b'text/html'

						else:
							request.response_headers[b'Content-Type'] = b'text/html'
				else:
					response = b''
					request.response_headers[b'Content-Type'] = b'plain/text'

				if not b'Content-Length' in request.response_headers:
					request.response_headers[b'Content-Length'] = bytes(str(len(response)), 'UTF-8')
				return response
			else:
				print(404)
				request.ret_code = 404
				data = None
		else:
			data = get_file(request)
			if data:
				request.ret_code, path, length, data = data
				mime = guess_type(path)[0] #TODO: Deviates from bytes pattern. Replace guess_type()
				if not mime and path[-4:] == '.iso': mime = 'application/octet-stream'
				if b'range' in request.headers:
					_, data_range = request.headers[b'range'].split(b'=',1)
					start, stop = [int(x) for x in data_range.split(b'-')]
					request.response_headers[b'Content-Range'] = bytes(f'bytes {start}-{stop}/{length}', 'UTF-8')
					request.ret_code = 206
				else:
					if mime == 'application/octet-stream':
						request.response_headers[b'Accept-Ranges'] = b'bytes'

				request.response_headers[b'Content-Type'] = bytes(mime, 'UTF-8') if mime else b'plain/text'
				request.response_headers[b'Content-Length'] = bytes(str(len(data)), 'UTF-8')
			else:
				request.ret_code = 404
				data = None

		return data

	def allow(self, allow_list, *args, **kwargs):
		staging_list = []
		for item in allow_list:
			if '/' in item:
				staging_list.append(ipaddress.ip_network(item, strict=False))
			else:
				staging_list.append(ipaddress.ip_address(item))
		self.allow_list = set(staging_list)
		return self.on_accept_callback

	def on_accept_callback(self, f, *args, **kwargs):
		if f:
			self.on_accept = f

	def on_accept(self, f, *args, **kwargs):
		self.on_accept_func = f

	def on_accept_func(self, socket, ip, source_port, *args, **kwargs):
		return HTTP_CLIENT_IDENTITY(self, socket, ip, source_port, on_close=self.on_close_func)

	def on_close(self, f, *args, **kwargs):
		self.on_close_func = f

	def on_upgrade(self, f, *args, **kwargs):
		self.on_upgrade_func = f

	def on_upgrade_func(self, request, *args, **kwargs):
		return None

	# def on_upgrade(self, methods, *args, **kwargs):
	#	self.upgraders = {**self.upgraders, **methods}
	#	return self.on_upgrade_router

	# def on_upgrade_router(self, f, *args, **kwargs):
	#	self.on_upgrade_pre_func = f

	# def on_upgrade_func(self, request, *args, **kwargs):
	#	if self.on_upgrade_pre_func:
	#		if self.on_upgrade_pre_func(request):
	#			return None
	#
	#	if (upgrader := request.headers[b'upgrade'].lower().decode('UTF-8')) in self.upgraders:
	#		return self.upgraders[upgrader](request)

	def on_close_func(self, CLIENT_IDENTITY, *args, **kwargs):
		self.pollobj.unregister(CLIENT_IDENTITY.fileno)
		CLIENT_IDENTITY.socket.close()
		del(self.sockets[CLIENT_IDENTITY.fileno])

	# @route
	def route(self, url, vhost=None, *args, **kwargs):
		"""
		A decorator for statically define HTTP request path's::

			@app.route('/auth/login')
			def route_handler(request):
				print(request.headers)

		.. note:: The above example will handle both GET and POST (any user-defined method actually)

		:param timeout: is in seconds
		:type timeout: integer
		:param fileno: Limits the return events to a specific socket/client fileno.
		:type fileno: integer
		:return: `tuple(Events.<type>, EVENT_DATA)`
		:rtype: iterator
		"""
		if not vhost in self.routes: self.routes[vhost] = {}

		self.routes[vhost][url] = ROUTE_HANDLER(url)
		return self.routes[vhost][url].gateway

	def process_new_client(self, socket, address):
		return socket, address

	def poll(self, timeout=0.2, fileno=None):
		"""
		poll is to be called from the main event loop. poll will process any queues
		in need of processing, such as accepting new clients and check for data in
		any of the poll-objects (client sockets/identeties). A basic example of a main event loop would be::


			import slimhttpd

			http = slimhttpd.host(slimhttpd.HTTP)

			while 1:
				for event, *event_data in http.poll():
					pass

		:param timeout: is in seconds
		:type timeout: integer
		:param fileno: Limits the return events to a specific socket/client fileno.
		:type fileno: integer
		:return: `tuple(Events.<type>, EVENT_DATA)`
		:rtype: iterator
		"""
		for left_over in list(self.sockets):
			if left_over in self.sockets and self.sockets[left_over].has_data():
				yield self.do_the_dance(left_over)

		for socket_fileno, event_type in self.pollobj.poll(timeout):
			if fileno:
				if socket_fileno == fileno:
					yield (socket_fileno, event_type)
			else:
				if socket_fileno == self.main_sock_fileno:
					client_socket, client_address = self.sock.accept()
					try:
						client_socket, client_address = self.process_new_client(client_socket, client_address)
					except Exception as e:
						self.log(e)
						client_socket.close()
						continue

					client_fileno = client_socket.fileno()
					ip_address = ipaddress.ip_address(client_address[0])
					
					## Begin the allow/deny process
					allow = True
					if self.allow_list:
						allow = False
						for net in self.allow_list:
							if ip_address in net or ipaddress == net:
								allow = True
								break

					if not allow:
						print(client_address[0], 'not in allow_list')
						client_socket.close()
						continue

					identity = self.on_accept_func(socket=client_socket, ip=client_address[0], source_port=client_address[1])
					if not identity:
						identity = HTTP_CLIENT_IDENTITY(self, client_socket, client_address, on_close=self.on_close_func)

					self.sockets[client_fileno] = identity
					self.pollobj.register(client_fileno, EPOLLIN)
					yield (Events.SERVER_ACCEPT, identity)
				else:
					## Check for data
					for client_event, *client_event_data in self.sockets[socket_fileno].poll(timeout, force_recieve=True):
						yield (client_event, client_event_data) # Yield "we got data" event

						if client_event == Events.CLIENT_DATA: # Data = data that needs to be parsed
							yield self.do_the_dance(socket_fileno)

	def do_the_dance(self, fileno):
		#self.log(f'Parsing request & building reponse events for client: {self.sockets[fileno]}')
		for parse_event, *client_parsed_data in self.sockets[fileno].build_request():
			yield (parse_event, client_parsed_data)

			if parse_event == Events.CLIENT_REQUEST:
				for response_event, *client_response_data in client_parsed_data[0].parse():
					yield (response_event, client_response_data)

					if response_event in Events.DATA_EVENTS and client_response_data:
						if fileno in self.sockets:
							## TODO: Dangerous to dump dictionary data without checking if the client is HTTP or WS identity?

							## Temporary: Adding a dict inspector for data, since
							## websockets support it and HTTP does as well if we convert it..
							## In the futgure, each CLIENT_IDENTITY object should be responsible for converting the data.
							## But that would mean that HTTP_CLIENT_IDENTITY and WS_CLIENT_IDENTITY from slimWS would both
							## require identical `.send()` endpoints.
							if type(client_response_data[0]) is dict:
								self.sockets[fileno].send(bytes(json.dumps(client_response_data[0], default=json_serial), 'UTF-8'))
							elif type(client_response_data[0]) is bytes:
								self.sockets[fileno].send(client_response_data[0])
							elif type(client_response_data[0]) is HTTP_RESPONSE:
								self.sockets[fileno].send(client_response_data[0].build())
						else:
							break # The client has already recieved data, and was not setup for continius connections. so Keep-Alive has kicked in.

					if fileno in self.sockets:
						if not self.sockets[fileno].keep_alive:
							self.sockets[fileno].close()
	def run(self):
		while 1:
			for event, *event_data in self.poll():
				pass

class HTTPS_SERVER(HTTP_SERVER):
	def __init__(self, *args, **kwargs):
		self.default_port = 443
		if not 'port' in kwargs: kwargs['port'] = self.default_port
		HTTP_SERVER.__init__(self, *args, **kwargs)


	def check_config(self, conf):
		if not os.path.isfile(conf['ssl']['cert']):
			raise ConfError(f"Certificate for HTTPS does not exist: {conf['ssl']['cert']}")
		if not os.path.isfile(conf['ssl']['key']):
			raise ConfError(f"Keyfile for HTTPS does not exist: {conf['ssl']['key']}")
		return HTTP_SERVER.check_config(self, conf)

	def default_config(self):
		"""
		Returns a simple but sane default configuration in case no one is given.
		Defaults to hosting the `web_root` to the `/srv/http` folder.

		:return: {'web_root' : '/srv/http', 'index' : 'index.html', 'vhosts' : { }, 'port' : 443}
		:rtype: dict
		"""
		## TODO: generate cert if not existing.
		return {
			'web_root' : '/srv/http',
			'index' : 'index.html',
			'vhosts' : {
				
			},
			'port' : 443,
			'ssl' : {
				'cert' : 'cert.pem',
				'key' : 'key.pem'
			}
		}

	def setup_socket(self):
		self.sock = socket()
		self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		#self.sock = 
		try:
			self.sock.bind((self.config['addr'], self.config['port']))
			self.log(f"Bound to {self.config['addr']}:{self.config['port']}")
		except:
			raise slimHTTP_Error(f'Address already in use: {":".join((self.config["addr"], str(self.config["port"])))}')

	def certificate_verification(self, conn, cert, errnum, depth, ret_code):
		cert_hash = cert.get_subject().hash()
		cert_info = dict(cert.get_subject().get_components())
		cert_serial = cert.get_serial_number()
		
		# cert = ['_from_raw_x509_ptr', '_get_boundary_time', '_get_name', '_issuer_invalidator', '_set_boundary_time', '_set_name', '_subject_invalidator', '_x509', 'add_extensions', 'digest', 'from_cryptography', 'get_extension', 'get_extension_count', 'get_issuer', 'get_notAfter', 'get_notBefore', 'get_pubkey', 'get_serial_number', 'get_signature_algorithm', 'get_subject', 'get_version', 'gmtime_adj_notAfter', 'gmtime_adj_notBefore', 'has_expired', 'set_issuer', 'set_notAfter', 'set_notBefore', 'set_pubkey', 'set_serial_number', 'set_subject', 'set_version', 'sign', 'subject_name_hash', 'to_cryptography']
		if cert_info[b'CN'] == b'Some Common Name':
			return True
		return False

	def process_new_client(self, socket, address):
		context = SSL.Context(SSL.TLSv1_2_METHOD) # TLSv1_METHOD
		context.set_verify(SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT, self.certificate_verification)
		context.set_verify_depth(9)

		#context.verify_mode = ssl.CERT_REQUIRED # CERT_OPTIONAL # CERT_REQUIRED
		#context.load_cert_chain(self.cert, self.key)
		context.use_privatekey_file(self.config['ssl']['key'])
		context.use_certificate_file(self.config['ssl']['cert'])
		context.set_default_verify_paths()

		context.set_mode(SSL.MODE_RELEASE_BUFFERS)
		# openssl x509 -noout -hash -in cert.pem
		# openssl version -d (place certs here or load manually)
		context.load_verify_locations(None, capath='./certs/')
		store = context.get_cert_store()
		for cert in glob.glob('./certs/*.cer'):
			x509 = crypto.load_certificate(cert)
			store.add_cert(x509)
		#	context.load_verify_locations(cafile=cert)

		socket = SSL.Connection(context, socket)
		try:
			socket.set_accept_state()
		except:
			pass # Hard to emulate this in the mock function, so this function simply doesn't exist.

		return socket, address

class HTTP_CLIENT_IDENTITY():
	"""
	client identity passed as a reference.
	"""
	def __init__(self, server, socket, address, source_port, on_close=None):
		self.server = server
		self.socket = socket
		self.fileno = socket.fileno()
		self.buffer_size = 8192
		self.address = address
		self.source_port = source_port
		self.closing = False
		self.keep_alive = False

		self.buffer = b''

		if on_close: self.on_close = on_close

	def close(self):
		if not self.closing:
			self.on_close(self)
			self.closing = True

	def on_close(self, *args, **kwargs):
		self.closing = True
		self.server.on_close_func(self)

	def poll(self, timeout=0.2, force_recieve=False):
		"""
		@force_recieve: If the caller knows there's data, we can override
		the polling event and skip straight to data recieving.
		"""
		if force_recieve or list(self.server.poll(timeout, fileno=self.fileno)):
			try:
				d = self.socket.recv(self.buffer_size)
			except: # There's to many errors that can be thrown here for differnet reasons, SSL, OSError, Connection errors etc.
					# They all mean the same thing, things broke and the client couldn't deliver data accordingly so eject.
				d = ''

			if len(d) == 0:
				self.on_close(self)
				return None

			self.buffer += d
			yield (Events.CLIENT_DATA, len(self.buffer))

	def send(self, data):
		return self.socket.send(data)

	def build_request(self):
		try:
			yield (Events.CLIENT_REQUEST, HTTP_REQUEST(self))
		except Exception as e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			self.server.log(f'Fatal error in HTTP_REQUEST from {self}, {fname}@{exc_tb.tb_lineno}: {e}')
			self.server.log(traceback.format_exc())

	def has_data(self):
		if self.closing: return False
		return True if len(self.buffer) else False

	def __repr__(self):
		return f'<slimhttpd.HTTP_CLIENT_IDENTITY @ {self.address}:{self.source_port}>'

class HTTP_PROXY_REQUEST():
	"""
	Turns a HTTP Request into a Reverse Proxy request,
	based on :class:`~slimHTTP.HTTP_REQUEST` identifying the requested host
	to be a vhost with the appropriate `vhost` configuration for a reverse proxy.
	"""
	def __init__(self, CLIENT_IDENTITY, ORIGINAL_REQUEST):
		self.CLIENT_IDENTITY = CLIENT_IDENTITY
		self.ORIGINAL_REQUEST = ORIGINAL_REQUEST
		self.config = self.CLIENT_IDENTITY.server.config
		self.vhost = self.ORIGINAL_REQUEST.vhost

	def __repr__(self, *args, **kwargs):
		return f"<HTTP_PROXY_REQUEST client={self.CLIENT_IDENTITY} vhost={self.vhost}, proxy={self.config['vhosts'][self.vhost]['proxy']}>"

	def parse(self):
		poller = epoll()
		sock = socket()
		sock.settimeout(0.2)
		proxy, proxy_port = self.config['vhosts'][self.vhost]['proxy'].split(':',1)
		try:
			sock.connect((proxy, int(proxy_port)))
		except:
			# We timed out, or the proxy was to slow to respond.
			self.CLIENT_IDENTITY.server.log(f'{self} was to slow to connect/respond. Aborting proxy and sending back empty response to requester.')
			return None
		sock.settimeout(None)
		if 'ssl' in self.config['vhosts'][self.vhost] and self.config['vhosts'][self.vhost]['ssl']:
			context = ssl.create_default_context()
			sock = context.wrap_socket(sock, server_hostname=proxy)
		poller.register(sock.fileno(), EPOLLIN)
		sock.send(self.CLIENT_IDENTITY.buffer)
		self.CLIENT_IDENTITY.server.log(f'Request sent for: {self}')

		data_buffer = b''
		# TODO: this will lock the entire application,
		#       some how we'll have to improve this.
		#       But for small scale stuff this will do, at least for testing.
		while poller.poll(0.2):
			tmp = sock.recv(8192)
			if len(tmp) <= 0: break
			data_buffer += tmp
		poller.unregister(sock.fileno())
		sock.close()
		return data_buffer

class HTTP_REQUEST():
	"""
	General request formatter passed as an object throughout the event stack.
	"""
	def __init__(self, CLIENT_IDENTITY):
		""" A dummy parser that will return 200 OK on everything. """
		self.CLIENT_IDENTITY = CLIENT_IDENTITY
		self.headers = {}
		self.payload = b''
		self.ret_code = 200 # Default return code.
		self.ret_code_mapper = {200 : b'HTTP/1.1 200 OK\r\n',
								206 : b'HTTP/1.1 206 Partial Content\r\n',
								302 : b'HTTP/1.1 302 Found\r\n',
								404 : b'HTTP/1.1 404 Not Found\r\n',
								418 : b'HTTP/1.0 I\'m a teapot\r\n'}
		self.response_headers = {}
		self.web_root = self.CLIENT_IDENTITY.server.config['web_root']

		#print(self.CLIENT_IDENTITY.buffer)

	def build_request_headers(self, data):
		## Parse the headers
		if b'\r\n' in data:
			METHOD, header = data.split(b'\r\n',1)
			for item in header.split(b'\r\n'):
				if b':' in item:
					key, val = item.split(b':',1)
					self.headers[key.strip().lower()] = val.strip()
		else:
			METHOD, self.headers = data, {}

		if not b' ' in METHOD:
			raise InvalidFrame(f"An invalid method was given: {METHOD[:100]}")
		METHOD, URL, proto = METHOD.split(b' ', 2)
		URI_QUERY = {}
		if b'?' in URL:
			URL, QUERIES = URL.split(b'?', 1)
			for item in QUERIES.split(b'&'):
				if b'=' in item:
					k, v = item.split(b'=',1)
					URI_QUERY[k.lower()] = v

		self.headers[b'URL'] = URL.decode('UTF-8')
		self.headers[b'METHOD'] = METHOD
		self.headers[b'URI_QUERY'] = URI_QUERY

		self.vhost = None

	def locate_index_file(self, index_files, return_any=True):
		if type(index_files) == str:
			if isfile(self.web_root + self.headers[b'URL'] + index_files):
				return index_files
			if return_any:
				return index_files
		elif type(index_files) in (list, tuple):
			for file in index_files:
				if isfile(self.web_root + self.headers[b'URL'] + file):
					if not return_any:
						return file
					break
			if return_any:
				return file

	def build_headers(self):
		x = b''
		if self.ret_code in self.ret_code_mapper:
			x += self.ret_code_mapper[self.ret_code]# + self.build_headers() + (response if response else b'')
		else:
			return b'HTTP/1.1 500 Internal Server Error\r\n\r\n'

		for key, val in self.response_headers.items():
			if type(key) != bytes: key = bytes(key, 'UTF-8')
			if type(val) != bytes: val = bytes(val, 'UTF-8')
			x += key + b': ' + val + b'\r\n'
		
		return x + b'\r\n'

	def parse(self):
		"""
		Split the HTTP data into headers and body.
		"""
		if b'\r\n\r\n' in self.CLIENT_IDENTITY.buffer:
			header, remainder = self.CLIENT_IDENTITY.buffer.split(b'\r\n\r\n', 1) # Copy and split the data so we're not working on live data.
			#self.CLIENT_IDENTITY.server.log(f'Request being parsed: {header[:2048]} ({remainder[:2048]})')
			self.payload = b''

			try:
				self.build_request_headers(header)
			except InvalidFrame as e:
				return (Events.INVALID_DATA, e)

			if self.headers[b'METHOD'] == b'POST':
				if b'content-length' in self.headers:
					content_length = int(self.headers[b'content-length'].decode('UTF-8'))
					self.payload = remainder[:content_length]

					if len(self.payload) < content_length:
						return (Events.CLIENT_DATA_FRAGMENTED, self)

					self.CLIENT_IDENTITY.buffer = remainder[content_length:] # Add any extended data outside of Content-Length back to the buffer
				else:
					return (Events.NOT_YET_IMPLEMENTED, NotYetImplemented('POST without Content-Length isn\'t supported yet.'))

			_config = self.CLIENT_IDENTITY.server.config
			if b'host' in self.headers and 'vhosts' in _config and self.headers[b'host'].decode('UTF-8') in _config['vhosts']:
				self.vhost = self.headers[b'host'].decode('UTF-8')
				if 'web_root' in _config['vhosts'][self.vhost]:
					self.web_root = _config['vhosts'][self.vhost]['web_root']

			# Find suitable upgrades if any
			if {b'upgrade', b'connection'}.issubset(set(self.headers)) and b'upgrade' in self.headers[b'connection'].lower():
				requested_upgrade_method = self.headers[b'upgrade'].lower()
				new_identity = self.CLIENT_IDENTITY.server.on_upgrade_func(self)
				if new_identity:
					self.CLIENT_IDENTITY.server.log(f'{self.CLIENT_IDENTITY} has been upgraded to {new_identity}')
					self.CLIENT_IDENTITY.server.sockets[self.CLIENT_IDENTITY.fileno] = new_identity
					yield (Events.CLIENT_UPGRADED, new_identity)
				else:
					yield (Events.CLIENT_UPGRADE_ISSUE, UpgradeIssue(f'Could not upgrade client {self.CLIENT_IDENTITY} with desired upgrader: {requested_upgrade_method}'))
				return

			# Check for @app.route definitions (self.routes in the server object).
			elif self.vhost in self.CLIENT_IDENTITY.server.routes and self.headers[b'URL'] in self.CLIENT_IDENTITY.server.routes[self.vhost]:
				yield (Events.CLIENT_URL_ROUTED, self.CLIENT_IDENTITY.server.routes[self.vhost][self.headers[b'URL']].parser(self))

			# Check vhost specifics:
			if self.vhost:
				if 'proxy' in _config['vhosts'][self.vhost]:
					proxy_object = HTTP_PROXY_REQUEST(self.CLIENT_IDENTITY, self)
					yield (Events.CLIENT_RESPONSE_PROXY_DATA, proxy_object.parse())
				elif 'module' in _config['vhosts'][self.vhost]:
					absolute_path = os.path.abspath(_config['vhosts'][self.vhost]['module'])
					
					if not absolute_path in virtual.sys.modules:
						spec = importlib.util.spec_from_file_location(absolute_path, absolute_path)
						imported = importlib.util.module_from_spec(spec)
						
						import_id = uniqueue_id()
						virtual.sys.modules[absolute_path] = Imported(self.CLIENT_IDENTITY.server, absolute_path, import_id, spec, imported)
						sys.modules[import_id+'.py'] = imported

					try:
						with virtual.sys.modules[absolute_path] as module:
							# We have to re-check the @.route definition after the import, since it *might* have changed
							# due to imports being allowed to do @.route('/', vhost=this)
							if self.vhost in self.CLIENT_IDENTITY.server.routes and self.headers[b'URL'] in self.CLIENT_IDENTITY.server.routes[self.vhost]:
								yield (Events.CLIENT_URL_ROUTED, self.CLIENT_IDENTITY.server.routes[self.vhost][self.headers[b'URL']].parser(self))

							elif hasattr(module.imported, 'on_request'):
								yield (Events.CLIENT_RESPONSE_DATA, module.imported.on_request(self))
					except ModuleError:
						self.CLIENT_IDENTITY.close()
					return

			# Lastly, handle the request as one of the builtins (POST, GET)
			elif (response := self.CLIENT_IDENTITY.server.REQUESTED_METHOD(self)):
				self.CLIENT_IDENTITY.server.log(f'{self.CLIENT_IDENTITY} sent a "{self.headers[b"METHOD"].decode("UTF-8")}" request to path "[{self.web_root}/]{self.headers[b"URL"]} @ {self.vhost}"', level=5, source='HTTP_REQUEST.parse()')
				if type(response) == dict: response = json.dumps(response)
				if type(response) == str: response = bytes(response, 'UTF-8')
				yield (Events.CLIENT_RESPONSE_DATA, self.build_headers() + response if response else self.build_headers())
			#else:
			#	self.CLIENT_IDENTITY.server.log(f'Can\'t handle {self.headers[b"METHOD"]} method.')