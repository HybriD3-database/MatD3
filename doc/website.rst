============================
Interacting with the website
============================

Adding new users
================

When a new user registers, all users with the superuser status receive an email. The new user cannot submit new data until their status has been set to "staff status" by one of the superusers. Note that for security reasons, they should not have the superuser status by default without a good reason.

Data verification
=================

Since this is a curated database, it is necessary to ensure the correctness of each data set somehow. For this, we have implemented a simple feature where users can review other users' data and click on the verification button present at each data set. Once one or more users have clicked on the verification button, the data set is considered "verified". Details about who originally created the data set, who last modified it, and which people have verified its correctness is recorded and displayed at the meta section of each data set. The users cannot verify their own data sets.

Data mutability
===============

Each data set is given a unique ID, which is displayed on the website and can be used to refer to the data set. The ID does not change and, should the data set be deleted, will not be reassigned to a different data set. Users are allowed to modify most of the contents of a data set after it has been submitted to the website. An exception is the actual numerical data. If any of the numerical values need to be edited, the data set has to be deleted and recreated instead.
