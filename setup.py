import re
# import ez_setup
# ez_setup.use_setuptools()

from setuptools import setup

with open('couchdiscover/__init__.py', 'rt') as fd:
    VERSION = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not VERSION:
    raise RuntimeError('Cannot find version information')

with open('README.md', 'rt') as fd:
    README = fd.read()

setup(
    name='couchdiscover',
    version=VERSION,
    description='Autodiscovery & Clustering for CouchDB 2.0 with Kubernetes',
    long_description=README,
    keywords = ['couchdb', 'kubernetes', 'cluster'],
    author='Joe Black',
    author_email='joeblack949@gmail.com',
    url='https://github.com/joeblackwaslike/couchdiscover',
    download_url='https://github.com/joeblackwaslike/couchdiscover/tarball/0.2.2',
    license='Apache 2.0',
    packages=['couchdiscover'],
    package_data={'': ['LICENSE']},
    dependency_links=['https://github.com/kelproject/pykube/tarball/cd5b511474bf8854d122af371681fb1dc467a1b9#egg=pykube'],
    install_requires=['CouchDB', 'requests', 'pykube'],
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
