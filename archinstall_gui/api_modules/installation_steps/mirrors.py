import json, time
import urllib.request
from os.path import isdir, isfile

from dependencies import archinstall
from lib.worker import spawn
import session

if 'encryption' in session.steps:
	html = f"""
		<div class="padded_content flex_grow flex column">
			<h3>Choose a mirror configuration <i>(Optional)</i></h3>
			
			<div class="warning">
				<div class="warningHeader"><div class="noteIcon"></div><span>Warning</span></div>
				<div class="noteBody">
					After pressing any button at the bottom, <div class="inlineCode">{session.information['drive']}</div> will be completely erased <i>(wiped/formatted)</i>.<br>
					<b>This action can not be undone!</b>
				</div>
			</div>

			<div class="note">
				<div class="noteHeader"><div class="noteIcon"></div><span>Note</span></div>
				<div class="noteBody">
					You can safely navigate in the left side menu without formatting any disks.
				</div>
			</div>

			<h3>Available mirrors</h3>
			<select id="mirrorlist" class="flex-grow" multiple>

			</select>

			<h3>Add a custom mirror</h3>
			<div class="form-area">
				<div class="input-form" id="input-form">
					<input type="text" id="mirror_name" required autocomplete="off" />
					<label class="label">
						<span class="label-content">Name of the mirror <i>(For instance: local_repo)</i>.</span>
					</label>
				</div>
			</div>
			<div class="form-area">
				<div class="input-form" id="input-form">
					<input type="text" id="mirror_url" required autocomplete="off" />
					<label class="label">
						<span class="label-content">URL to the custom mirror <i>(Ex: http://192.168.0.1/$repo/os/$arch)</i>.</span>
					</label>
				</div>
			</div>

			<div class="form-area oneliner">
				<select id="custom_signcheck">
					<option value="Never">Never</option>
					<option value="Optional">Optional</option>
					<option value="Required">Required</option>
				</select>

				<select id="custom_signoptions">
					<option value="TrustedOnly">TrustedOnly (default)</option>
					<option value="TrustAll">TrustAll</option>
				</select>
			</div>

			<div class="form-area">
				<div class="input-form" id="input-form">
					<button id="save_custom_mirror" class="flex-grow">Add mirror to available mirrors</button>
				</div>
			</div>

			<h3>Or use all mirrors from a specified region</h3>
			<div class="form-area">
				<div class="input-form" id="input-form">
					<input type="text" id="country_code" required autocomplete="off" />
					<label class="label">
						<span class="label-content">Write country code(s), separate with , <i>(Ex: SE,UK = Sweden and United Kingdom)</i>.</span>
					</label>
				</div>
			</div>

			<div class="buttons bottom">
				<button id="save_mirrors">Use selected mirrors <i>(and continue)</i></button>
				<button id="user_automatic_detection">Auto-detect closest mirrors <i>(and continue)</i></button>
				<button id="skip_step">Skip and use default mirrors</button>
			</div>
		</div>
	"""
else:
	html = 'Previous step <i>(encryption)</i> not completed.'

