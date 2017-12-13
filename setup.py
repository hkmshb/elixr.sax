# note: when installing via pip include flag `--process-dependency-links`

import os
from setuptools import setup, find_packages


## meta data
__version__ = "0.5"
__author__  = 'Hazeltek Solutions'


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.md')) as f:
    CHANGES = f.read()


requires = [
    'sqlalchemy',
    'elixr.base==0.4'
]

tests_requires = [
    'bcrypt',
    'openpyxl',
    'pytest',
    'pytest-cov'
]

setup(
    name='elixr.sax',
    version=__version__,
    description='Reusable types, models and utilities built around SQLAlchemy ORM',
    long_description=README + '\n\n' + CHANGES,
    author=__author__,
    author_email='info@hazeltek.com',
    maintainer='Abdul-Hakeem Shaibu',
    maintainer_email='hkmshb@gmail.com',
    url='https://bitbucket.org/hazeltek-dev/elixr.sax',
    keywords='elixr.sax, elixr SqlAlchemy eXtension',
    zip_safe=False,
    packages=find_packages(),
    platforms='any',
    install_requires=requires,
    extras_require={
        'test': tests_requires
    },
    dependency_links=[
        'https://bitbucket.org/hazeltek-dev/elixr.base/get/v0.4.tar.gz#egg=elixr.base-0.4',
    ],
    classifiers=[
        'Development Status :: *',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: ISV',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5'
    ]
)
