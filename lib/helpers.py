import sys
import importlib.util
from os import urandom
from hashlib import sha512
from subprocess import Popen, STDOUT, PIPE

def _sys_command(cmd, opts=None, *args, **kwargs):
	if not opts: opts = {}
	if 'debug' in opts:
		print('[!] {}'.format(cmd))
	handle = Popen(cmd, shell='True', stdout=PIPE, stderr=STDOUT, stdin=PIPE, **kwargs)
	output = b''
	while handle.poll() is None:
		data = handle.stdout.read()
		if len(data):
			if 'debug' in opts:
				print(data.decode('UTF-8'), end='')
		#	print(data.decode('UTF-8'), end='')
			output += data
	data = handle.stdout.read()
	if 'debug' in opts:
		print(data.decode('UTF-8'), end='')
	output += data
	handle.stdin.close()
	handle.stdout.close()
	return output

# def _onliest_singleness(entropy_length=256):
def _gen_uid(entropy_length=256):
	return sha512(urandom(entropy_length)).hexdigest()

class _safedict(dict):
	def __init__(self, *args, **kwargs):
		args = list(args)
		self.debug = False
		for index, obj in enumerate(args):
			if type(obj) == dict:
				m = safedict()
				for key, val in obj.items():
					if type(val) == dict:
						val = safedict(val)
					m[key] = val

				args[index] = m

		super(safedict, self).__init__(*args, **kwargs)

	def __getitem__(self, key):
		if not key in self:
			self[key] = safedict()

		val = dict.__getitem__(self, key)
		return val

	def __setitem__(self, key, val):
		if type(val) == dict:
			val = safedict(val)
		dict.__setitem__(self, key, val)

	def dump(self, *args, **kwargs):
		copy = safedict()
		for key in self.keys():
			val = self[key]
			if type(key) == bytes and b'*' in key: continue
			elif type(key) == str and '*' in key: continue
			elif type(val) == dict or type(val) == safedict:
				val = val.dump()
				copy[key] = val
			else:
				copy[key] = val
		return copy

	def copy(self, *args, **kwargs):
		return super(safedict, self).copy(*args, **kwargs)

def _importer(path):
	old_version = False
	log(f'Request to import "{path}"', level=6, origin='importer')
	if path not in modules:
		## https://justus.science/blog/2015/04/19/sys.modules-is-dangerous.html
		try:
			#log(f'Loading API module: {path}', level=4, origin='importer')
			#importlib.machinery.SOURCE_SUFFIXES.append('') # empty string to allow any file
			spec = importlib.util.spec_from_file_location(path, path)
			if not spec:
				raise ModuleNotFoundError(f"No such module: {path}")
			modules[path] = importlib.util.module_from_spec(spec)
			spec.loader.exec_module(modules[path])
			#sys.modules[path[:-3]] = modules[path]
			sys.modules[path] = modules[path]
			# if desired: importlib.machinery.SOURCE_SUFFIXES.pop()
			#modules[path] = importlib.import_module(path, path)
		except (SyntaxError, ModuleNotFoundError, FileNotFoundError) as e:
			log(f'Failed to load API module ({e}): {path}', level=2, origin='importer')
			return None
	else:
		#log(f'Reloading API module: {path}', level=4, origin='importer')
		#for key in sys.modules:
		#	print(key, '=', sys.modules[key])
		try:
			raise SyntaxError('https://github.com/Torxed/ADderall/issues/11')
			## Important: these two are crucial elements
			#importlib.invalidate_caches()

			#print('Reloading:', modules[path])
			#importlib.reload(modules[path])
		except SyntaxError as e:
			old_version = True
			#log(f'Failed to reload API module ({e}): {path}', level=2, origin='importer')
	return old_version, modules[f'{path}']