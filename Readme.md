MatD3 database software
=======================

MatD3 is a database and a web application for experimental and theoretical data on solid materials. The objective is to ensure better access and reproducibility of research data and it is intended to be used by any research group wishing to make their scientific results publicly available.

Installation
------------

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

* Create a superuser

  ```
  ./manage.py createsuperuser
  ```

* Start the server

  ```
  ./manage.py runserver
  ```

* Open a web browser and go to http://127.0.0.1:8000/.


Usage
-----

In order to enter data into the database, start by creating a new user (click on Register and follow instructions) or login as the superuser. Next, click on Add Data on the navigation bar in order to submit a data set into the database. Existing data can be viewed by using the Search function on the navigation bar.
