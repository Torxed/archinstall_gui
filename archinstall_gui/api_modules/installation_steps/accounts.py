import json, time, os
import urllib.request

from dependencies import archinstall
from lib.worker import spawn
import session

html = """
<div class="padded_content flex_grow flex column">
	<h3>Additional user account</h3>
	<span>If you wish to set up a non-root account here and now, this section enables you to do so.</span>

	<div class="note" id="arch_linux_worker_wait">
		<div class="noteHeader"><div class="noteIcon"></div><span>Note</span></div>
		<div class="noteBody">
			The additional user creation will be queued until the Base OS is installed.
		</div>
	</div>

	<div class="warning">
		<div class="warningHeader"><div class="noteIcon"></div><span>Warning</span></div>
		<div class="noteBody">
			By default, the <div class="inlineCode">root</div> account is disabled. <b>Skipping this step</b> or <i>not</i> setting sudo permission for the new users <b>requires you to set a root password</b> <i>(A popup prompt will ask you if you skip)</i>.
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

window.showRootPwPrompt = () => {
	let area = document.createElement('div');
	area.innerHTML = '<span>You opted in to skip this step, or a sudo user was not selected. This requires you to set a root password <i>(blank password works fine too)</i> or go back and create a sudo user since the root account is by default locked/disabled. You can go back by closing this popup.</span>'

	let form_area = document.createElement('div');
	form_area.classList = 'form-area';
	area.appendChild(form_area);

	let input_form = document.createElement('div');
	input_form.classList = 'input-form';
	form_area.appendChild(input_form);

	let root_pw_input = document.createElement('input');
	root_pw_input.type = 'password';
	root_pw_input.required = true;
	root_pw_input.autocomplete = 'off'; // Strictly not nessecary
	input_form.appendChild(root_pw_input);

	let root_pw_label = document.createElement('label');
	root_pw_label.classList = 'label';
	input_form.appendChild(root_pw_label);

	let label_span = document.createElement('span');
	label_span.classList='label-content';
	label_span.innerHTML = 'Choose a root password <i>(empty entry is allowed)</i>'
	root_pw_label.appendChild(label_span);

	let buttons = document.createElement('div');
	buttons.classList = 'buttons bottom';
	area.appendChild(buttons);

	let save_btn = document.createElement('button');
	save_btn.innerHTML = 'Set root password';
	buttons.appendChild(save_btn);

	let cancel_btn = document.createElement('button');
	cancel_btn.innerHTML = 'Go back';
	buttons.appendChild(cancel_btn);

	let frame = popup(area);

	save_btn.addEventListener('click', () => {
		socket.send({
			'_module' : 'installation_steps/accounts',
			'root_pw' : root_pw_input.value
		})
		frame.remove();
	})

	cancel_btn.addEventListener('click', () => {
		frame.remove();
	})
}

document.querySelector('#create_user').addEventListener('click', function() {
	let username = document.querySelector('#user').value;
	let password = document.querySelector('#password').value;
	let sudo = document.querySelector('#sudoer').checked;

	if(username.length <= 0 || !sudo) {
		showRootPwPrompt();
	} else {
		reboot_step = 'accounts';

		socket.send({
			'_module' : 'installation_steps/accounts',
			'username' : username,
			'password' : password,
			'sudo' : sudo
		})
	}
})

document.querySelector('#skip_accounts').addEventListener('click', function() {
	showRootPwPrompt();
//	socket.send({
//		'_module' : 'installation_steps/accounts',
//		'skip' : true
//	})
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

def set_root_pw(frame, password, worker, *args, **kwargs):
	# Mandatory, unless setup_iser with sudo=True was set.
	# https://github.com/archlinux/svntogit-packages/commit/0320c909f3867d47576083e853543bab1705185b#diff-8d0411b338c83cd8cd8ad9d9db127101
	session.steps['arch_linux'].user_set_pw('root', password=password)

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

def notify_root_pw_set_start(worker, *args, **kwargs):
	worker.frame.CLIENT_IDENTITY.send({
		'type' : 'notification',
		'source' : 'accounts',
		'message' : f"Setting <div class=\"inlineCode\">root</div> password.",
		'status' : 'active'
	})

def notify_root_pw_set_end(worker, *args, **kwargs):
	worker.frame.CLIENT_IDENTITY.send({
		'type' : 'notification',
		'source' : 'accounts',
		'message' : f"<div class=\"inlineCode\">root</div> password has been set successfully.",
		'status' : 'complete'
	})

def error_setting_root_pw(worker, *args, **kwargs):
	worker.frame.CLIENT_IDENTITY.send({
		'type' : 'notification',
		'source' : 'accounts',
		'message' : f"Could not set <div class=\"inlineCode\">root</div>.",
		'status' : 'error'
	})

def on_request(frame):
	if '_module' in frame.data and frame.data['_module'] == 'installation_steps/accounts':
		# Non-skippable step due to root being locked by default.
		#
		# if 'skip' in frame.data:
		# 	session.steps['accounts'] = spawn(frame, stub, dependency='arch_linux_worker')
		# 	yield {
		# 		'_modules' : 'accounts',
		# 		'status' : 'skipped',
		# 		'next' : 'aur_packages'
		# 	}
		# 	return
		if not 'username' in frame.data and 'root_pw' not in frame.data:# and 'group' not in frame.data:
			yield {
				'_modules' : 'accounts',
				'html' : html,
				'javascript' : javascript
			}
		elif 'username' in frame.data:
			session.steps['accounts'] = spawn(frame, setup_user, username=frame.data['username'], password=frame.data['password'], sudo=frame.data['sudo'], start_callback=notify_user_create_start, callback=notify_user_create_end, dependency='arch_linux_worker')
			yield {
				'_modules' : 'accounts',
				'status' : 'queued',
				'next' : 'language'
			}
		elif 'root_pw' in frame.data:
			session.steps['accounts'] = spawn(frame, set_root_pw, password=frame.data['root_pw'], error_callback=error_setting_root_pw, start_callback=notify_root_pw_set_start, callback=notify_root_pw_set_end, dependency='arch_linux_worker')
			yield {
				'_modules' : 'accounts',
				'status' : 'queued',
				'next' : 'language'
			}
		#elif 'group' in frame.data:
		#	print('Creating group:', frame.data['group'])