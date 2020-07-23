import setuptools, glob, os, shutil

with open("README.md", "r") as fh:
	long_description = fh.read()

## Build steps (prerequisits)
#  TODO: Perhaps not rename it core.py when copying in the lib?
#        Probably doesn't matter to much, but looks odd.
#        Can we re-use the __init__.py from main repo?
if not os.path.isdir('slimWS'):
	os.makedirs('./slimWS')
if not os.path.isfile('./slimWS/core.py'):
	shutil.copy2('./slimWS.py', './slimWS/core.py')
if not os.path.isfile('./slimWS/__init__.py'):
	with open('./slimWS/__init__.py', 'w') as __init__:
		__init__.write('from .core import *\n')
#if not os.path.isdir('./slimWS/examples'):
#	shutil.copytree('./examples', './slimWS/examples')

setuptools.setup(
	name="slimWS",
	version="1.0.0rc2",
	author="Anton Hvornum",
	author_email="anton@hvornum.se",
	description=" minimal WebSocket framework and works as a HTTP upgrader for slimHTTP.",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/Torxed/slimWS",
	packages=setuptools.find_packages(),
	classifiers=[
		"Programming Language :: Python :: 3.8",
		"License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
		"Operating System :: POSIX",
		"Operating System :: Microsoft",
	],
	python_requires='>=3.8'
#	package_data={'slimWS': glob.glob('examples/*.py')},
)