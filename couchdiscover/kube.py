"""
couchdiscover.kube
~~~~~~~~~~~~~~~~~~

This module contains constants and classes that abstract the details of
working with the kubernetes api as higher level objects.

:copyright: (c) 2016 by Joe Black.
:license: Apache2.
"""

import base64

import pykube

from . import config, util
from .exceptions import InvalidKubeHostnameError


class KubeHostname:
    """Represents a kubernetes hostname.

    A Kubernetes hostname where individual parts can be manipulated and the
    hostname is updated.  str(host) will return the hostname as a string.
    """

    def __init__(self, fqdn):
        self._init_from_fqdn(fqdn)

    def _verify_fqdn(self, fqdn):
        if len(fqdn.split('.')) < 5:
            raise InvalidKubeHostnameError(fqdn)

    @property
    def fqdn(self):
        """Returns a calculated FQDN for the hostname."""
        return self._join_fqdn(
            self.node, self.service, self.namespace, self.domain)

    @fqdn.setter
    def fqdn(self, fqdn):
        """"Allows a new kube hostname object to be set by manipulating the
        FQDN.
        """
        self._init_from_fqdn(fqdn)

    @property
    def node(self):
        """Retrieves the first part of the kubernetes hostname.
        Example: `couchdb-0`
        """
        return self._join_node(self.statefulset, self.index)

    @node.setter
    def node(self, node):
        """Allows the first part of the kubernetes hostname to be set and a
        new hostname object recalculated.
        """
        self.statefulset, self.index = self._split_node(node)

    @property
    def is_master(self):
        """Determines whether the index is 0 for when the master of a
        StatefulSet needs to be determined."""
        return self.index == 0

    def __repr__(self):
        class_name = type(self).__name__
        return "{}('{}')".format(class_name, self.fqdn)

    def __str__(self):
        return self.fqdn

    @staticmethod
    def _split_fqdn(fqdn):
        node, service, namespace, _, domain = fqdn.split('.', 4)
        return node, service, namespace, domain

    @staticmethod
    def _split_node(node):
        statefulset, index = node.split('-')
        index = int(index)
        return statefulset, index

    def _init_from_fqdn(self, fqdn):
        node, service, namespace, domain = self._split_fqdn(fqdn)
        statefulset, index = self._split_node(node)
        self.service = service
        self.namespace = namespace
        self.domain = domain
        self.statefulset = statefulset
        self.index = index

    @staticmethod
    def _join_fqdn(node, service, namespace, domain):
        return '.'.join((node, service, namespace, 'svc', domain))

    @staticmethod
    def _join_node(statefulset, index):
        return '{}-{}'.format(statefulset, str(index))

    def clone(self, master=False, index=None):
        """Clone's a copy of the current KubeHostname object.

        Options include requesting the KubeHostname for the master or by
        passing an index.
        """
        new = type(self)(self.fqdn)
        if index:
            new.index = index
        if master:
            new.index = 0
        return new


