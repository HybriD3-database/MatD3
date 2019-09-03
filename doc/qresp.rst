===================================
Interaction with the Qresp database
===================================

The Qresp database focuses on the reproducibility of experimental and computational results presented in scientific papers. Users are able to upload the contents of published papers in the form of datasets, charts, scripts, tools, and notebooks. The idea is to ensure that every table and figure is accurately reproducible. On a technical level, the figures, tables, and the numerical data of papers are stored elsewhere and the Qresp server only stores the meta information such as the publication, authors, scripts used to manipulate the data, and references (links) to the actual data. A MatD\ :sup:`3` server could be used to host the data, with Qresp entries pointing to that data. We have implemented extensions to Qresp that allow the user to upload the paper contents using the Qresp GUI, such that the main data is stored on a MatD\ :sup:`3` server, the metadata is stored on a Qresp server, and the paper contents are browsable on both servers.

Setting up a Qresp instance
===========================

Most of the information on how to set up Qresp is found at http://qresp.org/. Here we provide details specific to the MatD\ :sup:`3`/Qresp connection. Specifically, Qresp can be configured using an ``.env`` file similar to the MatD\ :sup:`3` database. Only two parameters are required to establish the connection. Here is an example:

.. code:: bash

  MATD3_URL=https://materials.hybrid3.duke.edu
  HOST_URL=https://qresp.hybrid3.duke.edu

That is, the URL of the MatD\ :sup:`3` server and that of the Qresp server.

Migrating data
==============

There are three ways to share data between the MatD\ :sup:`3` and Qresp servers.

- Creating the Qresp and MatD\ :sup:`3` entries at the same time. In the Qresp Curator, at the "Connect to Server" step, click on "Use MatD\ :sup:`3`". Then, when selecting charts (equivalent to data sets in MatD\ :sup:`3`), clicking on "Add new" allows you to create a data set in the MatD\ :sup:`3` database and immediately import the metadata of that data set to Qresp in the form of a chart. The rest of the curation follows the standard Qresp workflow (see \url{http://qresp.org/}).
- Importing existing MatD\ :sup:`3` data sets into Qresp. Same as before, click on "Use MatD\ :sup:`3`" at the "Connect to Server" step. Now, instead of selecting "Add new", enter the ID of a data set and hit "Submit" to turn that data set into a chart. The data set ID is found at the bottom of each data set at the MatD\ :sup:`3` website. The rest of the curation process stays the same
- Exporting Qresp entries to the MatD\ :sup:`3` database. Qresp charts can be exported to the MatD\ :sup:`3` server if applicable (e.g., they must be specific to HOIPs). At the Qresp website, click on "Export" and browse the articles as you normally would. Except now there is an "Export to the MatD\ :sup:`3` database" button next to each chart. Clicking on it brings you to the MatD\ :sup:`3` data submission page, where you need to fill in additional fields to convert the Qresp chart into a MatD\ :sup:`3` data set. The need to fill in additional information stems from the fact that Qresp uses a noSQL database for storing data, whereas MatD\ :sup:`3` is based on a SQL database. That is, were are moving from unstructured to structured data.
