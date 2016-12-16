"""
CouchDiscover
~~~~~~~~~~~~~

CouchDB 2.0 Autodiscovery for Kubernetes Environments.

Example:
    >>> import couchdiscover
    >>> couchdiscover.entrypoints.main()
"""

from . import config, util, exceptions, kube, couch, manage, entrypoints
from .kube import KubeHostname, KubeAPIClient, KubeInterface
from .couch import CouchServer, CouchInitClient, CouchManager
from .manage import ClusterManager, ContainerEnvironment
from .exceptions import (
    CouchDiscGeneralError,
    CouchDiscHTTPError,
    CouchAddNodeError,
    InvalidKubeHostnameError
)

__title__ = 'couchdiscover'
__version__ = '0.2.3'
__build__ = 0x000203
__author__ = "Joe Black <joe@valuphone.com>"
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2016 Joe Black'


util.setup_logging(
    level=config.LOG_LEVEL, fmt=config.LOG_FORMAT, date=config.DATE_FORMAT)
