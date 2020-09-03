=================
Development notes
=================

The most important configuration file for the project is ``settings.py`` located under ``mainproject``. This file would need to be reviewed and edited for each instance of the server. Most settings in it are already at reasonable (or correct) values and those that are most likely to be edited are stored in a separate file called ``.env`` in the root directory. This file is part of the Python Decouple tool, which allows you to organize the project's settings without having to edit the version controlled settings file and, most importantly, for keeping secrets out of version control. Each value in ``settings.py`` that is set using the ``config`` function should have a corresponding entry in ``.env``, unless you are satisfied with the default value. See ``env.example`` in the root directory for example contents.

When this is set up, start the server with

.. code:: bash

  ./manage.py runserver

and open ``localhost:8000`` in your web browser. You can browse the site just like the public one, but you will notice that there are no materials in the database. This is because the running instance is connected to an empty database, whether it's MySQL/MariaDB, SQLite, or some other flavor. This can be fixed by importing the database contents from the production server to the local database. Note that it is generally better to use the same database type in both development and production environments. This project is developed with MariaDB in mind and it is recommended for you to set it up on your own computer. In order to use MariaDB, make sure ``USE_SQLITE`` is set to ``False`` in ``.env`` or remove that variable altogether. Then perform the following steps:

  - Install and start the MariaDB server on your computer. Create a database called "materials" for the user "user" (you can change the latter).
  - Copy the database contents from the public server. First, log in to the server, e.g.

  .. code:: bash

     ssh <user>@materials.hybrid3.duke.edu

  - Fetch the entire database contents:

  .. code:: bash

     mysqldump -u <db_user> -p materials > dump.sql

  - Copy the dump file to your computer, e.g.

  .. code:: bash

     scp <user>@materials.hybrid3.duke.edu:/home/<user>/dump.sql .

  - Read the contents into the local database:

  .. code:: bash

    mysql -u user -p materials < dump.sql

  You may now delete the dump file on the server and on your computer.

You might need to adjust some of these steps to reflect your environment. Now restart the development server and you should be able to browse all the materials currently present in the database.

If you want to go back to SQLite instead of MariaDB for development, you can migrate the database to SQLite using the following script:

  https://github.com/dumblob/mysql2sqlite

Next, you should create a superuser:

.. code:: bash

  python manage.py createsuperuser

In order to access the site with admin rights, add ``/admin`` to the url and login as the superuser. The admin page allows editing of all data stored in the database.

Typically, when making changes to the Python source code, the effects are immediately visible at the site. There is no need to even restart the server. New byte-code is automatically regenerated for modified files. However, if you are making changes to the models, it is necessary to ``migrate``. Migrations change the database structure, which depends on changes in the models. Unlike the byte-code, which regenerates itself on-the-fly as needed, any updates to the database need to be performed manually. Thus, if you change a model, things are unlikely to work until you migrate. To create the migration files, type

.. code:: bash

  python manage.py makemigrations

This creates a file in the migrations directory that explains the changes that were made to the models, but it does not change anything about the database yet. The idea is to give you a chance to review the changes before applying them and, if necessary, make further modifications by hand. Next, run the migrations (this will write and apply the SQL statements for you) with

.. code:: bash

  python manage.py migrate

Once you are satisfied with the changes on your local machine, the changes
need to be synchronized with the real website. This is done using the Git version control system.


Git
===

Run

.. code:: bash

  git status

to see which files have been modified. Run

.. code:: bash

  git add

on each file you want to commit. Similarly, run

.. code:: bash

  git rm

on each file you want to remove from version control (don't remove them with ``rm``).
In order to commit, issue

.. code:: bash

  git commit

which prompts you with the commit message before the actual commit is performed. The basics of how to write a commit message are well explained in this blog post: https://chris.beams.io/posts/git-commit. In short, start with a summary line consisting of no more than 50 characters, not followed by a period. Leave a blank line followed by further description if necessary. For small commits, just the summary line may be sufficient. Write the whole commit message in the imperative tense (i.e. "Fix typo" not "Fixed typo"). Attention: never run ``git commit -a`` unless you are an experienced Git user! Finally, issue

.. code:: bash

  git push

to push the committed files to GitLab.

Git comes with tons of useful commands and being proficient at Git is generally a very useful skill to have. The basics of Git are nicely covered in the first three chapters of the Git book: https://git-scm.com/book/en/v2.
