====================
Example server setup
====================

There are many ways to configure a server to run HybriD\ :sup:`3` and Qresp instances. Here, we provide an example Nginx/Gunicorn configuration that has proven to work.

First, create and start the systemd units that run HybriD\ :sup:`3`/Qresp via the Gunicorn servers:

.. literalinclude:: qresp.socket

.. literalinclude:: qresp.service

.. literalinclude:: matd3.socket

.. literalinclude:: matd3.service

Note that the sockets should be started in system and not user mode. Then, start the Nginx server with the following configurations:

.. literalinclude:: qresp.conf

.. literalinclude:: matd3.conf
