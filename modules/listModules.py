import json
from os.path import isdir, isfile
from collections import OrderedDict as oDict

class parser():
	def parse(path, client, data, headers, fileno, addr, *args, **kwargs):
		print(args, kwargs)
		if '_module' in data and data['_module'] == 'listModules':
			yield {
				'modules' : oDict({
					'credentials' : {'required' : True, 'defaults' : {}},
					'mirrors' : {'required' : False, 'defaults' : {}},
					'hardware' : {'required' : True, 'defaults' : {}},
					'base_os' : {'required' : False, 'defaults' : {}},
					'templates' : {'required' : False, 'defaults' : {}},
					'language' : {'required' : False, 'defaults' : {}}
				})
			}
