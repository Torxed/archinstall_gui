import json
import urllib.request
from os import walk
from os.path import isdir, isfile, abspath
from time import time

html = """
<div class="padded_content flex_grow flex column">
	<h3>Add additional packages <i>(Optional)</i></h3>
	<span>If you want additional <a href="https://www.archlinux.org/packages/" target="_blank">packages</a> or <a href="https://aur.archlinux.org/" target="_blank">AUR packages</a>, add them below separated by spaces.</span>
	<textarea id="software_list" size="3" class="flex_grow" placeholder="base packages will be installed automatically (so no need to add them here)."></textarea>

	<div class="buttons bottom">
		<button id="save_packages">Install packages</button>
	</div>
</div>
"""

## TODO:
## Needs to be loaded this way, since we can't inject JS into divs etc in the HTML above.
javascript = """

document.querySelector('#save_packages').addEventListener('click', function() {
	socket.send({
		'_install_step' : 'base_os',
		'packages' : document.querySelector('#software_list').value
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

window.update_packages = (data) => {
	if(typeof data['packages'] !== 'undefined')
		document.querySelector('#software_list').value = data['packages']
}

if(socket.subscriptions('base_os') != 2)
	socket.subscribe('base_os', update_packages);

socket.send({'_install_step' : 'base_os', 'packages' : 'refresh'})

"""

class parser():
	def parse(path, client, data, headers, fileno, addr, *args, **kwargs):
		if '_install_step' in data and data['_install_step'] == 'base_os':
			if not 'packages' in data:
				if not 'pacstrap' in progress:
					additional_info = "Template steps won't be installed until after the base system has been installed.."
				else:
					additional_info = "The template will be installed as soon as you choose it."
				
				yield {
					'html' : html.format(additional_info=additional_info),
					'javascript' : javascript
				}
			elif 'packages' in data:
				if data['packages'] == 'refresh':
					## https://github.com/Torxed/archinstall/tree/master/deployments
					## document.querySelectorAll('.js-navigation-open') -> item.title
					packagelist = ''
					yield {
						'status' : 'success',
						'packagelist' : packagelist
					}
				else:
					yield {
							'status' : 'success',
							'next' : 'templates'
						}

