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

Setup Step 1
------------
Install the required components from their respective web pages or using a package manager if your system supports one. 
Instructions, advice and support for the installation of the third party components can be obtained by their providers.
Then, checkout Xdapy from its repository on https://github.com/xdapy/xdapy.git 
The path to your local copy of Xdapy must be added to the `PYTHONPATH`.

Basic Test
----------
Testing is conveniently done using nosetests. Here, we first test the basic installation 
of Python and SQLAlchemy using a SQLite in-memory database.::

	cd path/to/xdapy/
	nosetests

Python's build in unittests can be used alternatively starting with Python2.7::3

	python -m unittest discover
	
If the tests worked properly you are almost finished with the setup. There is only one more step.

Setup Step 2
------------
With the second step we define the default database that Xdapy will use. 
Create an initialization file that is located in a hidden directory below your home folder::

	cd ~
	mkdir .xdapy
	cd .xdapy
	
Furthermore, the file must be called `engine.ini` and it can contain several profiles that reference to different databases::

	[default]
	url = sqlite:///xdapy.db 
	[test]
	url = sqlite://
	[demo]
	url = sqlite:///demo.db 

The default profile must be specified. 
The test profile will only be used for the tests. 
The in-memory SQLite database from this example is the same option as when no test profile is specified. 
A third profile is applied with the demo code. This way, the database that will be used in the real application is not touched. 
If you wish to use Xdapy with PostgreSQL, then the tests should be rerun with an PostgreSQL database. 
Otherwise, you can skip the next paragraph and continue with step 3.

Test with PostreSQL
-------------------
Before we can run the tests for a PostgreSQL database or use one as default, these databases need to be created. 
Run the following commands on the console to create the databases locally::

	createdb dbname
	createdb testdbname
	
Then, adapt the `engine.ini`::

	[default]
	url =  postgresql://user:pass@host/dbname
	[test]
	url =  postgresql://user:pass@host/testdbname

and finally rerun the tests as described above. 

Setup Step 3
------------
At this point the general setup is running. 
You will only need to create the initial database table structure, and to do so you actually use Xdapy for the first time. ::

	from xdapy import Connection

	connection = Connection.profile("demo") # use demo profile
	connection.create_tables()

The example creates the tables for the "demo" profile. The same needs to be done for the default profile.
Now, the installation is finished and the database can be used. 