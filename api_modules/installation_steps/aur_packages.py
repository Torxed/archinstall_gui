import json, time, os
import urllib.request

from dependencies import archinstall
from lib.worker import spawn
import session

html = """
<div class="padded_content flex_grow flex column">
	<h3>AUR Support & Packages</h3>
	<span>If you wish to set up a non-root account here and now, this section can do so.</span>

	<div class="note" id="base_os_wait">
		<div class="noteHeader"><div class="noteIcon"></div><span>Note</span></div>
		<div class="noteBody">
			AUR support will be added once the Base OS step is complete.
		</div>
	</div>

	<div class="note">
		<div class="noteHeader"><div class="noteIcon"></div><span>Note</span></div>
		<div class="noteBody">
			The <a target="_blank" href="https://wiki.archlinux.org/index.php/Arch_User_Repository">Arch User Repository</a> is a collection of <a target="_blank" href="https://aur.archlinux.org/packages/">AUR packages</a> driven by the community.<br>
			After activating AUR support, any of the listed AUR packages can be installed here.
		</div>
	</div>

	<div class="warning">
		<div class="warningHeader"><div class="noteIcon"></div><span>Warning</span></div>
		<div class="noteBody">
			<b>Use it at your own risk!</b><br>
			Be aware that these packages are not officially supported and therefore <b>can contain bugs, malicious code and/or break your system</b>.<br>
			<br>
		</div>
	</div>

	<div class="warning">
		<div class="warningHeader"><div class="noteIcon"></div><span>Warning</span></div>
		<div class="noteBody">
			<b>Use it at your own risk!</b><br>
			Once activated, AUR can not be disabled from the installer.<br>
			You would need to boot your installation and remove the package <div class="inlineCode">yay</div> manually.
			<br>
		</div>
	</div>

	<div class="form-area-oneline">
		<button id="activate_AUR">Activate AUR support</button>
	</div>

	<div class="form-area" id="form-area">
		<div class="input-form" id="input-form">
			<input type="text" id="package_list" required autocomplete="off" disabled />
			<label class="label disabled">
				<span class="label-content" id="lbl_content">AUR support currently disabled</span>
			</label>
		</div>
	</div>

	<div class="buttons bottom">
		<button id="install_packages">Install AUR packages</button>
		<button id="skip_accounts">Skip this step</button>
	</div>
</div>
"""

## TODO:
## Needs to be loaded this way, since we can't inject JS into divs etc in the HTML above.
javascript = """

document.querySelector('#activate_AUR').addEventListener('click', function() {
	document.querySelector('#package_list').disabled = false;
	document.querySelector('#lbl_content').innerHTML = "Space separated list of AUR packages to install.";
})

document.querySelector('#install_packages').addEventListener('click', function() {
	socket.send({
		'_module' : 'installation_steps/aur_packages',
		'packages' : document.querySelector('#package_list').value.split(" ")
	})
	document.querySelector('#package_list').disabled = false;
})

document.querySelector('#skip_accounts').addEventListener('click', function() {
	notification({
		'source' : 'aur_packages',
		'status' : 'skipped',
		'next' : 'install_log'
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
	if '_module' in frame.data and frame.data['_module'] == 'installation_steps/aur_packages':
		if not 'packages' in frame.data:
			yield {
				'html' : html,
				'javascript' : javascript,
				'_modules' : 'aur_packages'
			}
		else:
			print('Installing:', frame.data['packages'])
			yield {
				'status' : 'success',
				'_modules' : 'aur_packages',
				'next' : 'accounts'
			}