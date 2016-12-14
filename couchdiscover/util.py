"""
couchdiscover.util
~~~~~~~~~~~~~~~~~~~

This module contains various utility functions and Mixins.

:copyright: (c) 2016 by Joe Black.
:license: Apache2.
"""

import logging


# needs to have a reference to the wrapped object @ self._wrapped
def passthrough(func):
    """A Decorator that will call the same named function on the wrapped
    object.

    Expected interface requires a `_wrapped` attribute on the wrapper object
    to contain a pointer to the wrapped object.
    """
    def wrap(self, *args, **kwargs):
        """This function allows arguments to be passed."""
        caller = func.__name__
        method = getattr(self._wrapped, caller)
        return method(*args, **kwargs)
    return wrap


def setup_logging(level, fmt, date):
    """This will setup logging for the module."""
    log = logging.getLogger('couchdiscover')
    loglvl = getattr(logging, level)
    log.setLevel(loglvl)

    chand = logging.StreamHandler()
    chand.setLevel(loglvl)
    chand.setFormatter(logging.Formatter(fmt, date))
    log.addHandler(chand)

    logging.raiseExceptions = False
    return log


class ReprMixin:
    """A mixin that does automatic repr configuration.

    Expected interface requires a `_public_attrs` attribute which is an
    iterable of public properties you want to expose through `__repr__`.
    """
    _public_attrs = ()

    def __repr__(self):
        clss = type(self).__name__
        attrs = ['{}: {}'.format(a, getattr(self, a))
                 for a in self._public_attrs]
        attrs = ', '.join(attrs)
        return '{}({})'.format(clss, attrs)
