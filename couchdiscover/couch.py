"""
couchdiscover.couch
~~~~~~~~~~~~~~~~~~~

This module contains constants and classes that abstract the details of
working with and clustering CouchDB 2.0 as higher level objects.

:copyright: (c) 2016 by Joe Black.
:license: Apache2.
"""

import time
import json
import logging
import socket

import requests
import couchdb

from . import config, util
from .exceptions import CouchAddNodeError


ADMIN_ONLY_DBS = ('_dbs', '_nodes', '_replicator', '_users')
log = logging.getLogger(__name__)


class CouchServer(util.ReprMixin):
    """Encapsulates the logic for interacting with CouchDB 2.0 Server"""
    _public_attrs = ('url', 'type', 'up')

    def __init__(self, proto='http', host='localhost',
                 port=config.DEFAULT_PORTS[0], creds=config.DEFAULT_CREDS):
        self._up = None
        self._args = dict(proto=proto, host=host, port=int(port), auth=creds)
        self.url = self._get_server_url()
        self._couch = couchdb.Server(self.url)
        self._wrapped = self._couch
        self._session = self._get_session()
        self.type = self._detect_type()

    def _get_server_url(self):
        args = self._args
        url = []
        url.append('{}://'.format(args['proto']))
        if args['auth']:
            url.append('{}:{}@'.format(*args['auth']))
        url.append(args['host'])
        url.append(':{}'.format(args['port']))
        url = ''.join(url)
        return url

    def _get_session(self):
        sess = requests.Session()
        sess.headers.update({'Content-Type': 'application/json'})
        if self._args['auth']:
            sess.auth = self._args['auth']
        return sess

    def _detect_type(self):
        all_dbs = self.all_dbs()
        if isinstance(all_dbs, list):
            if '_nodes' in all_dbs:
                return 'admin'
            else:
                return 'data'

    def _build_url(self, uri=None):
        if uri:
            if not uri.startswith('/'):
                uri = '/' + uri
        return self.url + uri

    @property
    def up(self):
        """Returns True if server is up."""
        try:
            if self.version():
                return True
        except ConnectionRefusedError:
            pass

    def __contains__(self, key):
        all_dbs = self.all_dbs()
        if all_dbs:
            return key in all_dbs

    def __getitem__(self, key):
        return self._couch[key]

    def __delitem__(self, key):
        del self._couch[key]

    @util.passthrough
    def config(self, *args, **kwargs):
        """Displays server configuration."""
        pass

    @util.passthrough
    def create(self, *args, **kwargs):
        """Create a database."""
        pass

    @util.passthrough
    def delete(self, *args, **kwargs):
        """Delete a database."""
        pass

    @util.passthrough
    def stats(self, *args, **kwargs):
        """Server stats."""
        pass

    @util.passthrough
    def version(self, *args, **kwargs):
        """Gets version of CouchDB."""
        pass

    def all_dbs(self):
        """Returns a generator iterating all DB objects."""
        return self.request(uri='/_all_dbs')

    def request(self, verb='get', uri=None, params=None, data=None,
                headers=None, files=None):
        """Send a low level HTTP request."""
        url = self._build_url(uri)
        sess = self._session
        try:
            req = sess.request(verb, url, params, data, headers, files=files)
            try:
                json_ = req.json()
                return json_
            except json.JSONDecodeError:
                return {}
        except requests.ConnectionError:
            pass