## TODO:
## Needs to be loaded this way, since we can't inject JS into divs etc in the HTML above.
javascript = """
document.querySelector('#save_mirrors').addEventListener('click', function() {
	let mirror_list = document.querySelector('#mirrorlist');
	
	var options = mirror_list.options, count = 0;
	for (var i=0; i < options.length; i++) {
		if (options[i].selected) count++;
	}

	if (count == 0) {
		popup('You need to select at least one mirror if you wish to use the selected mirrors option.');
		return;
	} else {
		let mirrors = [];
		Array.from(options).forEach(function(option_element) {
			let option_text = option_element.text;
			let option_value = option_element.value;
			let is_option_selected = option_element.selected;

			if (is_option_selected) {
				mirrors.push({'value' : option_value, 
							'country' : option_element.getAttribute('country'),
							'url' : option_element.getAttribute('url'),
							'signcheck' : option_element.getAttribute('signcheck'),
							'signoptions' : option_element.getAttribute('signoptions'),
							'name' : option_element.getAttribute('name')});
			}
		});

		socket.send({
			'_module' : 'installation_steps/mirrors',
			'mirrors' : {
				'region' : document.querySelector('#country_code').value,
				'selected_mirrors' : mirrors
			}
		})
	}
})

document.querySelector('#user_automatic_detection').addEventListener('click', function() {
	socket.send({
		'_module' : 'installation_steps/mirrors',
		'mirrors' : 'autodetect'
	})
})

document.querySelector('#skip_step').addEventListener('click', function() {
	socket.send({
		'_module' : 'installation_steps/mirrors',
		'skip' : true
	})
})

window.refresh_mirrorlist = () => {
	let mirrorlist_dropdown = document.querySelector('#mirrorlist');

	window.mirror_list['urls'].forEach((mirrorlist_info) => {
		if(!mirrorlist_info['active'])
			return
		if(mirrorlist_info['protocol'] !== 'https')
			return

		let option = document.createElement('option');
		option.value = mirrorlist_info['url'];
		option.setAttribute('country', mirrorlist_info['country']);
		option.innerHTML = mirrorlist_info['country'] + ' (' + mirrorlist_info['url'] + ')';

		mirrorlist_dropdown.appendChild(option);
	})

	sortSelect(mirrorlist_dropdown);
}

window.update_mirrorlist = (data) => {
	if(typeof data['mirrorlist'] !== 'undefined') {
		window.mirror_list = data['mirrorlist'];
		window.refresh_mirrorlist();
	}
}

save_custom_mirror.addEventListener('click', (event) => {
	let dropdown = document.querySelector('#mirrorlist');

	let mirror_name = document.querySelector('#mirror_name');
	let mirror_url = document.querySelector('#mirror_url');
	let custom_signcheck = document.querySelector('#custom_signcheck');
	let custom_signoptions = document.querySelector('#custom_signoptions');
	
	let new_mirror = document.createElement('option');
	new_mirror.value='-custom-';
	new_mirror.setAttribute('name', mirror_name.value);
	new_mirror.setAttribute('url', mirror_url.value);
	new_mirror.setAttribute('signcheck', custom_signcheck.value);
	new_mirror.setAttribute('signoptions', custom_signoptions.value);
	new_mirror.innerHTML = `${mirror_name.value} (${mirror_url.value})`

	dropdown.add(new_mirror, 0);
	new_mirror.selected = true;
})

/* Sweden */
//Server = https://mirror.osbeck.com/archlinux/$repo/os/$arch

if(socket.subscriptions('mirrorlist') != 2)
	socket.subscribe('mirrorlist', update_mirrorlist);

socket.send({'_module' : 'installation_steps/mirrors', 'mirrors' : 'refresh'})

"""

def notify_mirrors_complete(worker, *args, **kwargs):
	worker.frame.CLIENT_IDENTITY.send({
		'type' : 'notification',
		'source' : 'mirrors',
		'message' : 'Filter and ordered mirrors!',
		'status' : 'complete'
	})

def notify_mirror_updates(worker, *args, **kwargs):
	worker.frame.CLIENT_IDENTITY.send({
		'type' : 'notification',
		'source' : 'mirrors',
		'message' : 'Reorderings mirrors.',
		'status' : 'active'
	})

def filter_by_region(frame, region, worker, *args, **kwargs):
	return archinstall.filter_mirrors_by_region(region)

def update_mirrorlist(frame, mirrors, worker, *args, **kwargs):
	custom_mirrors = []
	normal_mirrors = {}
	for mirror in mirrors:
		if mirror['value'] == '-custom-':
			custom_mirrors.append(mirror)
		else:
			normal_mirrors[mirror['value']] = mirror['country']

	archinstall.add_custom_mirrors(custom_mirrors)
	return archinstall.insert_mirrors(normal_mirrors)

def stub(*args, **kwargs):
	return True

