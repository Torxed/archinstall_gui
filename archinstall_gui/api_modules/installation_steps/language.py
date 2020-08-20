import json
import urllib.request
import os
from time import time

from dependencies import archinstall
from lib.worker import spawn
import session

html = """
<div class="padded_content flex_grow flex column">
	<h3>Language & Regional settings <i>(Optional)</i></h3>
	<span>Some simpler language settings, such as timezone and locale.</span>

	<div class="note">
		<div class="noteHeader"><div class="noteIcon"></div><span>Note</span></div>
		<div class="noteBody">
			A list and more information on <a target="_blank" href="https://wiki.archlinux.org/index.php/Locale#Variables">locale's</a> can be found on the official Arch Wiki.<br>
			But as an example, <div class="inlineCode">en_US</div> would be for a US locale. <!-- .UTF-8 UTF-8 -->
		</div>
	</div>

	<select id="locale">

	</select>

	<h4>Time settings</h4>

	<div class="note">
		<div class="noteHeader"><div class="noteIcon"></div><span>Note</span></div>
		<div class="noteBody">
			More information on Time Zones and automatic time updates can be found in the <a target="_blank" href="https://wiki.archlinux.org/index.php/System_time#Time_zone">System Time</a> Arch Wiki article.
		</div>
	</div>

	
	<div class="warning">
		<div class="warningHeader"><div class="noteIcon"></div><span>Warning</span></div>
		<div class="noteBody">
			If you choose to select <div class="inlineCode">GMT+</div> and you opt in for <div class="inlineCode">Update system time automatically</div>, daylight saving time might not be correctly calculated, instead choose the closest city to you for more accurate time management.
		</div>
	</div>
	
	<span>
	Select a city cloest to you for a accurate Time Zone specification.
	</span>
	<select id="timezone">

	</select>

	<div class="form-area-oneline">
		<input type="checkbox" id="ntp" value="yes">
		<label for="ntp">Enable automatic time updates <i>(using NTP)</i></label>
	</div>

	<div class="buttons bottom">
		<button id="save_language">Save settings</button>
		<button id="skip_step">Skip and only set locale</button>
	</div>
</div>
"""

## TODO:
## Needs to be loaded this way, since we can't inject JS into divs etc in the HTML above.
javascript = """

window.refresh_timezones = () => {
	let timezones_dropdown = document.querySelector('#timezone');

	Object.keys(window.timezones).forEach((city) => {
		let symlink = window.timezones[city];


		let option = document.createElement('option');
		option.value = symlink;
		option.innerHTML = city;

		timezones_dropdown.appendChild(option);

	})

	sortSelect(timezones_dropdown);

	let options = timezones_dropdown.options;
	let i = 0;
	for (i=0; i < options.length; i++) {
		if (options[i].innerHTML == 'London') {
			break;
		}
	}

	timezones_dropdown.selectedIndex = i;

	return true;
}

window.refresh_locales = () => {
	let locales_dropdown = document.querySelector('#locale');

	Object.keys(window.locales).forEach((locale) => {
		let symlink = window.locales[locale];


		let option = document.createElement('option');
		option.value = locale;
		if (locale.includes('@')) {
			let locale_mods = locale.split('@');
			locale = locale_mods[0] + ' <i>('+locale_mods[1]+')</i>';
		}
		option.innerHTML = locale;

		locales_dropdown.appendChild(option);

	})

	sortSelect(locales_dropdown);

	let options = locales_dropdown.options;
	let i = 0;
	for (i=0; i < options.length; i++) {
		if (options[i].innerHTML == 'en_US') {
			break;
		}
	}

	locales_dropdown.selectedIndex = i;

	return true;
}

window.update_timezones = (data) => {
	if(typeof data['timezones'] !== 'undefined') {
		window.timezones = data['timezones'];
		window.refresh_timezones();
	}

	if(typeof data['locales'] !== 'undefined') {
		window.locales = data['locales'];
		window.refresh_locales();
	}

	return true;
}

document.querySelector('#save_language').addEventListener('click', function() {
	reboot_step = 'language';

	let tz = document.querySelector("#timezone");
	let loc = document.querySelector('#locale');

	socket.send({
		'_module' : 'installation_steps/language',
		'locale' : loc.options[loc.selectedIndex].value,
		'timezone' : tz.options[tz.selectedIndex].value,
		'ntp' : document.querySelector('#ntp').checked
	})
})

document.querySelector('#skip_step').addEventListener('click', function() {
	reboot_step = 'language';
	
	socket.send({
		'_module' : 'installation_steps/language',
		'skip' : true
	})
})

if(socket.subscriptions('language') != 2) {
	socket.subscribe('language', update_timezones);
}

socket.send({
	'_module' : 'installation_steps/language',
	'timezone' : 'refresh',
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
	return session.steps['arch_linux'].set_locale(fmt, encoding)

def set_timezone(frame, tz, *args, **kwargs):
	return session.steps['arch_linux'].set_timezone(tz)

def activate_ntp(frame, *args, **kwargs):
	return session.steps['arch_linux'].activate_ntp()

def stub(*args, **kwargs):
	return True

def on_request(frame):
	if '_module' in frame.data and frame.data['_module'] == 'installation_steps/language':
		if 'skip' in frame.data:
			# A bit of a missnomer, but ntp is the expected last step
			# of the language section, so set_locale has to satisfy it if we're skipping the step.
			session.steps['ntp'] = spawn(frame, set_locale, fmt='en_US', start_callback=language_config_start, callback=notify_language_set, dependency='arch_linux_worker')

			yield {
				'_modules' : 'language',
				'status' : 'queued',
				'next' : 'profiles'
			}
			return

		elif not 'locale' in frame.data and not 'timezone' in frame.data:
			yield {
				'html' : html,
				'javascript' : javascript,
				'_modules' : 'language'
			}
		elif 'timezone' in frame.data and frame.data['timezone'] == 'refresh':
			base = '/usr/share/zoneinfo/'
			timezones = {}
			for root, folders, files in os.walk(base):
				if len(folders): continue

				for city in files:
					if city in timezones:
						continue
					timezones[city] = os.path.join(root[len(base):], city)

			locale_base = '/usr/share/i18n/locales/'
			locales = {}

			for root, folders, files in os.walk(locale_base):
				if len(folders): continue

				for locale in files:
					locales[locale] = False

			yield {
				'_modules' : 'language',
				'timezones' : timezones,
				'locales' : locales
			}

		else:
			# TODO: Perhaps just change the language if the process hasn't yet finished.
			if not 'locale' in session.steps:
				session.steps['locale'] = spawn(frame, set_locale, fmt=frame.data['locale'], start_callback=language_config_start, dependency='accounts')
				session.steps['language'] = spawn(frame, set_timezone, tz=frame.data['timezone'], dependency=session.steps['locale'])
				
				if frame.data['ntp']:
					session.steps['ntp'] = spawn(frame, activate_ntp, callback=notify_language_set, dependency=session.steps['language'])
				else:
					session.steps['ntp'] = spawn(frame, stub, dependency=session.steps['language'])

				yield {
					'status' : 'queued',
					'_modules' : 'language',
					'next' : 'profiles'
				}

