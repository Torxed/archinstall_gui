import json
import urllib.request
from os import walk
from os.path import isdir, isfile, abspath
from time import time

from dependencies import archinstall
from lib.worker import spawn
import session

html = """
<div class="padded_content flex_grow flex column">
	<h3>Regional / Language settings <i>(Optional)</i></h3>
	<span>Some simpler language settings, such as timezone and locale.</span>

	<div class="note">
		<div class="noteHeader"><div class="noteIcon"></div><span>Note</span></div>
		<div class="noteBody">
			A list and more information on <a target="_blank" href="https://wiki.archlinux.org/index.php/Locale#Variables">locale's</a> can be found on the official Arch Wiki.<br>
			But as an example, <div class="inlineCode">en_US.UTF-8 UTF-8</div> would be for a US locale.
		</div>
	</div>

	<div class="form-area" id="form-area">
		<div class="input-form" id="input-form">
			<input type="text" id="locale" required autocomplete="off" value="en_US.UTF-8 UTF-8" />
			<label class="label">
				<span class="label-content">Choose a locale <i>(system language)</i>.</span>
			</label>
		</div>
	</div>

	<div class="note">
		<div class="noteHeader"><div class="noteIcon"></div><span>Note</span></div>
		<div class="noteBody">
			More information on Time Zones can be found in the <a target="_blank" href="https://wiki.archlinux.org/index.php/System_time#Time_zone">System Time</a> Arch Wiki article.
		</div>
	</div>

	<div class="form-area" id="form-area">
		<div class="input-form" id="input-form">
			<input type="text" id="timezone" required autocomplete="off" />
			<label class="label">
				<span class="label-content">Choose a Time Zone <i>(Ex: 'Europe/Stockholm' for Sweden)</i>.</span>
			</label>
		</div>
	</div>

	<div class="warning">
		<div class="warningHeader"><div class="noteIcon"></div><span>Warning</span></div>
		<div class="noteBody">
			The Time Zone is <b>case sensitive</b>. For instance, <div class="inlineCode">Europe/Stockholm</div> is valid, but <div class="inlineCode">europe/Stockhilm</div> is not.
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
		'_module' : 'installation_steps/language',
		'locale' : document.querySelector('#locale').value,
		'timezone' : document.querySelector('#timezone').value,
	})
})

"""

def language_config_start(worker, *args, **kwargs):
	worker.frame.CLIENT_IDENTITY.send({
		'type' : 'notification',
		'source' : 'language',
		'message' : 'Configuring language preferences.',
		'status' : 'active'
	})

def notify_language_set(worker, *args, **kwargs):
	worker.frame.CLIENT_IDENTITY.send({
		'type' : 'notification',
		'source' : 'language',
		'message' : 'Language has been configured.',
		'status' : 'complete'
	})

def set_locale(frame, fmt, *args, **kwargs):
	encoding = 'UTF-8'
	if ' ' in fmt:
		fmt, encoding = fmt.split(' ', 1)
	return session.steps['base_os'].set_locale(fmt, encoding)

def set_timezone(frame, tz, *args, **kwargs):
	return session.steps['base_os'].set_timezone(tz)

def on_request(frame):
	if '_module' in frame.data and frame.data['_module'] == 'installation_steps/language':
		if not 'locale' in frame.data:
			yield {
				'html' : html,
				'javascript' : javascript,
				'_modules' : 'language'
			}
		else:

			# TODO: Perhaps just change the language if the process hasn't yet finished.
			if not 'locale' in session.steps:
				session.steps['locale'] = spawn(frame, set_locale, fmt=frame.data['locale'], start_callback=language_config_start, dependency='base_os_worker')
				session.steps['timezone'] = spawn(frame, set_timezone, tz=frame.data['timezone'], callback=notify_language_set, dependency=session.steps['locale'])

				yield {
					'status' : 'queued',
					'_modules' : 'language',
					'next' : 'profiles'
				}

