# This file is covered by the BSD license. See LICENSE in the root directory.
"""WSGI config for myproject project.

It exposes the WSGI callable as a module-level variable named
``application``.

"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mainproject.settings")

application = get_wsgi_application()