class CouchInitClient:
    """Encapsulates a pair of CouchServer objects for admin and data ports."""
    def __init__(self, host='localhost', ports=config.DEFAULT_PORTS,
                 creds=config.DEFAULT_CREDS, proto='http'):
        self._secure = False
        self._args = dict(
            proto=proto, host=str(host), ports=ports, creds=creds)
        self._wait_for_couch()
        self._servers = self._setup_servers()
        self._upgrade_auth_if_enabled()

    def _wait_for_couch(self):
        args = self._args
        url = 'http://{}:{}/_up'.format(args['host'], args['ports'][0])
        up = False
        log.info('Waiting for host: %s to be up', url)
        while not up:
            try:
                req = requests.get(url)
                up = True
                log.info('Host is up')
                del req
            except requests.RequestException:
                log.info('Host: %s not up yet, retrying in 5s', url)
                time.sleep(5)

    def _upgrade_auth_if_enabled(self):
        status = self.status
        if status == 'cluster_disabled':
            self._secure = False
        else:
            self._upgrade_auth()

    def _upgrade_auth(self):
        self._secure = True
        self._servers = self._setup_servers(auth=True)

    @property
    def status(self):
        """Returns the cluster_setup state string."""
        req = self.cluster_setup(action='status')
        if req.get('error'):
            state = 'auth_required'
        else:
            state = req['state']
        return state

    @property
    def disabled(self):
        """Returns True if status is `cluster_disabled`."""
        return self.status == 'cluster_disabled'

    @property
    def enabled(self):
        """Returns True if status is `cluster_enabled`"""
        return self.status == 'cluster_enabled'

    @property
    def finished(self):
        """Returns True if status is `cluster_finished`"""
        return self.status == 'cluster_finished'

    def __repr__(self):
        cls_name = self.__class__.__name__
        servers = ['{}: {}'.format(k, v) for k, v in self._servers.items()]
        servers = ', '.join(servers)
        attrs = 'status: {}, servers: {}'.format(self.status, servers)
        return '{cls}({attrs})'.format(cls=cls_name, attrs=attrs)

    def __str__(self):
        return self._args['host']

    def __getitem__(self, key):
        server = self._server_for(key)
        return server[key]

    def _setup_servers(self, auth=False):
        servers = {}
        args = self._args
        for port in args['ports']:
            this_auth = args['creds'] if auth else None
            server = CouchServer(args['proto'], args['host'], port, this_auth)
            servers[server.type] = server
        return servers

    def _server_for(self, db):
        if db in ADMIN_ONLY_DBS:
            key = 'admin'
        else:
            key = 'data'
        return self._servers[key]

    def call(self, server, method, *args, **kwargs):
        """Call a bound method of the CouchServer object."""
        server = self._servers.get(server)
        bound_method = getattr(server, method)
        return bound_method(*args, **kwargs)

    def request(self, server='data', verb='get', uri=None, params=None,
                data=None, headers=None, files=None):
        """Wraps the `CouchServer.request`, dispatching by `server`."""
        server = self._servers.get(server)
        return server.request(verb, uri, params, data, headers, files)

    def _build_cluster_setup_payload(
            self, action='add', host=None, port=None, creds=None):
        """Builds a data payload for `request`."""
        if not host:
            host = self._args['host']
        if not port:
            port = self._args['ports'][0]
        if not creds:
            creds = self._args['creds']

        data = None
        if action == 'add':
            data = {'action': 'add_node', 'host': host, 'port': port}
        elif action == 'enable':
            data = {'action': 'enable_cluster'}
        elif action == 'finish':
            data = {'action': 'finish_cluster'}

        if action in ('add', 'enable') and creds and len(creds) == 2:
            data['username'], data['password'] = creds

        if isinstance(data, dict):
            data = json.dumps(data)
        return data

    def cluster_setup(self, action='add', host=None, port=None, creds=None):
        """Creates and submits a request to the `cluster_setup` endpoint."""
        if action == 'status':
            verb = 'get'
        elif action in ('add', 'enable', 'finish'):
            verb = 'post'
        else:
            raise requests.HTTPError('%s is not a valid action', action)

        data = self._build_cluster_setup_payload(action, host, port, creds)
        req = self.request(
            server='data', verb=verb, uri='/_cluster_setup', data=data)
        return req

    @staticmethod
    def host_is_valid(host):
        """Returns true if the host passed can be resolved by DNS."""
        try:
            socket.gethostbyname(host)
            return True
        except socket.gaierror:
            return False

    def _test_node(self, node):
        """Runs several tests and returns True if node passes."""
        host = node._args['host']
        if all([self.host_is_valid(host), node.up()]):
            if not self._node_in_nodes('couchdb@{}'.format(host)):
                return True

    def enable(self):
        """Enables the current node."""
        req = self.cluster_setup(action='enable')
        if req.get('ok'):
            self._upgrade_auth()

    def add_node(self, remote):
        """Add's a new node to the current node."""
        if self._test_node(remote):
            args = remote._args
            req = self.cluster_setup(
                'add', args['host'], args['ports'][0], args['creds'])
            if req and isinstance(req, dict) and req.get('ok') is True:
                return req
            else:
                raise CouchAddNodeError(
                    'error adding node: %s resp: %s', remote, req)

    def finish(self):
        """Finish the cluster."""
        return self.cluster_setup(action='finish')

    def nodes(self):
        """Get all nodes in the _nodes db of current node."""
        return tuple([n for n in self['_nodes']])

    def _node_in_nodes(self, node):
        """Return True if `node` is in _nodes db of current node."""
        nodes = self.nodes()
        return node in nodes

    def membership(self):
        """Returns the results of the `/_membership` endpoint."""
        return self.request(server='data', uri='/_membership')

    def up(self):
        """Returns if both CouchServer's return True for `s.up`"""
        return all([s.up for s in self._servers.values()])


