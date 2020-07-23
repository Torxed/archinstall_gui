import json
from os.path import isdir, isfile

def on_request(frame):
	if '_module' in frame.data and frame.data['_module'] == 'sysinfo':
		yield {
			'sysinfo' : {
				'version' : 'v0.1',
				'licence' : 'free'
			}
		}
