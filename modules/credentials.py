import json
from os.path import isdir, isfile
from collections import OrderedDict as oDict

class parser():
	def parse(path, client, data, headers, fileno, addr, *args, **kwargs):
		print(args, kwargs)
		if '_module' in data and data['_module'] == 'credentials':
			yield {
				'status' : 'success'
			}
