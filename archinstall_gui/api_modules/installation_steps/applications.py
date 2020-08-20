import json, time, os
import urllib.request

from dependencies import archinstall
from lib.worker import spawn
import session

html = """
<div class="padded_content flex_grow flex column">
	<h3>Additional applications</h3>
	<span>Here, you can install additional <a target="_blank" href="https://www.archlinux.org/packages/">Arch Linux packages</a>.</span>

	<div class="note" id="arch_linux_worker_wait">
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
	reboot_step = 'applications';

	socket.send({
		'_module' : 'installation_steps/applications',
		'applications' : document.querySelector('#package_list').value
	})
})

document.querySelector('#skip_templates').addEventListener('click', function() {
	socket.send({
		'_module' : 'installation_steps/applications',
		'skip' : true
	})
})

"""

def stub(*args, **kwargs):
	return True

def install_packages(frame, packages, worker, *args, **kwargs):
	return session.steps['arch_linux'].add_additional_packages(packages)

def notify_application_started(worker, *args, **kwargs):
	worker.frame.CLIENT_IDENTITY.send({
		'type' : 'notification',
		'source' : 'applications',
		'message' : 'Additional applications are being installed.',
		'status' : 'active'
	})

def notify_application_ended(worker, *args, **kwargs):
	worker.frame.CLIENT_IDENTITY.send({
		'type' : 'notification',
		'source' : 'applications',
		'message' : 'Additional applications have been installed.',
		'status' : 'complete'
	})

def on_request(frame):
	if '_module' in frame.data and frame.data['_module'] == 'installation_steps/applications':
		if 'skip' in frame.data:
			session.steps['applications'] = spawn(frame, stub, dependency='profiles')
			yield {
				'_modules' : 'applications',
				'status' : 'skipped',
				'next' : 'aur_packages'
			}
			return
		elif not 'applications' in frame.data:
			yield {
				'html' : html,
				'javascript' : javascript,
				'_modules' : 'applications'
			}
		else:
			session.steps['applications'] = spawn(frame, install_packages, packages=frame.data['applications'], start_callback=notify_application_started, callback=notify_application_ended, dependency='profiles')
			
			yield {
				'status' : 'queued',
				'_modules' : 'applications',
				'next' : 'aur_packages'
			}