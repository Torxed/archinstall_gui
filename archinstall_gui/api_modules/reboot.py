import json
from os.path import isdir, isfile

from dependencies import archinstall

def on_request(frame):
	if '_module' in frame.data and frame.data['_module'] == 'reboot':
		archinstall.reboot()