import json
from os.path import isdir, isfile

class parser():
	def parse(path, client, data, headers, fileno, addr, *args, **kwargs):
		print(args, kwargs)
		if '_module' in data and data['_module'] == 'reboot':
			archinstall.reboot()