import json
from os.path import isdir, isfile

html = """
<div class="padded_content flex_grow flex column">
	<h3>Credentials</h3>
	<span>Here you'll configure a disk password, which will also be your initial root password. Any additional users can be set up here as well any time during the installation process. Simply come back here at any time to add or remove users.</span>
	<div class="form-area" id="form-area">
		<div class="input-form" id="input-form">
			<input type="password" id="disk_password" required autocomplete="off" />
			<label class="label">
				<span class="label-content">Disk password:</span>
			</label>
		</div>
	</div>
	<div class="form-area" id="form-area">
		<div class="input-form" id="input-form">
			<input type="text" id="hostname" required autocomplete="off" />
			<label class="label">
				<span class="label-content">Give this machine a hostname on the network <i>(optional)</i></span>
			</label>
		</div>
	</div>
	<div class="buttons bottom" id="buttons">
		<button id="saveButton">Save configuration</button>
	</div>
</div>
"""

javascript = """
window.disk_password_input = document.querySelector('#disk_password');
window.hostname_input = document.querySelector('#hostname');

if(disk_password) {
	disk_password_input.value = disk_password;
	disk_password_input.disabled = true;
}

if(hostname) {
	hostname_input.value = hostname;
}

document.querySelector('#saveButton').addEventListener('click', function() {
	if(!disk_password) {
		disk_password = document.querySelector('#disk_password').value;
	}

	if(!hostname) {
		hostname = document.querySelector('#hostname').value;
	}

	socket.send({
		'_install_step' : 'credentials',
		'credentials' : {
			'disk_password' : disk_password,
			'hostname' : hostname
		}
	})
})
"""

class parser():
	def parse(path, client, data, headers, fileno, addr, *args, **kwargs):
		if '_install_step' in data and data['_install_step'] == 'credentials':
			if not 'credentials' in data:
				yield {
					'html' : html,
					'javascript' : javascript
				}
			else:
				## We got credentials to store, not just calling this module.
				if len(data['credentials']) == 1 and not 'formating' in progress:
					archinstall.args = archinstall.setup_args_defaults(archinstall.args)

					print(json.dumps(archinstall.args, indent=4))

					storage['credentials'] = data['credentials']
					archinstall.args['password'] = storage['credentials']['disk_password']

					yield {
						'status' : 'success',
						'next' : 'hardware'
					}

				elif len(data['credentials']) == 1:
					yield {
						'status' : 'failed',
						'message' : 'Can not set disk/root password after formatting has started.'
					}
				else:
					for account in storage['credentials']:
						if account == 'disk_password' and 'formatting' in progress: continue

						print('Setting up account:', account)

					yield {
						'status' : 'success',
						'next' : 'hardware'
					}