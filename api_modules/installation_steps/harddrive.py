import json, time
from os.path import isdir, isfile

from dependencies import archinstall
from lib.worker import spawn
from lib.helpers import install_base_os

import session

html = """
<div class="padded_content flex_grow flex column">
	<h3>Hardware setup</h3>
	<span>Select which disk to install Arch Linux to:</span>
	<div class="note">
		<div class="noteHeader"><div class="noteIcon"></div><span>Note</span></div>
		<div class="noteBody">
			Formatting will not start until encryption has been selected or skipped.
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
		'source' : 'base_os',
		'message' : 'Installing base operating system',
		'status' : 'active'
	})
def notify_base_install_done(worker, *args, **kwargs):
	worker.frame.CLIENT_IDENTITY.send({
		'type' : 'notification',
		'source' : 'base_os',
		'message' : 'Base operating system is installed.',
		'status' : 'complete'
	})

# def notify_encryption_started(worker, *args, **kwargs):
#	worker.frame.CLIENT_IDENTITY.send({
#		'type' : 'notification',
#		'source' : 'hardware',
#		'message' : 'Encrypting hard drive.',
#		'status' : 'active'
#	})

# def notify_base_configuration_started(worker, *args, **kwargs):
#	worker.frame.CLIENT_IDENTITY.send({
#		'type' : 'notification',
#		'source' : 'base_os',
#		'message' : 'Configuring base OS.',
#		'status' : 'active'
#	})

# def notify_base_configuration(worker, *args, **kwargs):
#	worker.frame.CLIENT_IDENTITY.send({
#		'type' : 'notification',
#		'source' : 'base_os',
#		'message' : 'Base operating system has been configured.',
#		'status' : 'active'
#	})

# def notify_bootloader_completion(worker, *args, **kwargs):
#	worker.frame.CLIENT_IDENTITY.send({
#		'type' : 'notification',
#		'source' : 'base_os',
#		'message' : 'Bootloader installed successfully.',
#		'status' : 'active'
#	})

# def notify_root_pw(worker, *args, **kwargs):
#	print('Notify root_root_pw called. Sending reboot button!')
#	worker.frame.CLIENT_IDENTITY.send({
#		'type' : 'notification',
#		'source' : 'base_os',
#		'message' : '<div class="balloon">Installation complete, click here to <b class="reboot" onClick="reboot();">reboot!</b></div>',
#		'status' : 'complete'
#	})

#last_update = time.time() # We generally don't need this since we're pushing through localhost. But just to not spam he UI.
# def progressbar(worker, output, *args, **kwargs):
#	global last_update
#	if len(output.strip()) and time.time() - last_update > 0.5:
#		try:
#			output = output.decode('UTF-8').strip()
#			sockets[worker.client.sock.fileno()].send({
#				'type' : 'notification',
#				'source' : 'base_os',
#				'message' : str(output[:120]),
#				'status' : 'active'
#			})
#			last_update = time.time()
#		except:
#			pass

def notify_language_set(worker, *args, **kwargs):
	sockets[worker.client.sock.fileno()].send({
		'type' : 'notification',
		'source' : 'language',
		'message' : 'Language has been configured.',
		'status' : 'complete'
	})

def strap_in_the_basics(frame, drive, hostname='Archnistall', *args, **kwargs):
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
			'source' : 'base_os',
			'message' : 'Installing base operating system',
			'status' : 'active'
		})

		with archinstall.Installer(drive.partition[1], boot_partition=drive.partition[0], hostname=hostname) as installation:
			if installation.minimal_installation():
				installation.add_bootloader()

				session.steps['base_os'] = True

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
					'status' : 'success',
					'next' : 'encryption',
					'_modules' : 'harddrive' 
				}

		elif 'format' in frame.data:
			print('Formatting without encryption on:', session.information['drive'])
			strap_in = spawn(frame, strap_in_the_basics, drive=session.information['drive'], start_callback=notify_partitioning_started, callback=notify_base_install_done)
			
			yield {
				'status' : 'success',
				'next' : 'language', # base_os doesn't contain anything (yet)
				'_modules' : 'encryption' 
			}

			yield {
				'type' : 'notification',
				'source' : 'encryption',
				'message' : 'Encryption skipped',
				'status' : 'complete'
			}

		"""
			if 'dependencies' in data:
				for dependency in data['dependencies']:
					if not dependency in storage:
						yield {	
							'status' : 'failed',
							'message' : f"Dependency '{dependency}' is not met."
						}
						return None # Break

			storage['drive'] = data['hardware']['drive']
			storage['start'] = '512MiB'
			storage['size'] = '100%'

			archinstall.args['drive'] = storage['drive']
			archinstall.args['start'] = storage['start']
			archinstall.args['size'] = storage['size']
			
			print(json.dumps(archinstall.args, indent=4))

			if not storage['SAFETY_LOCK']:
				archinstall.cache_diskpw_on_disk()
				archinstall.close_disks()

				if not 'mirror_region' in storage or 'mirror_specific' in storage:
					## TODO: add geoip guessing, and run filter_mirrors_by_country_list([GEOIP_GUESSED])
					spawn(client, archinstall.re_rank_mirrors)

				fmt = spawn(client, archinstall.format_disk, drive='drive', start='start', end='size', start_callback=notify_partitioning_started)
				refresh = spawn(client, archinstall.refresh_partition_list, drive='drive', dependency=fmt)
				mkfs = spawn(client, archinstall.mkfs_fat32, drive='drive', partition='1', dependency=refresh)
				encrypt = spawn(client, archinstall.encrypt_partition, drive='drive', partition='2', keyfile='pwfile', start_callback=notify_encryption_started, dependency=mkfs)
				mount_luksdev = spawn(client, archinstall.mount_luktsdev, drive='drive', partition='2', keyfile='pwfile', dependency=encrypt)
				btrfs = spawn(client, archinstall.mkfs_btrfs, dependency=mount_luksdev)
				progress['formatting'] = spawn(client, archinstall.mount_mountpoints, drive='drive', bootpartition='1', callback=notify_partitioning_done, dependency=btrfs)
				progress['strap_in'] = spawn(client, archinstall.strap_in_base, on_output=progressbar, start_callback=notify_base_install_started, callback=notify_base_install_done, dependency=progress['formatting'])
				if not 'set_locale' in progress:
					progress['set_locale'] = spawn(client, archinstall.set_locale, fmt='en_US.UTF-8 UTF-8', callback=notify_language_set, dependency='strap_in')
				progress['configure_base_system'] = spawn(client, archinstall.configure_base_system, start_callback=notify_base_configuration_started, callback=notify_base_configuration, dependency=progress['strap_in'])
				progress['setup_bootloader'] = spawn(client, archinstall.setup_bootloader, callback=notify_bootloader_completion, dependency=progress['configure_base_system'])
				progress['set_root_pw'] = spawn(client, archinstall.set_password, callback=notify_root_pw, dependency=progress['setup_bootloader'], user='root', password=storage['credentials']['disk_password'])
				
			else:
				print('Emulating: Formatting drive:', storage['drive'])

			yield {
				'status' : 'success',
				'next' : 'base_os'
			}"""