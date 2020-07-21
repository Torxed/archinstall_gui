import json, time, os
import urllib.request

from dependencies import archinstall
from lib.worker import spawn
import session

html = """
<div class="padded_content flex_grow flex column">
	<h3>Additional applications</h3>
	<span>Here, you can install additional <a target="_blank" href="https://www.archlinux.org/packages/">Arch Linux packages</a>.</span>

	<div class="note" id="base_os_wait">
		<div class="noteHeader"><div class="noteIcon"></div><span>Note</span></div>
		<div class="noteBody">
			The packages won't be installed until the Base OS is installed. But once that step is complete, your chosen packages will be installed.
		</div>
	</div>

	<div class="form-area" id="form-area">
		<div class="input-form" id="input-form">
			<input type="text" id="package_list" required autocomplete="off" />
			<label class="label">
				<span class="label-content">Space separated list of packages to install.</span>
			</label>
		</div>
	</div>

	<div class="buttons bottom">
		<button id="install_packages">Install packages</button>
		<button id="skip_templates">Skip this step</button>
	</div>
</div>
"""

## TODO:
## Needs to be loaded this way, since we can't inject JS into divs etc in the HTML above.
javascript = """

document.querySelector('#install_packages').addEventListener('click', function() {
	socket.send({
		'_module' : 'installation_steps/applications',
		'applications' : document.querySelector('#package_list').value.split(" ")
	})
})

document.querySelector('#skip_templates').addEventListener('click', function() {
	notification({
		'source' : 'applications',
		'status' : 'skipped',
		'next' : 'accounts'
	})
})

"""

def notify_template_installed(worker, *args, **kwargs):
	sockets[worker.client.sock.fileno()].send({
		'type' : 'notification',
		'source' : 'profiles',
		'message' : 'Template has been installed.',
		'status' : 'complete'
	})

def notify_template_started(worker, *args, **kwargs):
	sockets[worker.client.sock.fileno()].send({
		'type' : 'notification',
		'source' : 'profiles',
		'message' : 'Template is being installed',
		'status' : 'active'
	})

def request_input(key, *args, **kwargs):
	if key in storage['credentials']:
		return storage['credentials'][key]
	elif key in storage:
		return storage[key]
	return None

last_update = time.time() # We generally don't need this since we're pushing through localhost. But just to not spam he UI.
def progressbar(worker, output, *args, **kwargs):
	global last_update
	if len(output.strip()) and time.time() - last_update > 0.5:
		try:
			output = output.decode('UTF-8').strip()
			sockets[worker.client.sock.fileno()].send({
				'type' : 'notification',
				'source' : 'profiles',
				'message' : str(output[:120]),
				'status' : 'active'
			})
			last_update = time.time()
		except:
			pass

def on_request(frame):
	if '_module' in frame.data and frame.data['_module'] == 'installation_steps/applications':
		if not 'applications' in frame.data:
			yield {
				'html' : html,
				'javascript' : javascript,
				'_modules' : 'applications'
			}
		else:
			yield {
				'status' : 'success',
				'_modules' : 'applications',
				'next' : 'accounts'
			}
		"""
		elif 'template' in data:
			
			archinstall.instructions = archinstall.get_instructions(data['template'])
			archinstall.instructions = archinstall.merge_in_includes(archinstall.instructions)
			archinstall.cleanup_args(input_redirect=request_input)
			progress['install_template'] = spawn(client, archinstall.run_post_install_steps, dependency='setup_bootloader', on_output=progressbar, start_callback=notify_template_started, callback=notify_template_installed)
			if 'set_root_pw' in progress:
				log(f" --- Changing set_root_pw dependency to: {progress['install_template']}")
				log(f"Changing set_root_pw dependency to: {progress['install_template']}", level=3, origin='templates.parse')
				progress['set_root_pw'].kwargs['dependency'] = progress['install_template']
			else:
				print('--- No set_root_pw when running templates')

			yield {
					'status' : 'success',
					'next' : 'language'
				}
		"""

