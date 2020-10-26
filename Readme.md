![](https://github.com/hybrid3-database/matd3/workflows/main/badge.svg)

[![DOI](https://joss.theoj.org/papers/10.21105/joss.01945/status.svg)](https://doi.org/10.21105/joss.01945)

MatD3 database software
=======================

MatD3 is a database and a web application for experimental and theoretical data on solid materials. The objective is to ensure better access and reproducibility of research data and it is intended to be used by any research group wishing to make their scientific results publicly available.

Installation
------------

**From source code**

These instructions are for quickly setting up a local server on your personal computer. For setting up a real server, see the full documentation at https://hybrid3-database.readthedocs.io/en/latest/.

* Clone the project

  ```
  git clone https://github.com/HybriD3-database/MatD3.git
  cd MatD3
  ```

* In the root directory of the project, create a virtual Python environment

   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

* Upgrade pip and install all the requirements

   ```
   pip install --upgrade pip
   pip install -vr requirements.txt
   ```

   If you run into any issues, install the prerequisites as requested by the error messages. On Ubuntu, it might be necessary to install the following packages first:

   ```
   sudo apt install libmysqlclient-dev
   sudo apt install python3-dev
   sudo apt install firefox-geckodriver
   ```

   On a Mac, it might be necessary to run

   ```
   brew install mariadb
   ```

   If there are issues with installing MySQL/MariaDB and you only plan to use SQLite, remove the line `mysqlclient==1.4.2` from requirements.txt and proceed with the installation.

* Define your environment in .env in the root directory of the project

  ```
  cp env.example .env
  # edit .env
  ```

  If you wish to use anything other than the SQLite database, you first need to set up that database (e.g., MariaDB). See https://hybrid3-database.readthedocs.io/en/latest/setup.html for more details.

* Initialize static files and perform database migrations

  ```
  ./manage.py collectstatic
  ./manage.py migrate
  ```

* Run tests

  ```
  ./manage.py test
  ```

  Make sure the line

  ```
  127.0.0.1 localhost
  ```

  is in your `/etc/hosts`.

* Create a superuser

  ```
  ./manage.py createsuperuser
  ```

* If you want to customize the index page, make a copy of `home_default.html`,

  ```
  cp -v mainproject/templates/mainproject/home{_default,}.html
  ```

  and edit accordingly. Any images that `home.html` refers to should be placed in `mainproject/static/mainproject/images`.

* Start the server

  ```
  ./manage.py runserver
  ```

* Open a web browser and go to http://127.0.0.1:8000/.

**Using Docker**

* Run the MatD3 Docker container in detached mode:

  ```
  docker run -d --rm --name matd3 --env-file=env_file -p 80:80 matd3/matd3:1.0.0 python manage.py runserver 0.0.0.0:80
  ```

  where `env_file` (rename if you like) contains the necessary enrironment variables. See [here](https://github.com/HybriD3-database/MatD3/blob/master/env.example) for example contents. You can view the website by opening 0.0.0.0 in a web browser. If you wish to run the container on a different port, replace 80 in the command with the number of that port.

* Initialize static files and perform database migrations

  ```
  docker exec matd3 python manage.py collectstatic --noinput
  docker exec matd3 python manage.py migrate
  ```

* Create super user

  ```
  docker exec -it matd3 python manage.py createsuperuser
  ```

* You can stop the container with

  ```
  docker container stop matd3
  ```

Usage
-----

In order to enter data into the database, start by creating a new user (click on Register and follow instructions) or login as the superuser. Next, click on Add Data on the navigation bar in order to submit a data set into the database. Existing data can be viewed by using the Search function on the navigation bar.
