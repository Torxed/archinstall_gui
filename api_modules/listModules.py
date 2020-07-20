import json
from os.path import isdir, isfile
from collections import OrderedDict as oDict

def on_request(frame):
	if '_module' in frame.data and frame.data['_module'] == 'listModules':
		yield {
			'modules' : oDict({
				'Harddrive' : {'required' : True, 'defaults' : {}},
				'Encryption' : {'required' : True, 'defaults' : {}},
				'Base OS' : {'required' : False, 'defaults' : {}},
				'Language' : {'required' : False, 'defaults' : {}},
				'Profiles' : {'required' : False, 'defaults' : {}},
				'Applications' : {'required' : False, 'defaults' : {}},
				'Users & Groups' : {'required' : False, 'defaults' : {}},
				'AUR Support' : {'required' : False, 'defaults' : {}},
			}),
			'_modules' : 'listModules'
		}