class KubeAPIClient:
    """Contains the lower level functions for manipulating and retrieving
    objects from the kubernetes api.
    """
    def __init__(self, env=None, namespace=None):
        self.env = env
        self.namespace = namespace
        self.api = self._get_api()

    def _get_api(self):
        if self.env == 'dev':
            api = pykube.http.HTTPClient(
                pykube.KubeConfig.from_file(config.DEV_KUBECONFIG_PATH))
        else:
            api = pykube.http.HTTPClient(
                pykube.KubeConfig.from_service_account())
        return api

    def _get_api_object(self, resource, name=None, selector=None,
                        namespace=None):
        if not namespace:
            namespace = self.namespace
        if not issubclass(resource, pykube.objects.APIObject):
            raise pykube.PyKubeError('No object by type: %s', resource)
        req = pykube.query.Query(
            self.api, resource, namespace=namespace)
        if name:
            req = req.get_by_name(name)
        if selector:
            req = req.filter(selector=selector)
        if req.exists:
            return req.obj

    def get_pod(self, name=None, selector=None, namespace=None):
        """Get's pod by name or/or selector."""
        return self._get_api_object(pykube.Pod, name, selector, namespace)

    def get_service(self, name=None, selector=None, namespace=None):
        """Get's service by name or/or selector."""
        return self._get_api_object(pykube.Service, name, selector, namespace)

    def get_endpoint(self, name=None, selector=None, namespace=None):
        """Get's endpoint by name or/or selector."""
        return self._get_api_object(pykube.Endpoint, name, selector, namespace)

    def get_statefulset(self, name=None, selector=None, namespace=None):
        """Get's statefulset by name or/or selector."""
        return self._get_api_object(
            pykube.StatefulSet, name, selector, namespace)

    def get_secret(self, name=None, key=None, selector=None, namespace=None):
        """Get's secret by name or/or selector."""
        sec = self._get_api_object(pykube.Secret, name, selector, namespace)
        if key:
            sec = self._get_key_decoded(sec, key)
        return sec

    def get_configmap(self, name=None, key=None, selector=None,
                      namespace=None):
        """Get's configmap by name or/or selector."""
        cm = self._get_api_object(pykube.ConfigMap, name, selector, namespace)
        if key:
            cm = cm['data'].get(key)
        return cm

    @staticmethod
    def _get_key_decoded(obj, key):
        val = obj['data'].get(key)
        if val:
            obj = base64.b64decode(val).decode()
        return obj

    @staticmethod
    def _get_container(statefulset=None, container=None):
        if statefulset:
            pod = statefulset['spec']['template']
        if container:
            for cont in pod['spec']['containers']:
                if cont['name'] == container:
                    return cont
        else:
            return pod

    @staticmethod
    def _key_container_env(container):
        return {item['name']: item for item in container['env']}

    def _lookup_env_value(self, env):
        if env.get('value'):
            return env.get('value')
        elif env.get('valueFrom'):
            v_from = env.get('valueFrom')
            if v_from.get('fieldRef'):
                # don't implement downward api here, unnecessary
                return ''
            elif v_from.get('secretKeyRef'):
                ref = v_from.get('secretKeyRef')
                return self.get_secret(name=ref['name'], key=ref['key'])
            elif v_from.get('configMapKeyRef'):
                ref = v_from.get('configMapKeyRef')
                return self.get_configmap(name=ref['name'], key=ref['key'])

    def get_environment(self, statefulset, container):
        """Get's the environment for a container of a statefulset.

        Environment returned is a dictionary key'd by environment variable
        name, and who's value has been resolved in the case of externally
        referenced configmaps and secrets.
        """
        statefulset = self.get_statefulset(statefulset)
        cont = self._get_container(statefulset, container)
        env = self._key_container_env(cont)
        return {k: self._lookup_env_value(v) for k, v in env.items()}


class KubeInterface(util.ReprMixin):
    """This class exposes the information we need from kubernetes as lazy
    evaluated properties, caching provided by pykube.
    """
    _public_attrs = ('hosts', 'ports', 'creds', 'cluster_size')

    def __init__(self, host, env=None):
        self._host = host
        self.api = KubeAPIClient(env=env, namespace=self._host.namespace)

    def _fqdn_from_node(self, node):
        host = self._host.clone()
        host.node = node
        return str(host)

    @property
    def hosts(self):
        """Returns a tuple of full fqdn's for all nodes in the CouchDB
        statefulset.
        """
        service = self._host.service
        endp = self.api.get_endpoint(service)
        hosts = [self._fqdn_from_node(address['hostname'])
                 for address in endp['subsets'][0]['addresses']]
        return tuple(sorted(hosts))

    @property
    def ports(self):
        """Returns a tuple of ports for the CouchDB statefulset."""
        service = self._host.service
        endp = self.api.get_endpoint(service)
        ports = [port['port'] for port in endp['subsets'][0]['ports']]
        return tuple(sorted(ports))

    @property
    def creds(self):
        """Returns a tuple of user/pass for the CouchDB statefulset."""
        statefulset = self._host.statefulset
        env = self.api.get_environment(statefulset, statefulset)
        user = env.get('COUCHDB_ADMIN_USER', config.DEFAULT_CREDS[0])
        password = env.get('COUCHDB_ADMIN_PASS', config.DEFAULT_CREDS[1])
        return (user, password)

    @property
    def cluster_size(self):
        """Returns the expected cluster size by qerying the
        `COUCHDB_CLUSTER_SIZE` environment variable, and falling back to the
        number of replicas in the statefulset.  For most purposes, you can rely
        on default behavior here.
        """
        statefulset = self._host.statefulset
        ss = self.api.get_statefulset(statefulset)
        env = self.api.get_environment(statefulset, statefulset)
        size = ss['spec']['replicas']
        return env.get('COUCHDB_CLUSTER_SIZE', size)
