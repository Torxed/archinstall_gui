import json
import urllib.request
from os import walk
from os.path import isdir, isfile, abspath
from time import time

html = """
<div class="padded_content flex_grow flex column">
	<h3>Regional / Language settings <i>(Optional)</i></h3>
	<span>Some simpler language settings, such as timezone and locale.</span>

	<div class="form-area" id="form-area">
		<div class="input-form" id="input-form">
			<input type="text" id="locale" required autocomplete="off" />
			<label class="label">
				<span class="label-content">Choose language & region <i>(Ex: 'en_SE.UTF-8 UTF-8' or 'SE' for short)</i>.</span>
			</label>
		</div>
	</div>

	<div class="buttons bottom">
		<button id="save_language">Save settings</button>
	</div>
</div>
"""

## TODO:
## Needs to be loaded this way, since we can't inject JS into divs etc in the HTML above.
javascript = """

document.querySelector('#save_language').addEventListener('click', function() {
	socket.send({
		'_install_step' : 'language',
		'language' : document.querySelector('#locale').value
	})
})

"""

def notify_language_set(worker, *args, **kwargs):
	sockets[worker.client.sock.fileno()].send({
		'type' : 'notification',
		'source' : 'language',
		'message' : 'Language has been configured.',
		'status' : 'complete'
	})

class parser():
	def parse(path, client, data, headers, fileno, addr, *args, **kwargs):
		if '_install_step' in data and data['_install_step'] == 'language':
			if not 'language' in data:
				yield {
					'html' : html,
					'javascript' : javascript
				}
			else:

				set_locale = spawn(client, archinstall.set_locale, fmt=data['language'], callback=notify_language_set)

				yield {
					'status' : 'success',
					'next' : 'install_log'
				}

