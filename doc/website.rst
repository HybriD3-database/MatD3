============================
Interacting with the website
============================

Adding new users
================

When a new user registers, all users with the superuser status receive an email. The new user cannot submit new data until their status has been set to "staff status" by one of the superusers. Note that for security reasons, they should not have the superuser status by default without a good reason.

Data verification
=================

One of the features that makes this a curatable database is the user's ability to verify the correctness of data sets. When the users are reviewing other users' data they can click on the verification button present at each data set. Once one or more users have clicked on the verification button, the data set is considered "verified". Details about who originally created the data set, who last modified it, and which people have verified its correctness is recorded and displayed at the meta section of each data set. If the data set is modified after it has been verified, its verification status is revoked and it would need to be re-verified (all verifiers will receive an email noting the change). Users cannot verify their own data sets.

Editing data
============

Each data set is given a unique ID, which is displayed on the website and can be used to refer to the data set. The ID does not change and, should the data set be deleted, will not be reassigned to a different data set. Users are allowed to modify most of the contents of a data set after it has been submitted to the website. An exception is the actual numerical data. If any of the numerical values need to be edited, the data set has to be deleted and recreated instead.

REST API
========

We provide a REST API for downloading the contents of the database in a machine readable format such as JSON. This allows the user to easily manipulate the data as they see fit. Currently accessible endpoints are:

  - /materials/references/
  - /materials/systems/
  - /materials/properties/
  - /materials/units/
  - /materials/datasets/

The endpoints are appended to the URL of a live instance of MatD\ :sup:`3`. For example, in order to fetch all references hosted at https://materials.hybrid3.duke.edu/, issue a GET request to https://materials.hybrid3.duke.edu/materials/references/. In order to fetch data for a single model instance (specific reference, system, ...), append the endpoint with ``<id>/``, where ``<id>`` is the ID (primary key) of the corresponding model. As an example, the URL for fetching the contents of data set 317 is https://materials.hybrid3.duke.edu/materials/datasets/317/. The ID is the one seen at the bottom of the data set (see https://materials.hybrid3.duke.edu/materials/dataset/317).

HTTPie is a command line tool for issuing HTTP requests. Here is example usage:

.. code:: bash

   http --verify=no https://materials.hybrid3.duke.edu/materials/datasets/317/
