============
Coding rules
============

If you are unsure about any rule described in this section, see the source code for examples and clarification.

Python
======

- This project follows the PEP 8 style guide. Use a text editor that highlights parts of the code that do not conform to PEP 8 or use an external tool to do that. One such tool is flake8 (``pip install flake8``). You can test the correctness of a source file by running ``flake8 file.py``. We are not summarizing here all the rules described by PEP 8 but one thing worth noting is that the maximum line length is 79 characters.

HTML and Javascript
===================

- See the Airbnb style guide for instructions on formatting: https://github.com/airbnb/javascript.
- The maximum line length for Javascript is 80 characters.
- The line length limit of HTML is harder to establish because of the highly nested nature of HTML. Although not as strict, try to keep the lines within 120 characters.
- Use UNIX-style newlines (``\n``). Windows-style newlines (``\r\n``) are not allowed.

Python imports
==============

- Group imports as follows: standard system libraries, Django libraries, local libraries. Separate the groups by blank lines.
- Within a group, sort the imports alphabetically. This also means that ``from ...`` should come before ``import ...``.
- Do not import multiple things on one line. For example, ``import os, sys`` should be split into two imports.

Django template tags
====================

- Leave one space around the opening and closing symbols of a construct (e.g., \verb+{{+, \verb+%}+, \ldots).
