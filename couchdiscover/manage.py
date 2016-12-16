"""
couchdiscover.manage
~~~~~~~~~~~~~~~~~~~~

This module contains the main logic and highest level management objects along
with their configuration.

:copyright: (c) 2016 by Joe Black.
:license: Apache2.
"""

import time
import logging
import socket

from . import config, couch, kube, util
from .exceptions import InvalidKubeHostnameError

ONE_DAY = 60 * 60 * 24
log = logging.getLogger(__name__)


class ContainerEnvironment(util.ReprMixin):
    """Represents a self configuring environment object that can be passed to
    initialize other objects.
    """
    _public_attrs = ('index', 'statefulset', 'cluster_size', 'ports', 'creds')

    def __init__(self, env=None, host=None):
        self.env = env
        self._setup_environment(host)

    def _get_host(self, host=None):
        if not host:
            if self.env == 'dev':
                host = config.DEV_HOST
            else:
                host = socket.getfqdn()
        self._raise_if_host_invalid(host)
        return kube.KubeHostname(host)

    @staticmethod
    def _test_host(host):
        return len(host.split('.')) > 4

    def _raise_if_host_invalid(self, host):
        if not self._test_host(host):
            raise InvalidKubeHostnameError(host)

    def _setup_environment(self, host=None):
        self.host = self._get_host(host)
        self.kube = kube.KubeInterface(self.host, env=self.env)

    def reload(self):
        """Reload environment."""
        self._setup_environment()

    @property
    def index(self):
        """Represents the ordinal index 0-N of current node."""
        return self.host.index

    @property
    def statefulset(self):
        """Returns the statefulset name of the current node."""
        return self.host.statefulset

    @property
    def ports(self):
        """Returns the ports used by the CouchDB statefulset."""
        return self.kube.ports

    @property
    def creds(self):
        """Returns the auth credentials for the CouchDB statefulset."""
        return self.kube.creds

    @property
    def cluster_size(self):
        """Returns the expected cluster size of the CouchDB statefulset."""
        return self.kube.cluster_size

    @property
    def first_node(self):
        """Returns True if first node in cluster."""
        return self.index == 0

    @property
    def last_node(self):
        """Returns True if last node in cluster."""
        return (self.index + 1) == self.cluster_size

    @property
    def single_node_cluster(self):
        """Returns True if cluster is a single node cluster."""
        return self.cluster_size == 1


class ClusterManager(util.ReprMixin):
    """Represents the cluster manager, containing main logic that drives the
    self configuring of a CouchDB 2.0 cluster.
    """
    _public_attrs = ('env', 'couch')

    def __init__(self, env=None, host=None):
        self.env = ContainerEnvironment(env, host)
        self.couch = couch.CouchManager(self.env)

    def sleep_forever(self):
        """Work here is done, sleep forever.

        This would preferrably exit, but kubernetes only allows RestartPolicy
        to be applied per pod.
        """
        log.info('Done with: %s, sleeping forever', self.couch)
        while True:
            time.sleep(ONE_DAY)

    def run(self):
        """Main logic here, this is where we begin once all environment
        information has been retrieved."""
        log.info('Starting couchdiscover: %s', self.couch)
        if self.couch.disabled:
            log.info('Cluster disabled, enabling')
            self.couch.enable()
        elif self.couch.finished:
            log.info('Cluster already finished')
            self.sleep_forever()

        if self.env.first_node:
            log.info("Looks like I'm the first node")
            if self.env.single_node_cluster:
                log.info('Single node cluster detected')
                self.couch.finish()
        else:
            log.info("Looks like I'm not the first node")
            self.couch.add_to_master()
            if self.env.last_node:
                log.info("Looks like I'm the last node")
                self.couch.finish()
            else:
                log.info("Looks like I'm not the last node")
        self.sleep_forever()
