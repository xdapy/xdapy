I/O formats
===========

xdapy can read and write data in both XML and JSON formats. A specification of these formats is given here.

XML
---

For XML output to work, we first have to initialise the XML serialiser. We supply our current
object mapper as a parameter::

    from xdapy.io import XmlIO
    xmlio = XmlIO(mapper)

This will automatically register all known object mappings.

If we have data stored inside our database, we can now access the XML DOM tree through::

    xmltree = xmlio.write()

And print it::

    from xml.etree import ElementTree as ET
    ET.tostring(xmltree)

This may give us something like the following:

.. literalinclude:: includes/xml-long.xml
   :language: xml


And a more complicated example:

.. literalinclude:: includes/xml-short.xml
   :language: xml

References between several entity objects are expressed either by using the `id` variable or the `unique_id` identifier. The `id` is seen as a local identifier: It is not retained during import or export of objects. Each id is only unique for the medium it is defined in. E.g. for several input files of XML data, there may be several objects with ``id="92"``. All references with a specifier ``"id:92"`` can of course only be resolved inside that file.

For global references, the object mapper introduces a unique_id. This identifier may be used for stable referencing across several files.

In general, the object mapper will take care of generating these unique_id numbers. When creating a XML or JSON file for input, it is sufficient (and advisable) to only use `id` references and leave out `unique_id` values.

JSON
----

Alternatively, there is also a simple JSON-compatible format available.

.. literalinclude:: includes/json-long.json
   :language: javascript

The JSON representation is compressed in the sense that the `parameters` section of an entity is represented by a single dictionary (JSON object). In JSON we also use the directly corresponging representation of simple data types. E.g. we simply use ``1.0`` instead of ``"1.0"`` for a floating point number.


