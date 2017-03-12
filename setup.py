import os
import elixr.sax
from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.md')) as f:
    CHANGES = f.read()


requires = [
    'sqlalchemy',
    
    # deps not on pypi
    'elixr.core'
]

tests_requires = [
    'bcrypt',
    'pytest',
    'pytest-cov'
]

setup(
    name='elixr.sax',
    version=elixr.sax.__version__,
    description='Reusable types, models and utilities built around SQLAlchemy ORM',
    long_description=README + '\n\n' + CHANGES,
    author=elixr.sax.__author__,
    author_email='info@hazeltek.com',
    maintainer='Abdul-Hakeem Shaibu',
    maintainer_email='hkmshb@gmail.com',
    url='https://bitbucket.org/hkmshb/elixr',
    keywords='elixr.sax, elixr SqlAlchemy eXtension',
    zip_safe=False,
    packages=find_packages(),
    platforms='any',
    install_requires=requires,
    extras_require={ 'testing': tests_requires },
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