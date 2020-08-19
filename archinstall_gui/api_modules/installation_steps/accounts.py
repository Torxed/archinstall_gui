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
	reboot_step = 'accounts';

	socket.send({
		'_module' : 'installation_steps/accounts',
		'username' : document.querySelector('#user').value,
		'password' : document.querySelector('#password').value,
		'sudo' : document.querySelector('#sudoer').checked
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

def setup_user(frame, username, password, sudo, worker, *args, **kwargs):
	if sudo:
		sudo = ['wheel',]
	else:
		sudo = []
	session.steps['arch_linux'].user_create(username, password=password, groups=sudo)

	if sudo:
		with open(f"{session.steps['arch_linux'].mountpoint}/etc/sudoers", 'r') as sudoers_fh:
			sudoers = sudoers_fh.read()
		if '\n# %wheel ALL=(ALL) ALL' in sudoers:
			sudoers = sudoers.replace('\n# %wheel ALL=(ALL) ALL', '%wheel ALL=(ALL) ALL')
			with open(f"{session.steps['arch_linux'].mountpoint}/etc/sudoers", 'w') as sudoers_fh:
				sudoers_fh.write(sudoers)

	return True

def notify_user_create_start(worker, *args, **kwargs):
	worker.frame.CLIENT_IDENTITY.send({
		'type' : 'notification',
		'source' : 'accounts',
		'message' : f"User <div class=\"inlineCode\">{worker.kwargs['username']}</div> is now being created",
		'status' : 'active'
	})

def notify_user_create_end(worker, *args, **kwargs):
	worker.frame.CLIENT_IDENTITY.send({
		'type' : 'notification',
		'source' : 'accounts',
		'message' : f"User <div class=\"inlineCode\">{worker.kwargs['username']}</div> has been created successfully",
		'status' : 'complete'
	})

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
		elif not 'username' in frame.data:# and 'group' not in frame.data:
			yield {
				'_modules' : 'accounts',
				'html' : html,
				'javascript' : javascript
			}
		elif 'username' in frame.data:
			session.steps['accounts'] = spawn(frame, setup_user, username=frame.data['username'], password=frame.data['password'], sudo=frame.data['sudo'], start_callback=notify_user_create_start, callback=notify_user_create_end, dependency='applications')
			yield {
				'_modules' : 'accounts',
				'status' : 'queued',
				'next' : 'aur_packages'
			}
		#elif 'group' in frame.data:
		#	print('Creating group:', frame.data['group'])