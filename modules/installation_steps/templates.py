import json
import urllib.request
from os import walk
from os.path import isdir, isfile, abspath
from time import time

html = """
<div class="padded_content flex_grow flex column">
	<h3>Choose a template <i>(Optional)</i></h3>
	<span>If you don't want a bare-minimum Arch Linux installation.<br>Then here's where you can select a ready made template.<br>{additional_info}</span>
	<select id="templatelist" size="3" class="flex_grow">

	</select>

	<div class="buttons bottom">
		<button id="save_templates">Choose template</button>
	</div>
</div>
"""

## TODO:
## Needs to be loaded this way, since we can't inject JS into divs etc in the HTML above.
javascript = """

document.querySelector('#save_templates').addEventListener('click', function() {
	socket.send({
		'_install_step' : 'templates',
		'template' : document.querySelector('#templatelist').value
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
}

if(typeof resource_handlers['templates'] === 'undefined')
	resource_handlers['templates'] = [update_templtes];
else if(resource_handlers['templates'].length == 1)
	resource_handlers['templates'].push(update_templtes)

socket.send({'_install_step' : 'templates', 'templates' : 'refresh'})

"""

class parser():
	def parse(path, client, data, headers, fileno, addr, *args, **kwargs):
		print(args, kwargs)
		if '_install_step' in data and data['_install_step'] == 'templates':
			if not 'templates' in data and not 'template' in data:
				if not 'pacstrap' in progress:
					additional_info = "Template steps won't be installed until after the base system has been installed.."
				else:
					additional_info = "The template will be installed as soon as you choose it."
				
				yield {
					'html' : html.format(additional_info=additional_info),
					'javascript' : javascript
				}
			elif 'templates' in data:
				if data['templates'] == 'refresh':
					## https://github.com/Torxed/archinstall/tree/master/deployments
					## document.querySelectorAll('.js-navigation-open') -> item.title
					
					templates = {}
					for root, folders, files in walk('./dependencies/archinstall/deployments/'):
						for file in files:
							if not '.json' in file: continue
							with open(abspath(root + '/' + file), 'r') as fh:
								templates[file] = json.load(fh)
						break

					yield {
						'status' : 'success',
						'templates' : templates
					}
				elif type(data['templates']) == dict:
					pass
			elif 'template' in data:
				print('Selected specific template')
				yield {
						'status' : 'success',
						'next' : 'software'
					}

