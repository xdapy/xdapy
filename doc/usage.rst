.. _usage:

Usage
=====

Opening a connection
--------------------

In order to access a database, we need to create a mapper::

    postgresql_mapper = xdapy.Mapper("postgresql://user:pass@host/dbname")

we may also connect to a SQLite database::

    sqlite_mapper = xdapy.Mapper("sqlite:///test.db")

or even to a memory-based database for testing::

    memory_mapper = xdapy.Mapper("sqlite://")

The mapper can also access the profiles in the initialization file defined during the installation.  
In this case a connection is explicitly created and passed to the mapper::

	from xdapy import Connection, Mapper
	
	connection = Connection.profile("demo")
	mapper = Mapper(connection)
	

Define and create an object
---------------------------

We now need to define a structure which holds our data. We use the data model from the :ref:`example2` and create the first structure::

    class Experiment(xdapy.Entity):
        declared_params = {
          'identifier': 'int',
          'project': 'string',
          'author': 'author',
          'date': 'date'
        }

We have created a subclass of `xdapy.Entity` and added a special structure ``declared_params`` to it. 
In ``declared_params`` we have to specify all the parameters we want to store for this `Entity`. 
Also, we have to specify the type for the respective parameters. 
The ``declared_params`` structure is evaluated during the creation of the class itself (read: metaclass) and automatically sets some more attributes on `Entity`.
This is mainly needed for SQL storage but also provides us with a minimal type checking system.
Without a type checking, the database could save a parameter called `project` or `proect` and would not complain about a difference. 
During a search for the keyword `project`, the wrongly spelled parameter could not be found. 
Since the parameter declarations are permanently stored during the object registration, an `Exception` is raised if a misspelled parameter is stored. 
That also means that no other parameter, except for the declared ones, can be stored with an object.

However, Xdapy does not enforce that each parameter from the declared parameters dictionary is defined in every object instance.
If such an enforcement is desired, it needs to be implement in the application. 


Every use of Xdapy requires a registration of the objects in the mapper. 
With the registration the parameter declarations are stored in the database as triplets containing the class name of the object, parameter name, and parameter type.
The registration process is a security step to ensure compatibility between different applications of Xdapy::

	mapper.register(Experiment)

If the object class definitions are stored in a file, say objects.py, then they can simply be imported and registered in the mapper. 
It is therefore not necessary to rewrite the object definitions with every use.

We can now instantiate and use our `Experiment`. 
Parameters are either added inside the ``__init__`` method or accessed and changed through the ``params`` dict::

    experiment = Experiment(project="visual")
    experiment.params["identifier"] = 5005
    experiment.params["author"] = "John Jo"
    experiment.params["date"] = datetime.now()

Using the mapper, we save the object to the database::

    mapper.save(experiment)


Build an object hierarchy
-------------------------

To show how the hierarchical connections are made, let us first define more object classes and register them::
	
	#Define object classes
	class Session(xdapy.Entity):
	    declared_params = {
	    'count': 'integer',
	    'date': 'date',
	    'experimentalcondition': 'string',
	    }
	
	class Trial(xdapy.Entity):
	    declared_params = {
	    'count': 'integer',
	    'stimulus': 'integer',
	    'answercorrect': 'boolean'
	    }
	
	#Register
	mapper.register(Session)
	mapper.register(Trial)
	
Then, we create instances of the objects::
 	
 	s1 = Session(count=1, date=datetime.date.today(), experimentalcondition='outline')
	s2 = Session(count=2, date=datetime.date.today(), experimentalcondition='filled')
	
	t1 = Trial(count=1, stimulus=20, answercorrect=True)
	t2 = Trial(count=2, stimulus=36, answercorrect=True)
	t3 = Trial(count=3, stimulus=8, answercorrect=False)
	t4 = Trial(count=4, stimulus=87, answercorrect=False)
	t5 = Trial(count=5, stimulus=26, answercorrect=True)
	t6 = Trial(count=6, stimulus=74, answercorrect=True)
	t7 = Trial(count=7, stimulus=20, answercorrect=False)
	t8 = Trial(count=8, stimulus=16, answercorrect=True)
	t9 = Trial(count=9, stimulus=96, answercorrect=False)
	t10 = Trial(count=10, stimulus=36, answercorrect=True)