class CouchManager:
    """Contains configuration data and topology of couch cluster."""
    def __init__(self, env):
        self.host = env.host
        self.ports = env.ports
        self.creds = env.creds
        self.local = CouchInitClient(env.host, env.ports, env.creds)
        if not self.is_master:
            mhost = env.host.clone(master=True)
            self.master = CouchInitClient(mhost, env.ports, env.creds)

    def __repr__(self):
        clss = type(self).__name__
        attrs = ['{}: {}'.format(a, getattr(self, a)) for a in
                 ('status', 'is_master', 'ports', 'creds')]
        attrs = ', '.join(attrs)
        return '{}({})'.format(clss, attrs)

    @property
    def status(self):
        """Returns the `status` of wrapped local node."""
        return self.local.status

    @property
    def enabled(self):
        """Returns the `enabled` of wrapped local node."""
        return self.local.enabled

    @property
    def disabled(self):
        """Returns the `disabled` of wrapped local node."""
        return self.local.disabled

    @property
    def finished(self):
        """Returns the `finished` of wrapped local node."""
        return self.local.finished

    @property
    def is_master(self):
        """Returns whether local node is the `master`."""
        return self.host.index == 0

    def enable(self):
        """Enable the local node but with error checking and logging."""
        if self.enabled:
            log.warning('Already enabled')
        elif self.finished:
            log.warning("Can't enable finished cluster: %s", self.local)
        else:
            log.info('Enabling local: %s', self.local)
            return self.local.enable()

    def finish(self):
        """Finish cluster but with error checking and logging."""
        if self.disabled:
            log.warning("Can't finish cluster when disabled: %s", self.local)
        elif self.finished:
            log.warning('Cluster already finished: %s', self.local)
        else:
            log.info('Finishing cluster: %s', self.local)
            return self.master.finish()

    def wait_for_enabled_master(self):
        """Blocking wait until master is enabled.

        Prevents a race condition where non-master node tries to
        manipulate the state of the cluster before the master is enabled.
        """
        if self.is_master:
            log.warning("Can't wait for master when master: %s", self.local)
        else:
            while not self.master.enabled:
                log.info('Waiting for master: %s to be enabled', self.master)
                time.sleep(5)

    def add_to_master(self, node=None):
        """Add the local node to master with error checking and logging."""
        if not node:
            node = self.local
        if self.is_master:
            log.warning("Can't add self to self, master: %s", self.master)
        else:
            self.wait_for_enabled_master()
            log.info('Adding: %s to master: %s', node, self.master)
            return self.master.add_node(node)
