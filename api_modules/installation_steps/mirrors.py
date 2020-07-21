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
			<select id="mirrorlist" multiple>

			</select>

			<h3>Add a custom mirror</h3>
			<div class="form-area" id="form-area">
				<div class="input-form" id="input-form">
					<input type="text" id="mirror_name" required autocomplete="off" />
					<label class="label">
						<span class="label-content">Name of mirror<i>(Ex: local_repo</i>.</span>
					</label>
				</div>
			</div>
			<div class="form-area" id="form-area">
				<div class="input-form" id="input-form">
					<input type="text" id="mirror_url" required autocomplete="off" />
					<label class="label">
						<span class="label-content">URL to custom mirror <i>(Ex: http://192.168.0.1/$repo/os/$arch)</i>.</span>
					</label>
				</div>
			</div>

			<h3>Or use all mirrors from a specified region</h3>
			<div class="form-area" id="form-area">
				<div class="input-form" id="input-form">
					<input type="text" id="country_code" required autocomplete="off" />
					<label class="label">
						<span class="label-content">Write country code(s), separate with , <i>(Ex: SE,UK = Sweden and United Kingdom)</i>.</span>
					</label>
				</div>
			</div>

			<div class="buttons bottom">
				<button id="save_mirrors">Use selected mirrors</button>
				<button id="save_mirrors">Use Automatic detection</button>
				<button id="save_mirrors">Skip and use default mirrors</button>
			</div>
		</div>
	"""
else:
	html = 'Previous step <i>(encryption)</i> not completed.'

## TODO:
## Needs to be loaded this way, since we can't inject JS into divs etc in the HTML above.
javascript = """

document.querySelector('#save_mirrors').addEventListener('click', function() {
	let mirrors = {};
	let mirror_list = document.querySelector('#mirrorlist');
	Array.from(mirror_list.options).forEach(function(option_element) {
		let option_text = option_element.text;
		let option_value = option_element.value;
		let is_option_selected = option_element.selected;

		if (is_option_selected) {
			mirrors[option_value] = option_element.getAttribute('country');
		}
	});

	socket.send({
		'_module' : 'installation_steps/mirrors',
		'mirrors' : {
			'region' : document.querySelector('#country_code').value,
			'selected_mirrors' : mirrors
		}
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
}

window.update_mirrorlist = (data) => {
	if(typeof data['mirrorlist'] !== 'undefined') {
		window.mirror_list = data['mirrorlist'];
		window.refresh_mirrorlist();
	}
}

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

def update_mirrorlist(frame, mirrors, worker, *args, **kwargs):
	return archinstall.insert_mirrors(mirrors)

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
				region_update = spawn(frame, archinstall.filter_mirrors_by_region, start_callback=notify_mirror_updates, callback=notification_done, region=session.information['mirror_region'])
			
			if 'mirrors' in session.information and len(session.information['mirrors']):
				session.steps['mirrors'] = spawn(frame, update_mirrorlist, start_callback=notify_mirror_updates, callback=notify_mirrors_complete, mirrors=session.information['mirrors'], dependency=region_update)

			yield {
				'status' : 'queued',
				'_modules' : 'base_os' 
			}
			
			yield {
				'status' : 'success',
				'next' : 'language', # base_os doesn't contain anything (yet)
				'_modules' : 'mirrors' 
			}


#					storage['custom_mirror'] = {'name' : frame.data['mirrors']['mirror_name'], 'url' : frame.data['mirrors']['mirror_url']}
#					log(f"Storing selected mirrors. Region: {storage['mirror_region']}, Specifics: {storage['mirror_specific']}", level=4, origin='api.mirrors')
#
#					sync_mirrors = None
#					specific_mirrors = None
#					if storage['mirror_region']:
#						sync_mirrors = spawn(client, archinstall.filter_mirrors_by_country_list, start_callback=notify_mirror_updates, callback=notify_mirrors_complete, countries=storage['mirror_region'])#, dependency='formatting') # NOTE: This updates the live/local mirrorlist, which will be copied in the install steps later by pacstrap.
#
#					if storage['mirror_specific']:
#						if not storage['mirror_region']:
#							# Before adding specific mirrors, flush the default mirrors if we didn't supply a specific region as well.
#							# A region (SE) could for instance have been selected, then we won't flush that but simply add additional ones.
#							sync_mirrors = spawn(client, archinstall.flush_all_mirrors)
#						specific_mirrors = spawn(client, archinstall.add_specific_mirrors, start_callback=notify_mirror_updates, callback=notify_mirrors_complete, mirrors=storage['mirror_specific'], dependency=sync_mirrors)
#
#					if storage['custom_mirror']['name'] and storage['custom_mirror']['url']:
#						if not storage['mirror_region'] and not storage['mirror_specific']:
#							sync_mirrors = spawn(client, archinstall.flush_all_mirrors)
#
#						dependency = sync_mirrors
#						if specific_mirrors:
#							dependency = specific_mirrors
#						spawn(client, archinstall.add_custom_mirror, **storage['custom_mirror'], start_callback=notify_mirror_updates, callback=notify_mirrors_complete, dependency=dependency)
#
#
#					yield {
#						'status' : 'success',
#						'next' : 'hardware'
#					}
