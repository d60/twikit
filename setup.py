from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

setup(
    name='twikit',
    version='1.0.1',
    install_requires=['httpx', 'sphinx_rtd_theme '],
    description='Twitter API wrapper for python with no API key required.',
    long_description=long_description,
    long_description_content_type='text/markdown'
)
