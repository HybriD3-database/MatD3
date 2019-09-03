===========
Other notes
===========

- Should it be necessary to clean the Django permissions table, run

  .. code:: python

    Permission.objects.all().delete()

  This deletes all permissions. Once makemigrations and migrate are run, only the premissions for tables which are present are rebuilt.

- In order to have an interactive shell, install iPython in the virtual environment (not system wide).

- The command for running tests with Coverage.py is

  .. code:: bash

    coverage run manage.py test && coverage report -m

  Note that the tests are run with ``DEBUG=False``, which means that the CSS and JS files are only searched for in the directory specified by ``STATIC_ROOT``. Thus, it is in general necessary to run

  .. code:: bash

    ./manage.py collectstatic

  before running the tests. In order to save time and not rebuild the test database every time, use the ``--keepdb`` flag with ``./manage.py test``.
