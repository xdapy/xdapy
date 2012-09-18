Migration
=========

Often it is necessary, to migrate data from one database to another. This can be the case when the primary database is not accessible (perhaps due to network inavailability); or when trying to join collected data sets of different users.

There is no general strategy for these cases, as approaches may differ in details.

Considering, two entities with the same `unique_id` are alike what should be done if the parameters differ? What should be done to attached entities? What about associated data?

On the other hand, two entities in different databases may describe one and the same entity. (Having the same attributes but different `unique_id`\s.) Should these be merged automatically?

**xdapy** tries to ease migration, providing several mechanisms for intermediate data storage (XML, JSON, SQLite). Additionally, SQLite may be used as a full storage engine.


Possible issues
---------------

Migration is a two-fold process. The first step involves moving the raw data from one database into another, including binary data attachments and properties, possibly updating entities with the same `unique_id` (if these are considered identical). The second step includes updating all inter-entity references. This means moving all previous parent–child and entity–entity connections to the new database and finding sensible ways to deal with entities which have been present in both databases.


Rebranding Entities
===================

Another recurring problem can be the re-naming of classes. (Let’s call it *rebranding*.) While changing the name of an entity in a table would be next to trivial, changing the class itself from inside Python (through several layers of database abstraction) is not possible. This means that all previously generated object instances (in Python) are practically invalid and have to be recreated with the new class abstraction.

Moreover, the same is true, when we try to add or remove the set of `declared_params` for an entity (also because this set of parameters in turn defines the internal *name* of the entity); all of these actions require some thought and a potential migration process for each and every object.

Assume we start with the following entity which may be used to store some kind of software releases, say, of xdapy::

    class Release(Entity):
        declared_params = {
            "name": "string",
            "version": "int"
        }

we create a few entity objects and store them::

    e0 = MyEntity(name="xdapy", version=1)
    e1 = MyEntity(name="xdapy", version=2)

At some point in the future, we figure out that it would be best to store the version ‘number’ as a string and that we’d also like to add a proper release date to the `Release` entity::

    class ReleaseRefined(Entity):
        declared_params = {
            "name": "string",
            "version": "string",
            "release_date": "date"
        }

How would we get from one release schema to the other?

As it turns out, it is a little more complicated to change the entity type than it is to change the value of a parameter. A simple ``e0._type = ReleaseRefined`` would only change the database representation but not the object itself. (Leading to a few problems with SQLAlchemy.) Also, it would not migrate the version number on already existing objects. (Existing objects would have their old reference to one of the parameter tables fixed. These could only be updated with values of the same type.)

xdapy provides a helper function (`Mapper.rebrand`) which allows us to do the transformation with the help of some intermediate classes and functions::

    class ReleaseHelperA(xdapy.Entity):
        declared_params = {
            "name": "string",
            "version": "integer",
            "version_string": "string",
            "release_date": "date"
        }

    class ReleaseHelperB(xdapy.Entity):
        declared_params = {
            "name": "string",
            "version_string": "string",
            "release_date": "date"
        }

As a first step, we’ll add a new parameter to our `Release` which serves as a temporary storage for our `string`’d version number::

    mapper.rebrand(Release, ReleaseHelperA, after=migrate_version)

We hook in a function `migrate_version` to be applied to all migrated entities::

    def migrate_version(entity, params):
        params["version_string"] = str(params["version"])
        del params["version"]

        params["release_date"] = datetime.date.today()
        return params

All we do in this function is take the old version integer, stringify it and set the version_string parameter accordingly. Then we clear the original field. Additionally, we also add a dummy value for the release date.

As a next step, we are able to migrate into a version which does not contain any reference to an integer version (it is important to have deleted all params["version"] before that)::

    mapper.rebrand(ReleaseHelperA, ReleaseHelperB)

Finally, we can migrate to the refined version of `ReleaseRefined` by moving all params from `version_string` to `version`::

    def move_version_string(entity, params):
        params["version"] = params["version_string"]
        del params["version_string"]
        return params

    mapper.rebrand(ReleaseHelperB, ReleaseRefined, after=move_version_string)

In order to be safe from session failure, now would be a good moment to re-initialise and reconnect.

