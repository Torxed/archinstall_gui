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
	socket.send({
		'_module' : 'installation_steps/profiles',
		'template' : document.querySelector('#templatelist').value
	})
})

document.querySelector('#skip_templates').addEventListener('click', function() {
	notification({
		'source' : 'profiles',
		'status' : 'skipped',
		'next' : 'applications'
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
	if '_module' in frame.data and frame.data['_module'] == 'installation_steps/profiles':
		if not 'templates' in frame.data:
			yield {
				'html' : html,
				'javascript' : javascript,
				'_modules' : 'profiles'
			}
		elif 'templates' in frame.data:
			if frame.data['templates'] == 'refresh':
				## https://github.com/Torxed/archinstall/tree/master/deployments
				## document.querySelectorAll('.js-navigation-open') -> item.title
				
				templates = {}
				for root, folders, files in os.walk('./dependencies/archinstall/profiles/'):
					for file in files:
						extension = os.path.splitext(file)[1]
						if extension in ('.json', '.py'):
							templates[file] = extension
					break

				yield {
					'status' : 'success',
					'templates' : templates
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

