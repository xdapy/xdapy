Usage
=====

Opening a connection
--------------------

In order to access a database, we need to create a mapper::

    mapper = xdapy.Mapper("postgresql://user:pass@host/dbname")

we may also connect to a SQLite database::

    sqlite_mapper = xdapy.Mapper("sqlite:///test.db")

or even to a memory-based database for testing::

    memory_mapper = xdapy.Mapper("sqlite://")


Creating a model
----------------

We now need to define a structure which holds our data. For example, let’s assume we’d like to keep track of certain experiments::

    class Experiment(xdapy.Entity):
        declared_params = {
          'ident': 'int',
          'project': 'string',
          'supervisor': 'string',
          'observer': 'string',
          'date': 'date'
        }

We have created a subclass of `xdapy.Entity` and added a special structure ``declared_params`` to it. In ``declared_params`` we have to specify all the parameters we want to store for this `Entity`. Also, we have to specify the type for the respective parameters. This is mainly needed for SQL storage but also provides us with a minimal type checking system.

The ``declared_params`` structure is evaluated during the creation of the class itself (read: metaclass) and automatically sets some more attributes on `Entity`.

We can now try to instantiate and use our `Experiment`::

    experiment = Experiment(project="The failed experiment project")
    experiment.params["ident"] = 5005
    experiment.params["supervisor"] = "No name"
    experiment.params["date"] = datetime.now()

Parameters may be accessed and changed through the ``params`` dict. Additionally, for convenience, parameters may also be added inside the ``__init__`` method.

Using our mapper, we may also save it to the database::

    mapper.save(experiment)


Connecting entities
-------------------

At some point, we may want to add metadata related to, say, the observer of a certain experiment. Maybe his or her age or some other attribute. Rather than adding this as a separate parameter to the experiment, one could consider creating another entity::

    class Observer(xdapy.Entity):
        declared_params = {
            'age': 'int',
            'name': 'string',
            'handedness': 'string'
        }

    observer = Observer(name="Unknown Observer")

We can then *connect* or *attach* this observer to all experiments::

    experiment.attach("Observer", observer)

    // or, alternatively

    experiment.context["Observer"].add(observer)


Adding data
-----------

Adding binary data often needs special handling, since it potentially large data sets should not be automatically retrieved and loaded into memory from the database. Therefore, a special data API is integrated, acting on the `Entity.data` property::

    experiment.data["dataset #1"].put(data)
    experiment.data["dataset #2"].put(more_data)

*xdapy* takes care of splitting the data into smaller chunks which do not flood the memory and which are saved to the database right away. Consequently, the data should not be retrieved and loaded into memory but directly saved to a file::

    with open(save_to, 'w') as f:
        experiment.data["dataset #1"].get(f)

