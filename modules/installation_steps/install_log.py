import json
import urllib.request
from os import walk
from os.path import isdir, isfile, abspath
from time import time

html = """
<div class="padded_content flex_grow flex column">
	<h3>Installation log</h3>
	<span>Here's the complete list of commands executed <i>(so far)</i>.</span>
	<textarea id="logbox" size="3" class="flex_grow" placeholder="Nothing has been executed yet...">{log}</textarea>

	<div class="buttons bottom">
		<button id="refresh_button">Refresh</button>
	</div>
</div>
"""

## TODO:
## Needs to be loaded this way, since we can't inject JS into divs etc in the HTML above.
javascript = """

document.querySelector('#refresh_button').addEventListener('click', function() {
	show_install_log();
})

if(typeof archinstall_timers['logrefresh'] !== 'undefined')
	clearInterval(archinstall_timers['logrefresh']);

archinstall_timers['logrefresh'] = setInterval(() => {
	let html_obj = document.querySelector('#logbox');
	if(!html_obj) {
		clearInterval(archinstall_timers['logrefresh']);
	} else {
		show_install_log();
	}
}, 1000)

window.logbox = document.querySelector('#logbox');
window.logbox.scrollTop = window.logbox.scrollHeight;

"""

class parser():
	def parse(path, client, data, headers, fileno, addr, *args, **kwargs):
		if '_install_step' in data and data['_install_step'] == 'install_log':
			log = '\n'.join(archinstall.commandlog)
			yield {
				'html' : html.format(log=log),
				'javascript' : javascript
			}