import json
from os.path import isdir, isfile

html = """
<div class="padded_content flex_grow flex column">
	<h3>Choose mirror options</h3>
	<span>Here's your chance to select region/specific mirrors.<br>{additional_info}</span>
	<div class="form-area" id="form-area">
		<div class="input-form" id="input-form">
			<input type="password" id="country_code" required autocomplete="off" />
			<label class="label">
				<span class="label-content">Enter a country code</span>
			</label>
		</div>
	</div>

	<div class="buttons bottom">
		<button id="save_mirrors">Start formatting</button>
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
			'region' : null
		}
	})
})

window.update_mirrorlist = (errors, data) => {
	console.log('Got mirrors!', errors)
}

fetch(`https://www.archlinux.org/mirrors/status/json/`)
       .then(response => response.json())
       .then(json => callback(null, json.restaurants))
       .catch(error => callback(error, null))

"""

class parser():
	def parse(path, client, data, headers, fileno, addr, *args, **kwargs):
		print(args, kwargs)
		if '_install_step' in data and data['_install_step'] == 'mirrors':
			if not 'mirrors' in data:
				if not 'pacstrap' in progress:
					additional_info = "Installation of packages have not yet begun, so there's still time to change desired mirror for the installation process."
				else:
					additional_info = "Installation has begun, so these changes won't take affect until you're in the installed system."
				
				yield {
					'html' : html.format(additional_info=additional_info),
					'javascript' : javascript,
					'all_mirrors' : {
						'/dev/sda' : {'fileformat' : 'NTFS', 'size' : '512GB'},
						'/dev/sdb' : {'fileformat' : 'NTFS', 'size' : '120GB'},
						'/dev/nvme0' : {'fileformat' : 'Linux Filesyste', 'size' : '120GB'}
					}
				}
			else:
				yield {
					'status' : 'success',
					'next' : 'language'
				}