============================================
Welcome to the MatD\ :sup:`3` documentation!
============================================

The MatD\ :sup:`3` database is designed to store and curate materials data for solid materials. It is supported by two NSF-DMREF-funded projects (initially DMR-1729297, then DMR-2323803). This document provides details on the database structure, how to set up a web interface for interacting with the database, and some details on the usage of the website. At the time of this update (September 2025), there are two live instances of the database software known to us:

https://materials.hybrid3.duke.edu/ (for hybrid organic-inorganic semiconductors)

https://muchas-db.egr.duke.edu/ (for multinary chalcogenide semiconductors)

We also explain how to interface the MatD\ :sup:`3` website with the Qresp web application.

An overview of the database software is found in the following reference:

  - |paper_ref|

.. |paper_ref| raw:: html

   <embed>
    <a href=https://doi.org/10.21105/joss.01945>R. Laasner, X. Du, A. Tanikanti, C. Clayton, M. Govoni, G. Galli, M. Ropo, and V. Blum, Journal of Open Source Software, <strong>5</strong>, 1945 (2020)</a>
    </embed>

---------
Contents
---------

.. toctree::
   :maxdepth: 2

   database
   setup
   development
   website
   coding_rules
   other
   qresp
   example_server
   tutorial
