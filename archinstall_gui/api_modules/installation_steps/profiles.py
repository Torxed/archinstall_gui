import json, time, os
import urllib.request

from dependencies import archinstall
from lib.worker import spawn
import session

html = """
<div class="padded_content flex_grow flex column">
	<h3>Choose a profile <i>(Optional)</i></h3>
	<span>If you don't want a bare-minimum Arch Linux installation.<br>Then here's where you can select a ready made template.</span>

	<div class="note">
		<div class="noteHeader"><div class="noteIcon"></div><span>Note</span></div>
		<div class="noteBody">
			The official Arch Installer documentation has more in-depth information regarding <a target="_blank" href="https://archinstaller.readthedocs.io/en/latest/">profiles & templates</a>.
		</div>
	</div>

	<select id="templatelist" size="3" class="flex_grow">

	</select>

	<div class="buttons bottom">
		<button id="save_templates">Use selected template</button>
		<button id="skip_templates">Skip this step</button>
	</div>
</div>
"""

## TODO:
## Needs to be loaded this way, since we can't inject JS into divs etc in the HTML above.
javascript = """

document.querySelector('#save_templates').addEventListener('click', function() {
	reboot_step = 'profiles';

	socket.send({
		'_module' : 'installation_steps/profiles',
		'template' : document.querySelector('#templatelist').value
	})
})

document.querySelector('#skip_templates').addEventListener('click', function() {
	socket.send({
		'_module' : 'installation_steps/profiles',
		'skip' : true
	})
})

window.refresh_template_list = () => {
	let templatelist_dropdown = document.querySelector('#templatelist');

	Object.keys(window.templates).forEach((template) => {
		let template_info = window.templates[template];
		let option = document.createElement('option');
		option.value = template;
		option.innerHTML = template + ' (' + template_info['description'] + ')';

		templatelist_dropdown.appendChild(option);
	})
}

window.update_templtes = (data) => {
	if(typeof data['templates'] !== 'undefined') {
		window.templates = data['templates'];
		window.refresh_template_list();
	}
	return true;
}

if(socket.subscriptions('templates') != 2)
	socket.subscribe('templates', update_templtes);

socket.send({'_module' : 'installation_steps/profiles', 'templates' : 'refresh'})

"""

def notify_template_started(worker, *args, **kwargs):
	worker.frame.CLIENT_IDENTITY.send({
		'type' : 'notification',
		'source' : 'profiles',
		'message' : 'Template is being installed',
		'status' : 'active'
	})

def notify_template_installed(worker, *args, **kwargs):
	worker.frame.CLIENT_IDENTITY.send({
		'type' : 'notification',
		'source' : 'profiles',
		'message' : 'Template has been installed.',
		'status' : 'complete'
	})

def install_profile(frame, profile_name, worker, hostname='Archnistall', *args, **kwargs):
	return session.steps['arch_linux'].install_profile(session.information['profiles_cache'][profile_name]['path'])

def stub(*args, **kwargs):
	return True

def on_request(frame):
	main_dependency = 'ntp'
	
	if '_module' in frame.data and frame.data['_module'] == 'installation_steps/profiles':
		if 'skip' in frame.data:
			session.steps['profiles'] = spawn(frame, stub, dependency=main_dependency)
			yield {
				'_modules' : 'profiles',
				'status' : 'skipped',
				'next' : 'applications'
			}
			return

		elif 'templates' in frame.data:
			if frame.data['templates'] == 'refresh':
				## https://github.com/Torxed/archinstall/tree/master/deployments
				## document.querySelectorAll('.js-navigation-open') -> item.title
				
				session.information['profiles_cache'] = archinstall.list_profiles('./dependencies/archinstall/profiles/')

				yield {
					'status' : 'success',
					'templates' : session.information['profiles_cache']
				}
		
		elif 'template' in frame.data and frame.data['template'].strip():
			
			session.steps['profiles'] = spawn(frame, install_profile, profile_name=frame.data['template'], start_callback=notify_template_started, callback=notify_template_installed, dependency=main_dependency)
			
			yield {
				'status' : 'queued',
				'next' : 'applications',
				'_modules' : 'profiles' 
			}

		else:
			yield {
				'html' : html,
				'javascript' : javascript,
				'_modules' : 'profiles'
			}