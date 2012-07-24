Installation
============

Requirements
------------

* Python 2.6 / 2.7
* SQLAlchemy

Additionally for PostgreSQL
^^^^^^^^^^^^^^^^^^^^^^^^^^^
* psycopg2 (Python–PostgreSQL Database Adapter)
.. note::
    Psycopg2 must be of version 2.4.1 or above due to a bug concerning PostgreSQL handling of binary data.
    See also http://initd.org/psycopg/docs/faq.html#problems-with-type-conversions.
* A postgresql database

Additionally for SQLite
^^^^^^^^^^^^^^^^^^^^^^^
(built into Python)

Testing
=======

Testing is conveniently done using nosetests.