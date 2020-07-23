import setuptools, glob, os, shutil

with open("README.md", "r") as fh:
	long_description = fh.read()

## Build steps (prerequisits)
#  TODO: Perhaps not rename it core.py when copying in the lib?
#        Probably doesn't matter to much, but looks odd.
#        Can we re-use the __init__.py from main repo?
if not os.path.isdir('slimHTTP'):
	os.makedirs('./slimHTTP')
if not os.path.isfile('./slimHTTP/core.py'):
	shutil.copy2('./slimHTTP.py', './slimHTTP/core.py')
if not os.path.isfile('./slimHTTP/__init__.py'):
	with open('./slimHTTP/__init__.py', 'w') as __init__:
		__init__.write('from .core import *\n')
if not os.path.isdir('./slimHTTP/examples'):
	shutil.copytree('./examples', './slimHTTP/examples')

setuptools.setup(
	name="slimHTTP",
	version="1.0.1rc5",
	author="Anton Hvornum",
	author_email="anton@hvornum.se",
	description="A minimalistic non-threaded HTTP server written in Python. Supports REST & WebSockets¹.",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/Torxed/slimHTTP",
	packages=setuptools.find_packages(),
	classifiers=[
		"Programming Language :: Python :: 3.8",
		"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
		"Operating System :: POSIX",
		"Operating System :: Microsoft",
	],
	python_requires='>=3.8',
	package_data={'slimHTTP': glob.glob('examples/*.py')},
)