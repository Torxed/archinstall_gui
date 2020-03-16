import json, traceback, sys, os
from collections.abc import Iterator

class pre_parser():
	def __init__(self, *args, **kwargs):
		self.parsers = safedict()

	def parse(self, client, data, headers, fileno, addr, *args, **kwargs):
		## This little bundle of joy, imports python-modules based on what module is requested from the client.
		## If the reload has already been loaded once before, we'll invalidate the python module cache and
		## reload the same module so that if the code has changed on disk, it will now be executed with the new code.
		##
		## This prevents us from having to restart the server every time a API endpoint has changed.

		# If the data isn't JSON (dict)
		# And the data doesn't contain _module, !abort!
		if not type(data) in (dict, safedict) or ('_module' not in data and '_install_step' not in data):
			log(f'Invalid request data type or missing _module/_install_step in JSON data: {data}', level=3, origin='pre_parser', function='parse')
			return

		print(json.dumps(data, indent=4))

		## TODO: Add path security!
		if '_module' in data:
			loaded_module = data['_module']
			module_path = f"./modules/{data['_module']}.py"
		else:
			loaded_module = data['_install_step']
			module_path = f"./modules/installation_steps/{data['_install_step']}.py"
		import_result = importer(module_path)
		if import_result:
			old_version, handle = import_result

			# Just keep track if we're executing the new code or the old, for logging purposes only
			if not old_version:
				log(f'Calling {handle}.parser.parse(client, data, headers, fileno, addr, *args, **kwargs)', level=4, origin='pre_parser', function='parse')
			else:
				log(f'Calling old {handle}.parser.parse(client, data, headers, fileno, addr, *args, **kwargs)', level=3, origin='pre_parser', function='parse')

			try:
				response = modules[module_path].parser.parse(f'modules', client, data, headers, fileno, addr, *args, **kwargs)
				if response:
					if isinstance(response, Iterator):
						for item in response:
							yield {
								**item,
								'_id' : data['_id'] if '_id' in data else None,
								'_modules' : loaded_module
							}
					else:
						yield {
							**response,
							'_id' : data['_id'] if '_id' in data else None,
							'_modules' : loaded_module
						}
			except BaseException as e:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				log(f'Module error in {fname}@{exc_tb.tb_lineno}: {e} ', level=2, origin='pre_parser', function='parse')
				log(traceback.format_exc(), level=2, origin='pre_parser', function='parse')