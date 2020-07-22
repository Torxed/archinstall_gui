import json, time, os
import urllib.request

from dependencies import archinstall
from lib.worker import spawn
import session

html = """
<div class="padded_content flex_grow flex column">
	<h3>Additional user account</h3>
	<span>If you wish to set up a non-root account here and now, this section can do so.</span>

	<div class="note" id="arch_linux_worker_wait">
		<div class="noteHeader"><div class="noteIcon"></div><span>Note</span></div>
		<div class="noteBody">
			The additional user creation will be queued until the Base OS is installed.
		</div>
	</div>

	<div class="warning">
		<div class="warningHeader"><div class="noteIcon"></div><span>Warning</span></div>
		<div class="noteBody">
			This step will not <a target="_blank" href="https://wiki.archlinux.org/index.php/Sudo#Disable_root_login">disable the <div class="inlineCode">root</div> account</a>. The tool is also quite limited to only creating one account, if you wish to create more than one account please read the official Arch Linux Wiki section called <a target="_blank" href="https://wiki.archlinux.org/index.php/Users_and_groups">Users & Groups</a>.
		</div>
	</div>

	<div class="form-area">
		<div class="input-form" id="input-form">
			<input type="text" id="user" required autocomplete="off" />
			<label class="label">
				<span class="label-content">Choose a username.</span>
			</label>
		</div>
	</div>

	<div class="form-area">
		<div class="input-form" id="input-form">
			<input type="password" id="password" required autocomplete="off" />
			<label class="label">
				<span class="label-content">A password for the chosen username.</span>
			</label>
		</div>
	</div>

	<div class="form-area-oneline">
		<input type="checkbox" id="sudoer" value="yes">
		<label for="sudoer">Add user to sudoer list?</label>
	</div>

	<div class="buttons bottom">
		<button id="create_user">Create user</button>
		<button id="skip_accounts">Skip this step</button>
	</div>
</div>
"""

## TODO:
## Needs to be loaded this way, since we can't inject JS into divs etc in the HTML above.
javascript = """

document.querySelector('#create_user').addEventListener('click', function() {
	socket.send({
		'_module' : 'installation_steps/accounts',
		'username' : document.querySelector('#user').value.split(" "),
		'password' : document.querySelector('#password').value.split(" ")
	})
})

document.querySelector('#skip_accounts').addEventListener('click', function() {
	socket.send({
		'_module' : 'installation_steps/accounts',
		'skip' : true
	})
})

"""

def stub(*args, **kwargs):
	return True

def on_request(frame):
	if '_module' in frame.data and frame.data['_module'] == 'installation_steps/accounts':
		if 'skip' in frame.data:
			session.steps['accounts'] = spawn(frame, stub, dependency='applications')
			yield {
				'_modules' : 'accounts',
				'status' : 'skipped',
				'next' : 'aur_packages'
			}
			return
		elif not 'user' in frame.data or 'group' not in frame.data:
			yield {
				'html' : html,
				'javascript' : javascript,
				'_modules' : 'accounts'
			}
		elif 'user' in frame.data:
			print('Creating user:', frame.data['user'])
		elif 'group' in frame.data:
			print('Creating group:', frame.data['group'])