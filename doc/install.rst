Installation
============

Requirements
------------

* Python 2.6 / 2.7
* SQLAlchemy
.. note::
    SQLAlchemy must be of version 0.7 or above
    
Additionally for PostgreSQL
^^^^^^^^^^^^^^^^^^^^^^^^^^^
* psycopg2 (Python–PostgreSQL Database Adapter)
.. note::
    Psycopg2 must be of version 2.4.1 or above due to a bug concerning PostgreSQL handling of binary data.
    See also http://initd.org/psycopg/docs/faq.html#problems-with-type-conversions. To it needs to be installed 
    from source, the packages libpq and libpq-dev are required as well.
* A postgresql database

Additionally for SQLite
^^^^^^^^^^^^^^^^^^^^^^^
(built into Python)


Testing
=======

Testing is conveniently done using nosetests.
