"""
couchdiscover.exceptions
~~~~~~~~~~~~~~~~~~~~~~~~

This module contains custom exceptions for use in this package, some which
add context.

:copyright: (c) 2016 by Joe Black.
:license: Apache2.
"""

import collections


class CustomErrorMixin:
    """Provides the ability to customize exceptions with context

    Usually works off of a message template stored in :attr:`_msg` by
    merging it as such self._msg.format(**kwargs).

    If args are provided, they are interpreted as usual and added to the end.

    The methods of this mixin are pretty generic and overriding them allows
    for much more advanced customization of the context.
    """

    _msg = ''

    def __init__(self, *args, **kwargs):
        kwargs = self._process_kwargs(kwargs)
        args = self._process_args(args, kwargs)
        super().__init__(*args)

    def _process_kwargs(self, kwargs=None):
        if not kwargs:
            kwargs = {}
        kwargs = collections.defaultdict(str, kwargs)
        for key, val in kwargs.items():
            setattr(self, key, val)
        return kwargs

    def _process_msg(self, kwargs):
        msg = ''
        if kwargs:
            msg = self._msg.format(**kwargs)
        return msg

    def _process_orig_msg(self, args):
        msg, *args = args
        return msg % tuple(args)

    def _merge_msgs(self, msg, orig):
        if msg:
            if orig:
                msg += ' ' + orig
        else:
            msg = orig
        return msg

    def _process_args(self, args, kwargs):
        msg = self._process_msg(kwargs)
        if args:
            orig = self._process_orig_msg(args)
            msg = self._merge_msgs(msg, orig)
        args = (msg,)
        return args


class CouchDiscGeneralError(CustomErrorMixin, Exception):
    """Generic catch all exception.

    Catch this exception in a except block to catch all errors related to this
    package.
    """


class CouchDiscHTTPError(CouchDiscGeneralError):
    """Generic exception during HTTP request

    Adds additional context from request and response to error message.

    Add the `req` kwarg when raising error to attach request context.

    * Overrides `_process_kwargs` to parse out request and response
    * Overrides `_process_msg` to add req and resp context to error message
    * Overrides `_merge_msgs` to allow the orig message to provide the message

    Example:
    >>> import requests
    >>> r = requests.get('http://httpbin.org/user-agent')
    >>> raise CouchDiscHTTPError('Error', req=r)
    CouchDiscHTTPError: Error req(GET http://httpbin.org/user-agent None)
    resp(200 {"user-agent": "python-requests/2.12.3"})
    """

    def _process_kwargs(self, kwargs=None):
        if not kwargs:
            kwargs = {}
        if kwargs.get('req'):
            kwargs['resp'] = kwargs.pop('req')
            if hasattr(kwargs.get('resp'), 'request'):
                kwargs['req'] = kwargs['resp'].request
        kwargs = super()._process_kwargs(kwargs)
        return kwargs

    def _merge_msgs(self, extra, orig):
        return super()._merge_msgs(orig, extra)

    def _process_msg(self, kwargs=None):
        if not kwargs:
            kwargs = {}
        extra = ''
        req = kwargs.get('req')
        if req:
            extra += 'req(%s %s %s)' % (req.method, req.url, req.body)
        resp = kwargs.get('resp')
        if resp:
            if req:
                extra += ' '
            extra += 'resp(%s %s)' % (resp.status_code, resp.text)
        return extra


class CouchAddNodeError(CouchDiscHTTPError):
    """Error adding node to master."""


class InvalidKubeHostnameError(CouchDiscGeneralError):
    """Invalid kubernetes hostname

    Raised when a host doesn't match the signature of a kubernetes statefulset
    hostname.

    Provides a `_msg` that includes the host passed in as a kwarg.

    Example:
    >>> raise InvalidKubeHostnameError(host='google.com')
    InvalidKubeHostnameError: The Hostname: google.com doesn't match the
    signature of a kubernetes statefulset hostname.
    """

    _msg = ("The Hostname: {host} doesn't match the signature of a kubernetes"
            " statefulset hostname.")
