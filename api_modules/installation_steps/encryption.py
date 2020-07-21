import json
from os.path import isdir, isfile

from lib.worker import spawn

import session

if 'harddrive' in session.steps:
	html = f"""
	<div class="padded_content flex_grow flex column">
		<h3>Disk Encryption <i>(Optional)</i></h3>

		<div class="note">
			<div class="noteHeader"><div class="noteIcon"></div><span>Note</span></div>
			<div class="noteBody">
				Disk encryption is optional, but if you value your local data <i>(including web browser history and logins)</i>, it's strongly
				adviced that disk encryption is enabled. The minimum system requirements for disk encryption increases to <div class="inlineCode">1 GB</div> of RAM.
			</div>
		</div>

		<div class="warning">
			<div class="warningHeader"><div class="noteIcon"></div><span>Warning</span></div>
			<div class="noteBody">
				The password prompt while unlocking a drive is always <div class="inlineCode">en_US.UTF-8</div>, keep this in mind if you choose a password with special characters, that when prompted during boot for a disk password, the passphrase will be inputted with US keyboard layout<a target="_blank" href="https://bbs.archlinux.org/viewtopic.php?id=173506">[1]</a>.
			</div>
		</div>

		<div class="form-area" id="form-area">
			<div class="input-form" id="input-form">
				<input type="text" id="disk_password" required autocomplete="off" />
				<label class="label">
					<span class="label-content">Enter a disk password</span>
				</label>
			</div>
		</div>
		
		<div class="buttons bottom" id="buttons">
			<button id="saveButton">Enable Disk Encryption</button>
			<button id="skipButton">Don't use disk encryption</button>
		</div>
	</div>
	"""
else:
	html = 'Previous step not completed.'

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
	disk_password = document.querySelector('#disk_password').value;

	socket.send({
		'_module' : 'installation_steps/encryption',
		'disk_password' : disk_password
	})
})

document.querySelector('#skipButton').addEventListener('click', function() {
	socket.send({
		'_module' : 'installation_steps/harddrive',
		'format' : true
	})
})
"""

def strap_in_the_basics_with_encryption(frame, disk_password, drive, worker, hostname='Archnistall', *args, **kwargs):
	frame.CLIENT_IDENTITY.send({
		'type' : 'notification',
		'source' : 'harddrive',
		'message' : f"Paritioning has started on <div class=\"inlineCode\">{session.information['drive']}</div>",
		'status' : 'active'
	})

	with archinstall.Filesystem(drive, archinstall.GPT) as fs:
		# Use partitioning helper to set up the disk partitions.
		fs.use_entire_disk('luks2')

		if drive.partition[1].size == '512M':
			raise OSError('Trying to encrypt the boot partition for petes sake..')
		
		frame.CLIENT_IDENTITY.send({
			'type' : 'notification',
			'source' : 'harddrive',
			'message' : 'Paritioning is done',
			'status' : 'complete'
		})

		frame.CLIENT_IDENTITY.send({
			'type' : 'notification',
			'source' : 'encryption',
			'message' : f"Encrypting <div class=\"inlineCode\">{drive.partition[1]}</div>",
			'status' : 'active'
		})

		drive.partition[0].format('fat32')
		# First encrypt and unlock, then format the desired partition inside the encrypted part.
		with archinstall.luks2(drive.partition[1], 'luksloop', disk_password) as unlocked_device:
			unlocked_device.format('btrfs')

			frame.CLIENT_IDENTITY.send({
				'type' : 'notification',
				'source' : 'encryption',
				'message' : f"Encryption is done.",
				'status' : 'complete'
			})
			
			session.handles['filesystem'] = fs
			session.handles['boot'] = drive.partition[0]
			session.handles['root'] = unlocked_device

			frame.CLIENT_IDENTITY.send({
				'type' : 'notification',
				'source' : 'base_os',
				'message' : 'Installing base operating system',
				'status' : 'active'
			})

			with archinstall.Installer(drive.partition[1], boot_partition=drive.partition[0], hostname=hostname) as installation:
				if installation.minimal_installation():
					installation.add_bootloader()

					session.steps['base_os'] = installation
					session.steps['base_os_worker'] = worker

def on_request(frame):
	if '_module' in frame.data and frame.data['_module'] == 'installation_steps/encryption':
		if not 'harddrive' in session.steps:
			yield {
				'status' : 'incomplete',
				'next' : 'harddrive',
				'_modules' : 'encryption'
			}
			return

		if not 'disk_password' in frame.data:
			yield {
				'html' : html,
				'javascript' : javascript,
				'_modules' : 'encryption'
			}
		else:
			print('Formatting with encryption on:', session.information['drive'])
			#fmt = spawn(frame, archinstall.format_disk, drive='drive', start='start', end='size', start_callback=notify_partitioning_started)
		"""
		else:
			## We got credentials to store, not just calling this module.
			if 'disk_password' in data['credentials'] and not 'formating' in progress:
				archinstall.args = archinstall.setup_args_defaults(archinstall.args) # Note: don't setup args unless disk password is present, since that might start formatting on drives and stuff
				archinstall.args['password'] = data['credentials']['disk_password']
				print(json.dumps(archinstall.args, indent=4))
			else:
				yield {
					'status' : 'failed',
					'message' : 'Can not set disk/root password after formatting has started.'
				}

			if 'hostname' in data['credentials']:
				archinstall.args['hostname'] = data['credentials']['hostname']

			if 'username' in data['credentials'] and data['credentials']['username']:
				archinstall.create_user(data['credentials']['username'], data['credentials']['password'], data['credentials']['groups'].split(' '))

			storage['credentials'] = data['credentials']
			notify_credentials_saved(fileno)

			yield {
				'status' : 'success',
				'next' : 'mirrors'
			}
		"""