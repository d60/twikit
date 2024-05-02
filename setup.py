import re
from pathlib import Path

from setuptools import setup

long_description = Path('README.md').read_text(encoding='utf-8')
version = re.findall(r"__version__ = '(.+)'", Path('./twikit/__init__.py').read_text())[0]
requirements = Path('requirements.txt').read_text().splitlines()

setup(
    name='twikit',
    version=version,
    install_requires=requirements,
    python_requires='>=3.10',
    description='Twitter API wrapper for python with **no API key required**.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    url='https://github.com/d60/twikit',
    author='Your Name',
    author_email='your.email@example.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.10',
    ],
    package_data={'twikit': ['py.typed']},
)
