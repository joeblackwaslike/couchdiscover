"""
couchdiscover.entrypoints
~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains functions that exist as entrypoints into the package.

:copyright: (c) 2016 by Joe Black.
:license: Apache2.
"""

from . import config, manage


def main():
    """main

    Main entrypoint executed by bin stub: `couchdiscover`.
    """
    man = manage.ClusterManager(env=config.ENVIRONMENT)
    return man.run()
