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

Migrating Entities
------------------


