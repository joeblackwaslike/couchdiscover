"""
couchdiscover.config
~~~~~~~~~~~~~~~~~~~~

This module holds configuration constants.

:copyright: (c) 2016 by Joe Black.
:license: Apache2.
"""

import os

ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')

LOG_FORMAT = '%(asctime)s %(levelname)s %(module)s.%(funcName)s] %(message)s'
DATE_FORMAT = '%m/%d/%Y %I:%M:%S %p'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG').upper()

DEFAULT_CREDS = ('admin', 'secret')
DEFAULT_PORTS = (5984, 5986)

DEV_KUBECONFIG_PATH = "~/.kube/config"
DEV_HOST = 'couchdb-0.couchdb.default.svc.cluster.local'

del os
