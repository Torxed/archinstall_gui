import json, time
from os.path import isdir, isfile

from dependencies import archinstall
from lib.worker import spawn

import session

html = """
<div class="padded_content flex_grow flex column">
	<h3>Hardware setup</h3>
	<span>Select which disk to install Arch Linux to:</span>
	<div class="note">
		<div class="noteHeader"><div class="noteIcon"></div><span>Note</span></div>
		<div class="noteBody">
			Formatting will not start until mirrors have been selected in the third step.
		</div>
	</div>
	<select id="drives" class="flex_grow" size="3">
		
	</select>
	<div class="drive_information">

	</div>

	<div class="buttons bottom">
		<button id="select_disk">Select Disk</button>
	</div>
</div>
"""

## TODO:
## Needs to be loaded this way, since we can't inject JS into divs etc in the HTML above.
javascript = """
window.drives_dropdown = document.querySelector('#drives');

window.refresh_drives = () => {
	window.drives_dropdown.innerHTML = '';
	Object.keys(drives).forEach((drive) => {
		let option = document.createElement('option');
		option.value = drive;
		option.innerHTML = `${drive} (${drives[drive]['info']['size']}, ${drives[drive]['info']['label']}, ${drives[drive]['info']['mountpoint']})`;
		window.drives_dropdown.appendChild(option);
	})
}

window.drives_dropdown.addEventListener('change', function(obj) {
	selected_drive = this.value;

})

document.querySelector('#select_disk').addEventListener('click', function() {
	socket.send({
		'_module' : 'installation_steps/harddrive',
		'hardware' : {
			'drive' : selected_drive
		},
		'dependencies' : ['encryption']
	})
})

window.update_drives = (data) => {
	console.log(data);
	if(typeof data['drives'] !== 'undefined') {
		Object.keys(data['drives']).forEach((drive) => {
			drives[drive] = data['drives'][drive];
		})
		window.refresh_drives()
	}
}

if(socket.subscriptions('drive_list') != 2)
	socket.subscribe('drive_list', update_drives);

socket.send({
	'_module' : 'installation_steps/harddrive',
	'hardware' : 'refresh'
})

"""

def notify_partitioning_started(worker, *args, **kwargs):
	worker.frame.CLIENT_IDENTITY.send({
		'type' : 'notification',
		'source' : 'harddrive',
		'message' : f"Paritioning has started on <div class=\"inlineCode\">{session.information['drive']}</div>",
		'status' : 'active'
	})
def notify_partitioning_done(worker, *args, **kwargs):
	worker.frame.CLIENT_IDENTITY.send({
		'type' : 'notification',
		'source' : 'harddrive',
		'message' : 'Paritioning is done',
		'status' : 'complete'
	})
def notify_base_install_started(worker, *args, **kwargs):
	worker.frame.CLIENT_IDENTITY.send({
		'type' : 'notification',
		'source' : 'arch_linux',
		'message' : 'Installing base operating system',
		'status' : 'active'
	})
def notify_base_install_done(worker, *args, **kwargs):
	worker.frame.CLIENT_IDENTITY.send({
		'type' : 'notification',
		'source' : 'arch_linux',
		'message' : '<div class="balloon">Base installation complete.</div>',
		'status' : 'complete'
	})

def strap_in_the_basics(frame, drive, worker, hostname='Archnistall', *args, **kwargs):
	with archinstall.Filesystem(drive, archinstall.GPT) as fs:
		# Use partitioning helper to set up the disk partitions.
		fs.use_entire_disk('ext4')

		if drive.partition[1].size == '512M':
			raise OSError('Trying to encrypt the boot partition for petes sake..')

		drive.partition[0].format('fat32')
		drive.partition[1].format('ext4')

		session.handles['filesystem'] = fs
		session.handles['boot'] = drive.partition[0]
		session.handles['root'] = drive.partition[1]

		frame.CLIENT_IDENTITY.send({
			'type' : 'notification',
			'source' : 'harddrive',
			'message' : 'Paritioning is done',
			'status' : 'complete'
		})

		frame.CLIENT_IDENTITY.send({
			'type' : 'notification',
			'source' : 'arch_linux',
			'message' : 'Installing base operating system',
			'status' : 'active'
		})

		with archinstall.Installer(drive.partition[1], boot_partition=drive.partition[0], hostname=hostname) as installation:
			if installation.minimal_installation():
				installation.add_bootloader()

				session.steps['arch_linux'] = installation
				session.steps['arch_linux_worker'] = worker

	# Verified: Filesystem() doesn't do anything shady on __exit__
	#           other than sync being called.
	return True

def on_request(frame):
	if '_module' in frame.data and frame.data['_module'] == 'installation_steps/harddrive':
		if not 'hardware' in frame.data and 'format' not in frame.data:
			yield {
				'html' : html,
				'javascript' : javascript,
				'_modules' : 'harddrive'
			}
		elif 'hardware' in frame.data and frame.data['hardware'] == 'refresh':
			yield {
				'drives' : archinstall.all_disks(),
				'_modules' : 'drive_list'
			}
		elif 'hardware' in frame.data and type(frame.data['hardware']) == dict:
			if 'drive' in frame.data['hardware']:
				selected_drive = frame.data['hardware']['drive']
				session.information['drive'] = archinstall.all_disks()[selected_drive]
				session.steps['harddrive'] = True

				yield {
					'status' : 'queued',
					'next' : 'encryption',
					'_modules' : 'harddrive' 
				}

		elif 'format' in frame.data:
			if 'arch_linux' not in session.steps:
				session.steps['arch_linux'] = spawn(frame, strap_in_the_basics, drive=session.information['drive'], start_callback=notify_partitioning_started, callback=notify_base_install_done, dependency='mirrors')
				session.steps['encryption'] = True

				yield {
					'status' : 'success',
					'next' : 'mirrors', # arch_linux doesn't contain anything (yet)
					'_modules' : 'encryption' 
				}

				yield {
					'type' : 'notification',
					'source' : 'encryption',
					'message' : 'Encryption skipped',
					'status' : 'skipped'
				}