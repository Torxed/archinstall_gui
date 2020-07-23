import sys
import importlib.util
from os import urandom
from hashlib import sha512
from subprocess import Popen, STDOUT, PIPE

# def _onliest_singleness(entropy_length=256):
def gen_uid(entropy_length=256):
	return sha512(urandom(entropy_length)).hexdigest()