# This file is covered by the BSD license. See LICENSE in the root directory.
"""Define global variables for the Django templates."""
from .settings import MATD3_NAME


def title(request):
    return {'matd3_name': MATD3_NAME}
