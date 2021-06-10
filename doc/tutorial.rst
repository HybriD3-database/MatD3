===================
Beginners Tutorials
===================

Here, we provide an aggregated but still incomplete list of our recommended starting tutorials as well as the first steps necessary for new developers for the MatD3 database.

- `The official Django tutorial`_ - this would be the best starting point. We suggest doing the first six parts of the tutorial. The Django homepage has many more useful tutorials on various topics which are all well written. You'll probably come back to those as needed.

- The Django tests are written using the `Selenium framework`_.

- `reStructuredText (RST)`_ - this format is commonly used for writing technical documentation. When making changes, run ``make html`` in the doc directory and then ``open doc/_build/html/index.html`` on your personal computer. If happy with the changes, commit and push. The documentation website (e.g. hybrid3-database.readthedocs.io/en/latest/) then automatically pulls the changes from Github and should be up to date within seconds.

  Before pushing, make sure all tests pass:

  .. code:: bash

    source venv/bin/activate

    python manage.py test --keepdb # --keepdb is not necessary but will usually save time

  If a test fails but you've already committed, you can amend the commit by running

  .. code:: bash

    git commit --amend

- When updating the code, other than documentation, the changes also need to be pulled from the server side. After pushing changes to Github, ``ssh`` to e.g. materials.hybrid3.duke.edu (i.e. the server you have access to) and issue

  .. code:: bash

    cd /var/www/hybrid3-database # Project location on the server

    source venv/bin/activate # Activate the Python environment for this project

    export DJANGO_SETTINGS_MODULE=mainproject.settings

    git pull

    ./manage.py collectstatic --noinput # Update static files if necessary

    ./manage.py migrate # Update Django models if necessary

    sudo systemctl restart hybrid3.socket # Restart the server

  Some of those commands will not have an effect when, for example, there were no changes to the models or no static files were updated. But we suggest running them all of them anyway just to be safe. (Why not create a single alias for all those commands in your .bashrc?)

- The data is stored in two different places - the SQL (MariaDB) database and in the directory /var/www/hybrid3-database/mainproject/media. Thus, two actions need to be taken for backing up all data. For making a copy (a dump) of the SQL data, run

  .. code:: bash

    mysqldump -u <user> -p'<password>' materials > dump.sql

  which creates a file called dump.sql in the current directory. Replace <user> and <password> by the values of DB_USER and DB_PASSWORD found in /var/www/hybrid3-database/.env. The media folder can be backed up simply with ``cp -r`` although we suggest compressing it first. For instance, one might issue

  .. code:: bash

    cd /var/www/hybrid3-database/mainproject/media

    mysqldump -u <user> -p'<password>' materials > dump_58c90cc.sql && mv dump_58c90cc.sql ~

    tar cjf media_58c90cc.tar.bz2 media && mv media_58c90cc.tar.bz2 ~

  where 58c90cc is the short hash of the latest Git commit in this example.

- Basic tutorials on `HTML`_, `CSS`_, and `Javascript`_ - this would be a good starting point for learning the basics of these three languages. For a more complete reference for Javascript, see https://javascript.info/.



.. _The official Django tutorial: https://docs.djangoproject.com/en/3.2/intro/tutorial01/
.. _Selenium framework: https://selenium-python.readthedocs.io/getting-started.html
.. _reStructuredText (RST): https://sphinx-tutorial.readthedocs.io/step-1/
.. _HTML: https://www.w3schools.com/html/html_intro.asp
.. _CSS: https://www.w3schools.com/css/css_intro.asp
.. _Javascript: https://www.w3schools.com/js/js_intro.asp
