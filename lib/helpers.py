import sys
import importlib.util
from os import urandom
from hashlib import sha512
from subprocess import Popen, STDOUT, PIPE

# def _onliest_singleness(entropy_length=256):
def gen_uid(entropy_length=256):
	return sha512(urandom(entropy_length)).hexdigest()

def install_base_os(drive, boot_partition, hostname='Archinstall'):
	with archinstall.Installer(drive, boot_partition=boot_partition, hostname=hostname) as installation:
		if installation.minimal_installation():
			installation.add_bootloader()

	## Verified: Installer() has no __exit__ which would break threads etc.