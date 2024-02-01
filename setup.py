from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

setup(
    name='twikit',
    version='1.0.6',
    install_requires=['requests'],
    description='Twitter API wrapper for python with **no API key required**.',
    long_description=long_description,
    long_description_content_type='text/markdown'
)
