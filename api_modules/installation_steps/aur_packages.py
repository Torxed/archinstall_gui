import json, time, os
import urllib.request

from dependencies import archinstall
from lib.worker import spawn
import session

html = """
<div class="padded_content flex_grow flex column">
	<h3>AUR Support & Packages</h3>
	
	<div class="note">
		<div class="noteHeader"><div class="noteIcon"></div><span>Note</span></div>
		<div class="noteBody">
			The <a target="_blank" href="https://wiki.archlinux.org/index.php/Arch_User_Repository">Arch User Repository <i>(AUR)</i></a> is a collection of <a target="_blank" href="https://aur.archlinux.org/packages/">AUR packages</a> driven by the community.<br>
		</div>
	</div>
	
	<span>Installing and using AUR <i>(community)</i> packages inside your installation is provided by <a target="_blank" href="https://github.com/Jguer/yay">yay</a>.<br>
	<div class="inlineCode">yay</div> is a small AUR helper, with many flags similar to <a target="_blank" href="https://wiki.archlinux.org/index.php/pacman"><div class="inlineCode">pacman</div></a> - the builtin package manager of Arch Linux.<br>
	Although there are some differences, <div class="inlineCode">yay</div> should make it easier for beginners to install otherwise complicated community packages.<br>
	<br>
	It's <b>strongly suggested</b> that you read the official Wiki article regarding <a href="https://wiki.archlinux.org/index.php/Arch_User_Repository" target="_blank">Arch User Repository</a> in order to get familar and understand what could go wrong and how to maintain and install AUR packages in general.<br>
	<br>
	Before asking questions regarding AUR in the official support channels of Arch Linux, the Wiki article should be understood in full.</span>


	<div class="note" id="arch_linux_worker_wait">
		<div class="noteHeader"><div class="noteIcon"></div><span>Note</span></div>
		<div class="noteBody">
			AUR support will be added once the Base OS step is complete.
		</div>
	</div>


	<div class="warning">
		<div class="warningHeader"><div class="noteIcon"></div><span>Warning</span></div>
		<div class="noteBody">
			<b>Use AUR at your own risk!</b> These packages are not officially supported and therefore <b>can contain bugs, malicious code and/or break your system</b>.<br>
			<br>
		</div>
	</div>

	<div class="form-area-oneline">
		<button id="activate_AUR">Activate AUR support</button>
	</div>

	<div class="form-area" id="form-area">
		<div class="input-form" id="input-form">
			<input type="text" id="package_list" required autocomplete="off" disabled />
			<label class="label disabled">
				<span class="label-content" id="lbl_content">AUR support currently disabled</span>
			</label>
		</div>
	</div>

	<div class="buttons bottom">
		<button id="install_packages">Install AUR packages</button>
		<button id="skip_step">Skip this step</button>
	</div>
</div>
"""

## TODO:
## Needs to be loaded this way, since we can't inject JS into divs etc in the HTML above.
javascript = """

document.querySelector('#activate_AUR').addEventListener('click', function() {
	document.querySelector('#package_list').disabled = false;
	document.querySelector('#lbl_content').innerHTML = "Space separated list of AUR packages to install.";
})

document.querySelector('#install_packages').addEventListener('click', function() {
	socket.send({
		'_module' : 'installation_steps/aur_packages',
		'packages' : document.querySelector('#package_list').value.split(" ")
	})
	document.querySelector('#package_list').disabled = false;
})

document.querySelector('#skip_step').addEventListener('click', function() {
	socket.send({
		'_module' : 'installation_steps/aur_packages',
		'skip' : true
	})
})

"""

def stub(*args, **kwargs):
	return True

def on_request(frame):
	if '_module' in frame.data and frame.data['_module'] == 'installation_steps/aur_packages':
		if 'skip' in frame.data:
			session.steps['aur_packages'] = spawn(frame, stub, dependency='accounts')
			yield {
				'_modules' : 'aur_packages',
				'status' : 'skipped',
				'next' : 'arch_linux'
			}
			return
		elif not 'packages' in frame.data:
			yield {
				'html' : html,
				'javascript' : javascript,
				'_modules' : 'aur_packages'
			}
		else:
			yield {
				'status' : 'queued',
				'_modules' : 'aur_packages',
				'next' : 'arch_linux'
			}