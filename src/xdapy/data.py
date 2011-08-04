# -*- coding: utf-8 -*-

import collections
import tempfile

try:
    # check, if the faster version of StringIO is available
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from sqlalchemy import Column, ForeignKey, String, Integer
from sqlalchemy import func
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.orm import relationship, validates, synonym
from sqlalchemy.ext.declarative import synonym_for

# So we really want to support only Postgresql?
from sqlalchemy.dialects.postgresql import BYTEA

from xdapy import Base
from xdapy.errors import Error, InsertionError, MissingSessionError, DataInconsistencyError


DATA_CHUNK_SIZE = 5 * 1000 * 1000 # Byte
DATA_COLUMN_LENGTH = DATA_CHUNK_SIZE # Must be greater or equal than DATA_CHUNK_SIZE

class DataChunks(Base):
    """Data are divided into smaller chunks of size `DATA_CHUNK_SIZE` to avoid
    that everything is loaded all at once when accessing the data."""

    id = Column('id', Integer, autoincrement=True, primary_key=True)
    data_id = Column(Integer, ForeignKey('data.id'), nullable=False)
    index = Column("index", Integer)

    # hide the raw value in order to allow for a specific setter method
    _chunk = Column('data', BYTEA(DATA_COLUMN_LENGTH), nullable=False)
    @property
    def chunk(self):
        return self._chunk

    @chunk.setter
    def chunk(self, chunk):
        # we also set the _length here
        if not isinstance(chunk, basestring): # TODO what about real binary?
            raise ValueError("Data must be a string")
        self._chunk = chunk
        self._length = len(chunk)

    chunk = synonym('_chunk', descriptor=chunk)

    _length = Column('length', Integer)

    @synonym_for('_length')
    @property
    def length(self):
        return self._length

    __tablename__ = 'data_chunks'
    __table_args__ = (UniqueConstraint(data_id, index),
                    {'mysql_engine':'InnoDB'})

    def __init__(self, index, chunk):
        self.index = index
        self.chunk = chunk

    def __repr__(self):
        return "<DataChunk #{0} for Data[{1}], length {2}>".format(self.index, self.data_id, self.length)

class Data(Base):
    '''
    The class `Data` is mapped on the table 'data'. The name assigned to Data
    must be a string. Each Data is connected to at most one entity through the
    adjacency list 'datalist'. The corresponding entities can be accessed via
    the entities attribute of the Data class.
    '''
    id = Column('id', Integer, autoincrement=True, primary_key=True)
    entity_id = Column(Integer, ForeignKey('entities.id'), nullable=False)
    key = Column('key', String(40))
    mimetype = Column('mimetype', String(40))

    @property
    def length(self):
        return self._length

    _chunks = relationship(DataChunks, cascade="save-update, merge, delete")

    __tablename__ = 'data'
    __table_args__ = (UniqueConstraint(entity_id, key),
                    {'mysql_engine':'InnoDB'})

    @validates('key')
    def validate_name(self, key, parameter):
        if not isinstance(parameter, basestring):
            raise TypeError("Argument must be a string")
        return parameter

    def __repr__(self):
        return "<%s('%s','%s',%s)>" % (self.__class__.__name__, self.key, self.mimetype, self.entity_id)

