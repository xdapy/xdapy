# -*- coding: utf-8 -*-

from xml.etree import ElementTree as ET

from xdapy.structures import EntityObject
from xdapy.io import XmlIO

from xdapy import Connection, Mapper

connection = Connection.test() # use standard profile
#connection = Connection(dbname="xdapy")
m = Mapper(connection)

# drop the old database structure
m.create_tables(overwrite=True)


class Trial(EntityObject):
    parameter_types = {'count': 'string', 'phase_of_signal_in_first_interval': 'string', 'reaction_time': 'string', 'noise_seed': 'string', 'phase_of_signal_in_second_interval': 'string', 'signal_interval': 'string', 'note': 'string', 'start': 'string', 'valid': 'boolean', 'subject_response': 'string'}

class Setup(EntityObject):
    parameter_types = {'serial_number_monitor': 'string', 'calibration_file': 'string', 'hardware': 'string', 'frame_rate': 'string', 'serial_number_visage': 'string', 'software': 'string'}

class Experiment(EntityObject):
    parameter_types = {'project': 'string', 'stimulus_file': 'string', 'reference': 'string', 'source_directory': 'string', 'note': 'string', 'source_file': 'string', 'experimenter': 'string', 'data_directory': 'string', 'keywords': 'string'}

class Observer(EntityObject):
    parameter_types = {'name': 'string', 'age': 'integer', 'handedness': 'string', 'birthday': 'date', 'glasses': 'boolean', 'initials': 'string'}

class Session(EntityObject):
    parameter_types = {'count': 'string', 'Number_of_Trials': 'string', 'feedback': 'string', 'data_file': 'string', 'signalContrast': 'string', 'stimulusSizeDegrees': 'string', 'note': 'string', 'percentCorrect': 'string', 'frequency': 'string', 'presentationTime': 'string', 'date': 'string', 'pedestalContrast': 'string', 'noiseContrast': 'string', 'noiseType': 'string'}


objects = EntityObject.__subclasses__()
m.register(*objects)
xmlio = XmlIO(m, objects)
xmlio.read_file("demo/xml.xml")

with m.auto_session as session:
    e = Experiment()
    session.add(e)

print ET.tostring(xmlio.write())

from xml.dom.minidom import parseString

def prettyPrint(element):
    txt = ET.tostring(element)
    print parseString(txt).toprettyxml()

prettyPrint(xmlio.write())



