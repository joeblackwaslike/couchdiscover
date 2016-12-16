import re
from setuptools import setup

with open('couchdiscover/__init__.py', 'rt') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

with open('README.md', 'rt') as fd:
    readme = fd.read()

setup(
    name='couchdiscover',
    version=version,
    description='Autodiscovery & Clustering for CouchDB 2.0 with Kubernetes',
    long_description=readme,
    keywords = ['couchdb', 'kubernetes', 'cluster'],
    author='Joe Black',
    author_email='joeblack949@gmail.com',
    url='https://github.com/joeblackwaslike/couchdiscover',
    download_url='https://github.com/joeblackwaslike/couchdiscover/tarball/0.2.3',
    license='Apache 2.0',
    packages=['couchdiscover'],
    package_data={'': ['LICENSE']},
    dependency_links=['https://github.com/kelproject/pykube/tarball/e62ff67d60852247b3dec7d1cc9c0b062a15f14b#egg=pykube'],
    install_requires=[
        'CouchDB',
        'requests',
        'pykube'
    ],
    entry_points=dict(
        console_scripts=['couchdiscover = couchdiscover.entrypoints:main']),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Database',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: System :: Clustering',
    ]
)
