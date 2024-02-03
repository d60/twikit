from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

setup(
    name='twikit',
    version='1.1.1',
    install_requires=['httpx'],
    description='Twitter API wrapper for python with **no API key required**.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    url='https://github.com/d60/twikit'
)
