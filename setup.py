from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in kh_fama/__init__.py
from kh_fama import __version__ as version

setup(
	name="kh_fama",
	version=version,
	description="KH Fama",
	author="hammad",
	author_email="hammad@srptechs.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
