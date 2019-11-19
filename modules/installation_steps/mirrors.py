import json
import urllib.request
from os.path import isdir, isfile
from time import time

html = """
<div class="padded_content flex_grow flex column">
	<h3>Choose mirror<i>(s) (Optional)</i></h3>
	<span>Here's your chance to select region/specific mirrors.<br>{additional_info}</span>
	<div class="form-area" id="form-area">
		<div class="input-form" id="input-form">
			<input type="text" id="country_code" required autocomplete="off" />
			<label class="label">
				<span class="label-content">Filter by country code(s), separate with , <i>(Ex: SE,UK = Sweden and United Kingdom)</i>.</span>
			</label>
		</div>
	</div>
	<select id="mirrorlist" multiple>

	</select>

	<div class="buttons bottom">
		<button id="save_mirrors">Save mirrorlist<i>(s)</i></button>
	</div>
</div>
"""

## TODO:
## Needs to be loaded this way, since we can't inject JS into divs etc in the HTML above.
javascript = """

document.querySelector('#save_mirrors').addEventListener('click', function() {
	socket.send({
		'_install_step' : 'mirrors',
		'mirrors' : {
			'region' : document.querySelector('#country_code').value,
			'specific' : document.querySelector('#mirrorlist').selectedOptions
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

if(typeof resource_handlers['mirrors'] === 'undefined')
	resource_handlers['mirrors'] = [update_mirrorlist];
else if(resource_handlers['mirrors'].length == 1)
	resource_handlers['mirrors'].push(update_mirrorlist)

socket.send({'_install_step' : 'mirrors', 'mirrors' : 'refresh'})

"""

class parser():
	def parse(path, client, data, headers, fileno, addr, *args, **kwargs):
		if '_install_step' in data and data['_install_step'] == 'mirrors':
			if not 'mirrors' in data:
				if not 'pacstrap' in progress:
					additional_info = "Installation of packages have not yet begun, so there's still time to change desired mirror for the installation process."
				else:
					additional_info = "Installation has begun, so these changes won't take affect until you're in the installed system."
				
				yield {
					'html' : html.format(additional_info=additional_info),
					'javascript' : javascript
				}
			else:
				if data['mirrors'] == 'refresh':
					## https://www.archlinux.org/mirrors/status/json/
					## https://www.archlinux.org/mirrorlist/?country=SE&protocol=https&use_mirror_status=on
					if not 'mirrors' in storage or time() - storage['mirrors']['last_check'] > storage['mirrors']['check_frequency']:
						with urllib.request.urlopen('https://www.archlinux.org/mirrors/status/json/') as url:
							json_data = json.loads(url.read().decode())
							storage['mirrors'] = json_data
							storage['mirrors']['last_check'] = time() # Replace STRFTIME format with unix timestamp.

					yield {
						'status' : 'success',
						'mirrorlist' : storage['mirrors']
					}
				elif type(data['mirrors']) == dict:
					storage['mirror_region'] = data['mirrors']['region']
					storage['mirror_specific'] = data['mirrors']['specific']

					spawn(client, archinstall.filter_mirrors_by_country_list, countries=storage['mirror_region'], dependency='formatting')

					yield {
						'status' : 'success',
						'next' : 'hardware'
					}