class _DataProxy(object):
    def __init__(self, assoc, key):
        self.assoc = assoc
        self.key = key

    @property
    def __session(self):
        """Returns the session of the associated entity."""
        # makes code more readable
        return self.assoc.owning._session()

    @property
    def __data(self):
        """Returns the data relation object of the associated entity.
        This method also raises a `MissingSessionError`, if no session is
        associated with the entity.
        """
        self.__session # check that a session is available
        return self.assoc.owning._data

    @property
    def mimetype(self):
        """Return the mimetype of the related data object."""
        return self.get_data().mimetype

    @mimetype.setter
    def mimetype(self, mimetype):
        data = self.get_or_create_data()
        data.mimetype = mimetype

    @mimetype.deleter
    def mimetype(self):
        self.get_data().mimetype = None

    def has_data(self):
        return self.key in self.__data

    def get_data(self):
        """Returns the associated data for `self.key`."""
        # raises a KeyError, if no data is associated
        data = self.__data[self.key]

        assert data.id is not None, "data.id has not been set" # we check explicitly to avoid complications at a later point
        return data

    def get_or_create_data(self):
        if not self.has_data():
            # Add a new data entry to the owning list (which should add it to the session)
            self.__data[self.key] = Data(key=self.key)
            # and flush it
            self.__session.flush()
        return self.get_data()

    def chunk_ids(self):
        return [chunk.id for chunk in self._chunk_query(DataChunks.id)]

    def chunk_index(self):
        return [chunk.index for chunk in self._chunk_query(DataChunks.index)]

    def delete(self):
        data = self.get_data()
        self.__session.delete(data)
        self.__session.flush()

    def clear_data(self):
        data = self.get_data()
        for ch in data._chunks:
            self.__session.delete(ch)
            self.__session.flush()

    def put(self, file_or_str, mimetype=None):
        if isinstance(file_or_str, basestring):
            self.put_string(file_or_str)
        else:
            self.put_file(file_or_str)
        if mimetype:
            self.mimetype = mimetype

    def put_string(self, string):
        string = StringIO(string)
        try:
            self.put_file(string)
        finally:
            string.close()

    def put_file(self, fileish):
        if not hasattr(fileish, 'read'):
            # if there is no 'read' method, is is
            # probably the wrong type
            raise ValueError("Unassignable Type")

        data = self.get_or_create_data()
        self.clear_data()

        buffer_size = DATA_CHUNK_SIZE
        idx = 0

        chunk = fileish.read(buffer_size)

        while chunk:
            idx += 1
            chunk = DataChunks(idx, chunk)
            data._chunks.append(chunk)

            chunk = fileish.read(buffer_size)
            if idx % 10 == 0:
                # we flush every now and then
                self.__session.flush()

        self.__session.flush()

    def _chunk_query(self, *entities, **kwargs):
        # Version which uses caching of data_id
#        if not hasattr(self, "data_id") or self.data_id is None:
#            try:
#                self.data_id = self.__session().query(Data.id).filter(Data.entity_id==self.assoc.owning.id).filter(Data.key==self.key).one().id
#            except NoResultFound:
#                raise SelectionError("Could not find a result. Maybe there is no data associated with this key.")
        data_id = self.get_data().id # this probably does the same as above code and raises a KeyError

        return self.__session.query(*entities, **kwargs).filter(DataChunks.data_id==data_id)

        # Version which uses a join each time
        # return self.__session.query(*entities, **kwargs).join(Data).filter(Data.entity_id==self.assoc.owning.id).filter(Data.key==self.key)

    def get(self, fileish):
        for chunk in self._chunk_query(DataChunks.chunk).order_by(DataChunks.index):
            fileish.write(chunk.chunk) # self._data[gen_key].data)

    def get_string(self):
        string_io = StringIO()
        try:
            self.get(string_io)
            return string_io.getvalue()
        finally:
            string_io.close()

    def size(self):
        return self._chunk_query(func.sum(DataChunks.length)).scalar()

    def chunks(self):
        return self._chunk_query(DataChunks.id).count()

    def check_consistency(self):
        """Checks that data chunks are indexed in order without gaps."""
        check = 1
        for idx in self._chunk_query(DataChunks.index).order_by(DataChunks.index):
            if check != idx.index:
                raise DataInconsistencyError("Chunked data is inconsistent.")
            check += 1
        return True


class _DataAssoc(collections.MutableMapping):
    """Association dict for data.

    The dict acts a bit *weird* in the sense that `dict["unknown item"]` does not
    raise a `KeyError`. In order to find out that an item exists, one must use
    `"item" in dict`.
    """
    def __init__(self, owning):
        self.owning = owning

    def _query(self, *entities, **kwargs):
        """Issues a query on the session of the owning object, with a filter on the owning id."""
        return self.owning._session().query(*entities, **kwargs).filter(Data.entity_id==self.owning.id)

    def __getitem__(self, key):
        return _DataProxy(self, key)

    def __delitem__(self, key):
        del self.owning._data[key]

    def __setitem__(self, key, value):
        if not isinstance(value, _DataProxy):
            raise ValueError("value needs to be instance of DataProxy")
        # """Note that this is only expected to work if value *really* has the same semantics."""

        # We use a tempfile as long as chunk based copying is not established
        with tempfile.TemporaryFile() as f:
            value.get(f)
            f.seek(0) # Reset the file pointer, otherwise we'll only see EOF
            self[key].put(f)

        self[key].mimetype = value.mimetype

    def __len__(self):
        return len(self.owning._data)

    def __iter__(self):
        """Iterate over the keys."""
        return iter(self.owning._data) # our keys are of course the same as _data's

    def __contains__(self, key):
        """Is key in self?"""
        # We must do this, because we do not raise a KeyError in __getitem__
        return key in self.owning._data

    def copy(self, other):
        """Copys everything from another DataAssoc into this."""
        for data_key in other:
            self[data_key] = other[data_key]