def on_request(frame):
	if '_module' in frame.data and frame.data['_module'] == 'installation_steps/mirrors':

		# Verify that the encryption step has been completed/skipped
		if not 'encryption' in session.steps:
			yield {
				'status' : 'incomplete',
				'next' : 'encryption',
				'_modules' : 'mirrors'
			}
			return

		if 'skip' in frame.data:
			session.steps['mirrors'] = spawn(frame, stub)
			yield {
				'status' : 'queued',
				'_modules' : 'arch_linux' 
			}
			yield {
				'_modules' : 'mirrors',
				'status' : 'complete',
				'next' : 'language'
			}
			return

		# If no specific mirrors are given, return the HTML data.
		if not 'mirrors' in frame.data:
			yield {
				'html' : html,
				'javascript' : javascript,
				'_modules' : 'mirrors'
			}

		elif frame.data['mirrors'] == 'refresh':
			## https://www.archlinux.org/mirrors/status/json/
			## https://www.archlinux.org/mirrorlist/?country=SE&protocol=https&use_mirror_status=on
			if not 'mirror_sync' in session.information or time.time() - session.information['mirror_sync']['last_check'] > session.information['mirror_sync']['check_frequency']:
				frame.CLIENT_IDENTITY.server.log(f'Getting latest mirrors from archlinux.org')
				with urllib.request.urlopen('https://www.archlinux.org/mirrors/status/json/') as url:
					session.information['mirror_sync'] = json.loads(url.read().decode())
					session.information['mirror_sync']['last_check'] = time.time() # Replace STRFTIME format with unix timestamp.

			yield {
				'mirrorlist' : session.information['mirror_sync'],
				'_modules' : 'mirrors'
			}
		elif frame.data['mirrors'] == 'autodetect':
			with urllib.request.urlopen('https://slimhttp.hvornum.se/geoip') as url:
				info = json.loads(url.read().decode())

			session.steps['mirrors'] = spawn(frame, filter_by_region, start_callback=notify_mirror_updates, callback=notify_mirrors_complete, region=info['country'])

			yield {
				'status' : 'queued',
				'_modules' : 'arch_linux' 
			}
			yield {
				'_modules' : 'mirrors',
				'status' : 'complete',
				'next' : 'language'
			}
			return
		elif type(frame.data['mirrors']) == dict:
			if ('selected_mirrors' not in frame.data['mirrors'] or 'region' not in frame.data['mirrors']) or len(frame.data['mirrors']['selected_mirrors']) == 0 and len(frame.data['mirrors']['region']) == 0:
				yield {
					'_modules' : 'mirrors',
					'status' : 'error',
					'message' : 'Need to select at least one mirror or region <i>(or skip and use default mirrors)</i>'
				}

			if 'region' in frame.data['mirrors']:
				session.information['mirror_region'] = frame.data['mirrors']['region']
			if 'selected_mirrors' in frame.data['mirrors']:
				session.information['mirrors'] = frame.data['mirrors']['selected_mirrors']

			region_update = None
			if 'mirror_region' in session.information and len(session.information['mirror_region']):
				notification_done = notify_mirrors_complete
				if 'mirrors' in session.information and len(session.information['mirrors']):
					notification_done = None
				region_update = spawn(frame, filter_by_region, start_callback=notify_mirror_updates, callback=notification_done, region=session.information['mirror_region'])

			custom_mirrors = spawn(frame, stub)
			
			if 'mirrors' in session.information and len(session.information['mirrors']):
				session.steps['mirrors'] = spawn(frame, update_mirrorlist, start_callback=notify_mirror_updates, callback=notify_mirrors_complete, mirrors=session.information['mirrors'], dependency=region_update)

			yield {
				'status' : 'queued',
				'_modules' : 'arch_linux' 
			}
			
			yield {
				'status' : 'success',
				'next' : 'language', # skip arch_linux as it's an informational page, will be redirected after the last AUR step.
				'_modules' : 'mirrors' 
			}