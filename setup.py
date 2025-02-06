import re
from sys import version_info

from setuptools import setup

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

with open('./twikit/__init__.py') as f:
    version = re.findall(r"__version__ = '(.+)'", f.read())[0]


if version_info >= (3, 12, 0):
    js2py_version = 'git+https://github.com/a-j-albert/Js2Py---supports-python-3.13.git'
else:
    js2py_version = 'js2py'


setup(
    name='twikit',
    version=version,
    install_requires=[
        'httpx[socks]',
        'filetype',
        'beautifulsoup4',
        'pyotp',
        'lxml',
        'webvtt-py',
        'm3u8',
        js2py_version
    ],
    python_requires='>=3.8',
    description='Twitter API wrapper for python with **no API key required**.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    url='https://github.com/d60/twikit',
    package_data={'twikit': ['py.typed']}
)