Finally, the relationships among the objects will be defined through parent and child definitions. 
There are several equivalent ways to define relations::
	
	
	s2.parent = experiment
	
	experiment.children.append(s1)
	s1.children.append(t1)
	s1.children.append(t2)
	
	s2.children += [t3,t4,t5,t6,t7,t8,t9,t10]
	
	#Save all relations 
	mapper.save(experiment)

It should be enough to save the highest object in the hierarchy and the relations and children are saved with it. 
The connections we just created result in this tree:

.. figure:: images/exampleExp.png

 
Attach entities
---------------
Now the annotations about the observer that participated in the first session are *connect* or *attach*::
	
	class Observer(xdapy.Entity):
	    declared_params = {
	    'name': 'string',
	    'birthyear': 'integer',
	    'initials': 'string',
	    'handedness': 'string',
	    'glasses': 'boolean'
	    }
	    
    cs = Observer(name="Clara Sight", initials="CS", handedness="right", glasses=False, birthyear=1989)
    tt = Observer(name="Tom Token", initials="TT", handedness="right", glasses=True, birthyear=1978)

    s1.attach("Observer", cs)

    // or, alternatively

    s2.context["Observer"].add(tt)

Please note, that when attaching an entity to another, a label is provided with it. In this example the label is "Observer". 
This label will be used during searches.

Adding data
-----------

A last critical feature that belongs to the creation and storage of objects is to add data such as:

* files

* raw data

* binary data in general
 
For example you might want to store a file containing the project proposal and its goals with the experiment.
Adding binary data often needs special handling, since its potentially large data sets should not be automatically retrieved and loaded into memory from the database. 
Therefore, a special data API is integrated, acting on the `Entity.data` property::

    experiment.data["project proposal"].put(data)
    experiment.data["dataset #1"].put(more_data)

*Xdapy* takes care of splitting the data into smaller chunks which do not flood the memory and which are saved to the database right away. 
Consequently, the data should not be retrieved and loaded into memory but directly saved to a file::

    with open(save_to, 'w') as f:
        experiment.data["project proposal"].get(f)

Load objects from the database
------------------------------

Assuming that all sessions of two Experiment e1 and e2 were
recorded and stored, the question is how to extract the data
from the database for analysis. There are several possibilities
to query the database. The simplest options are the mapper
methods find_all and find_first::
	
	o = m.find_first(Observer, filter={"birthyear": range(1970, 1985)})
	print o.params
	
	o = m.find_all(Observer, filter={"initials": ["%S%"]})
	print o[0].params
	
	>>>>{u'birthyear': 1978, u'initials': u'TT', u'handedness': u'right', u'name': u'Tom Token', u'glasses': True}
	>>>>{u'birthyear': 1989, u'initials': u'CS', u'handedness': u'right', u'name': u'Clara Sight', u'glasses': False}
	
Query the database
------------------
Admittedly, the syntax of complex searches is not easy to
read. We therefore recommend to encapsulate repeatedly used searches in regular Python methods

The following procedure lists the stimulus number and response of the trials from the outline condition in the visual experiment 
in which observer CS responded correctly. 	::

	sessions = mapper.find_complex("Session",
	                       {("_context", "Observer"): {"_any": [("Observer",{"initials": "CS"})]},
						   "_parent":("Experiment",{"project":"vision"}),
						   "experimentalcondition":"outline"})
	trials = m.find_complex("Trial",{"_parent": {"_any": sessions}})
	for trial in trials:
		print trial.params["stimulus"], trial.params["answercorrect"]
	
	>>>> 20 True
	>>>> 36 True
