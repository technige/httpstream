
from collections import namedtuple
from itertools import groupby
import json
import logging
import re

from httpstream import (
    Resource as _Resource,
    ClientError as _ClientError,
    ServerError as _ServerError,
    URI,
    Request as _Request,
)
from iana.http import NOT_FOUND
from jsonstream import assembled

from .exceptions import ClientError, ServerError, CypherError, BatchError
from .mixins import Cacheable
from .util import compact, flatten, has_all, is_collection, quote, version_tuple


DEFAULT_SCHEME = "http"
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 7474
DEFAULT_NETLOC = "{0}:{1}".format(DEFAULT_HOST, DEFAULT_PORT)
DEFAULT_URI = "{0}://{1}".format(DEFAULT_SCHEME, DEFAULT_NETLOC)

SIMPLE_NAME = re.compile(r"[A-Za-z_][0-9A-Za-z_]*")

logger = logging.getLogger(__name__)


def _hydrated(data):
    """ Takes input iterable, assembles and resolves any Resource objects,
    returning the result.
    """
    if isinstance(data, dict):
        for cls in (Relationship, Node, Path):
            if has_all(data, cls.signature):
                return cls._hydrated(data)
        else:
            raise ValueError("Cannot determine object type", data)
    elif is_collection(data):
        # list or tuple but not string
        return type(data)([_hydrated(datum) for datum in data])
    else:
        return data


def _node(*args, **kwargs):
    """ Cast the arguments provided to a :py:class:`neo4j.Node`. The following
    general combinations are possible:

    - ``node(node_instance)``
    - ``node(property_dict)``
    - ``node(**properties)``
    - ``node(*labels, **properties)``

    If :py:const:`None` is passed as the only argument, :py:const:`None` is
    returned instead of a ``Node`` instance.

    Examples::

        node(Node("http://localhost:7474/db/data/node/1"))
        node()
        node(None)
        node(name="Alice")
        node({"name": "Alice"})
        node("Person")
        node("Person", name="Alice")

    """
    if len(args) == 1 and not kwargs:
        arg = args[0]
        if arg is None:
            return None
        elif isinstance(arg, Node):
            return arg
        elif isinstance(arg, dict):
            return Node.abstract(**arg)
        else:
            return Node.abstract(arg)
    else:
        return Node.abstract(*args, **kwargs)


def _rel(*args, **kwargs):
    """ Cast the arguments provided to a :py:class:`neo4j.Relationship`. The
    following general combinations are possible:

    - ``rel(relationship_instance)``
    - ``rel((start_node, type, end_node))``
    - ``rel((start_node, type, end_node, properties))``
    - ``rel((start_node, (type, properties), end_node))``
    - ``rel(start_node, type, end_node, **properties)``

    Examples::

        rel(Relationship("http://localhost:7474/db/data/relationship/1"))
        rel((alice, "KNOWS", bob))
        rel((alice, "KNOWS", bob, {"since": 1999}))
        rel((alice, ("KNOWS", {"since": 1999}), bob))
        rel(alice, "KNOWS", bob, since=1999)

    """
    if len(args) == 1 and not kwargs:
        arg = args[0]
        if isinstance(arg, Relationship):
            return arg
        elif isinstance(arg, tuple):
            if len(arg) == 3:
                return _UnboundRelationship.cast(arg[1]).bind(arg[0], arg[2])
            elif len(arg) == 4:
                return Relationship.abstract(arg[0], arg[1], arg[2], **arg[3])
            else:
                raise TypeError(arg)
        else:
            raise TypeError(arg)
    elif len(args) >= 3:
        return Relationship.abstract(*args, **kwargs)
    else:
        raise TypeError((args, kwargs))


class Resource(object):
    """ Basic RESTful web resource with JSON metadata. Wraps an
    `httpstream.Resource`.
    """

    class Metadata(object):

        @classmethod
        def load(cls, resource):
            return cls(assembled(resource.get()))

        def __init__(self, metadata):
            self._metadata = dict(metadata)

        def __getitem__(self, key):
            return self._metadata[key]

        def __iter__(self):
            return iter(self._metadata.items())

    def __init__(self, uri):
        self._resource = _Resource(uri, headers={
            # TODO: proper user agent
            "User-Agent": "py2neo/1.6.alpha (linux; python/2.7.3)",
            "X-Stream": "true;format=pretty",
        })
        self._metadata = None
        self._subresources = {}
        self.__cypher = None

    def __repr__(self):
        """ Return a valid Python representation of this object.
        """
        return repr(self._resource)

    def __eq__(self, other):
        """ Determine equality of two objects based on URI.
        """
        return self._resource == other._resource

    def __ne__(self, other):
        """ Determine inequality of two objects based on URI.
        """
        return self._resource != other._resource

    @property
    def __uri__(self):
        return self._resource.__uri__

    @property
    def __relative_uri__(self):
        offset = len(self.graph_db.__uri__)
        return URI(str(self._resource.__uri__)[offset:])

    @property
    def __metadata__(self):
        if not self._metadata:
            self.refresh()
        return self._metadata

    @property
    def is_abstract(self):
        """ Return :py:const:`True` if this entity is abstract (i.e. not bound
        to a concrete entity within the database), :py:const:`False` otherwise.

        :return: :py:const:`True` if this entity is abstract
        """
        return not bool(self.__uri__)

    @property
    def service_root(self):
        return ServiceRoot.get_instance(self._resource.__uri__.base)

    @property
    def graph_db(self):
        return self.service_root.graph_db

    @property
    def cypher(self):
        """ Cypher resource for this resource.
        """
        return self.graph_db.cypher

    def refresh(self):
        """ Refresh resource metadata.
        """
        if not self.is_abstract:
            self._metadata = Resource.Metadata.load(self._resource)

    def _request(self, method, *args, **kwargs):
        try:
            return method(*args, **kwargs)
        except _ClientError as e:
            raise ClientError(e._http, e._request, e._response, **e._kwargs)
        except _ServerError as e:
            raise ServerError(e._http, e._request, e._response, **e._kwargs)

    def _get(self, headers=None):
        return self._request(self._resource.get, headers)

    def _put(self, body=None, headers=None):
        return self._request(self._resource.put, body, headers)

    def _post(self, body=None, headers=None):
        return self._request(self._resource.post, body, headers)

    def _delete(self, headers=None):
        return self._request(self._resource.delete, headers)

    def _subresource(self, key, cls=None):
        if key not in self._subresources:
            try:
                uri = URI(self.__metadata__[key])
            except KeyError:
                raise KeyError("Key {0} not found in resource "
                               "metadata".format(repr(key)), self.__metadata__)
            if not cls:
                cls = Resource
            self._subresources[key] = cls(uri)
        return self._subresources[key]


class ServiceRoot(Cacheable, Resource):
    """ Neo4j REST API service root resource.
    """

    def __init__(self, uri=None):
        Resource.__init__(self, uri or DEFAULT_URI)

    @property
    def graph_db(self):
        return GraphDatabaseService.get_instance(self.__metadata__["data"])


class GraphDatabaseService(Cacheable, Resource):
    """ An instance of a `Neo4j <http://neo4j.org/>`_ database identified by
    its base URI. Generally speaking, this is the only URI which a system
    attaching to this service should need to be directly aware of; all further
    entity URIs will be discovered automatically from within response content
    when possible (see `Hypermedia <http://en.wikipedia.org/wiki/Hypermedia>`_)
    or will be derived from existing URIs.

    The following code illustrates how to connect to a database server and
    display its version number::

        from py2neo import neo4j

        graph_db = neo4j.GraphDatabaseService(neo4j.DEFAULT_URI)
        print(graph_db.neo4j_version)

    :param uri: the base URI of the database (defaults to the value of
        :py:data:`DEFAULT_URI`)
    """

    def __init__(self, uri=None):
        if uri is None:
            Resource.__init__(self, ServiceRoot().graph_db.__uri__)
        else:
            Resource.__init__(self, uri)

    def __nonzero__(self):
        """ Return :py:const:`True` is this graph contains at least one
        relationship.
        """
        return bool(self.cypher.execute_one("START r=rel(*) RETURN r LIMIT 1"))

    def __len__(self):
        """ Return the size of this graph (i.e. the number of relationships).
        """
        return self.size()

    @property
    def _node_resource(self):
        return self._subresource("node")

    def clear(self):
        """ Clear all nodes and relationships from the graph.

        .. warning::
            This method will permanently remove **all** nodes and relationships
            from the graph and cannot be undone.
        """
        batch = WriteBatch(self)
        batch._append_cypher("START r=rel(*) DELETE r")
        batch._append_cypher("START n=node(*) DELETE n")
        batch._submit()

    def create(self, *abstracts):
        """ Create multiple nodes and/or relationships as part of a single
        batch, returning a list of :py:class:`Node` and
        :py:class:`Relationship` instances. For a node, simply pass a
        dictionary of properties; for a relationship, pass a tuple of
        (start, type, end) or (start, type, end, data) where start and end
        may be :py:class:`Node` instances or zero-based integral references
        to other node entities within this batch::

            # create a single node
            alice, = graph_db.create({"name": "Alice"})

            # create multiple nodes
            people = graph_db.create(
                {"name": "Alice", "age": 33}, {"name": "Bob", "age": 44},
                {"name": "Carol", "age": 55}, {"name": "Dave", "age": 66},
            )

            # create two nodes with a connecting relationship
            alice, bob, rel = graph_db.create(
                {"name": "Alice"}, {"name": "Bob"},
                (0, "KNOWS", 1, {"since": 2006})
            )

            # create a node plus a relationship to pre-existing node
            ref_node = graph_db.get_reference_node()
            alice, rel = graph_db.create(
                {"name": "Alice"}, (ref_node, "PERSON", 0)
            )

        .. warning::
            This method will *always* return a list, even when only creating
            a single node or relationship. To automatically unpack a list
            containing a single item, append a trailing comma to the variable
            name on the left of the assignment operation.

        """
        if not abstracts:
            return []
        batch = WriteBatch(self)
        for abstract in abstracts:
            batch.create(abstract)
        return batch.submit()

    @property
    def cypher(self):
        return Cypher.get_instance(self.__metadata__["cypher"])

    def delete(self, *entities):
        """ Delete multiple nodes and/or relationships as part of a single
        batch.
        """
        if not entities:
            return
        batch = WriteBatch(self)
        for entity in entities:
            if entity is None:
                continue
            else:
                batch.delete(entity)
        batch._submit()

    def find(self, label, property_key=None, property_value=None):
        if property_key:
            uri = "{0}label/{1}/nodes?{2}={3}".format(
                self.__uri__, str(label), quote(property_key),
                quote(json.dumps(property_value))
            )
        else:
            uri = "{0}label/{1}/nodes".format(self.__uri__, str(label))
        try:
            return [
                Node(result["self"])
                for result in self._send(rest.Request(self, "GET", uri)).body
            ]
        except rest.ResourceNotFound:
            return None

    def get_properties(self, *entities):
        """ Fetch properties for multiple nodes and/or relationships as part
        of a single batch; returns a list of dictionaries in the same order
        as the supplied entities.
        """
        if not entities:
            return []
        if len(entities) == 1:
            return [entities[0].get_properties()]
        batch = ReadBatch(self)
        for entity in entities:
            batch.get_properties(entity)
        return [rs.body or {} for rs in batch._submit()]

    def match(self, start_node=None, rel_type=None, end_node=None,
              bidirectional=False, limit=None):
        """ Fetch all relationships which match a specific set of criteria. The
        arguments provided are all optional and are used to filter the
        relationships returned. Examples are as follows::

            # all relationships from the graph database
            # ()-[r]-()
            rels = graph_db.match()

            # all relationships outgoing from `alice`
            # (alice)-[r]->()
            rels = graph_db.match(start_node=alice)

            # all relationships incoming to `alice`
            # ()-[r]->(alice)
            rels = graph_db.match(end_node=alice)

            # all relationships attached to `alice`, regardless of direction
            # (alice)-[r]-()
            rels = graph_db.match(start_node=alice, bidirectional=True)

            # all relationships from `alice` to `bob`
            # (alice)-[r]->(bob)
            rels = graph_db.match(start_node=alice, end_node=bob)

            # all relationships outgoing from `alice` of type "FRIEND"
            # (alice)-[r:FRIEND]->()
            rels = graph_db.match(start_node=alice, rel_type="FRIEND")

            # up to three relationships outgoing from `alice` of type "FRIEND"
            # (alice)-[r:FRIEND]->()
            rels = graph_db.match(start_node=alice, rel_type="FRIEND", limit=3)

        :param start_node: concrete start :py:class:`Node` to match or
            :py:const:`None` if any
        :param rel_type: type of relationships to match or :py:const:`None` if
            any
        :param end_node: concrete end :py:class:`Node` to match or
            :py:const:`None` if any
        :param bidirectional: :py:const:`True` if reversed relationships should
            also be included
        :param limit: maximum number of relationships to match or
            :py:const:`None` if no limit
        """
        if start_node is None and end_node is None:
            query = "START a=node(*)"
            params = {}
        elif end_node is None:
            query = "START a=node({A})"
            start_node = _cast(start_node, Node, abstract=False)
            params = {"A": start_node._id}
        elif start_node is None:
            query = "START b=node({B})"
            end_node = _cast(end_node, Node, abstract=False)
            params = {"B": end_node._id}
        else:
            query = "START a=node({A}),b=node({B})"
            start_node = _cast(start_node, Node, abstract=False)
            end_node = _cast(end_node, Node, abstract=False)
            params = {"A": start_node._id, "B": end_node._id}
        if rel_type is None:
            if bidirectional:
                query += " MATCH (a)-[r]-(b) RETURN r"
            else:
                query += " MATCH (a)-[r]->(b) RETURN r"
        else:
            if bidirectional:
                query += " MATCH (a)-[r:`" + str(rel_type) + "`]-(b) RETURN r"
            else:
                query += " MATCH (a)-[r:`" + str(rel_type) + "`]->(b) RETURN r"
        if limit is not None:
            query += " LIMIT {0}".format(int(limit))
        data, metadata = cypher.execute(self, query, params)
        return [row[0] for row in data]

    def match_one(self, start_node=None, rel_type=None, end_node=None,
                  bidirectional=False):
        """ Fetch a single relationship which matches a specific set of
        criteria.

        :param start_node: concrete start :py:class:`Node` to match or
            :py:const:`None` if any
        :param rel_type: type of relationships to match or :py:const:`None` if
            any
        :param end_node: concrete end :py:class:`Node` to match or
            :py:const:`None` if any
        :param bidirectional: :py:const:`True` if reversed relationships should
            also be included

        .. seealso::
           :py:func:`GraphDatabaseService.match <py2neo.neo4j.GraphDatabaseService.match>`
        """
        rels = self.match(start_node, rel_type, end_node, bidirectional, 1)
        if rels:
            return rels[0]
        else:
            return None

    @property
    def neo4j_version(self):
        return version_tuple(self.__metadata__["neo4j_version"])

    def node(self, id):
        """ Fetch a node by ID.
        """
        return Node(self.__metadata__['node'] + "/" + str(id))

    @property
    def node_labels(self):
        """ Return the set of node labels currently defined within this
        database instance.
        """
        uri = "{0}labels".format(self.__uri__)
        try:
            return set(self._send(rest.Request(self, "GET", uri)).body)
        except rest.ResourceNotFound:
            return None

    def order(self):
        """ Fetch the number of nodes in this graph.
        """
        data, metadata = cypher.execute(self, "START n=node(*) RETURN count(n)")
        if data and data[0]:
            return data[0][0]
        else:
            raise EnvironmentError("Unable to count nodes")

    def relationship(self, id):
        """ Fetch a relationship by ID.
        """
        uri = "{0}relationship/{1}".format(self.__uri__.base, id)
        return Relationship(uri)

    @property
    def relationship_types(self):
        """ Return the set of relationship types currently defined within this
        database instance.
        """
        uri = self.__metadata__['relationship_types']
        return set(self._send(rest.Request(self, "GET", uri)).body)

    def size(self):
        """ Fetch the number of relationships in this graph.
        """
        data, metadata = cypher.execute(self, "START r=rel(*) RETURN count(r)")
        if data and data[0]:
            return data[0][0]
        else:
            raise EnvironmentError("Unable to count relationships")

    def get_indexes(self, content_type):
        """ Fetch a dictionary of all available indexes of a given type.

        :param content_type: either :py:class:`neo4j.Node` or
            :py:class:`neo4j.Relationship`
        :return: a list of :py:class:`Index` instances of the specified type
        """
        if content_type == Node:
            rq = rest.Request(self, "GET", self.__metadata__['node_index'])
        elif content_type == Relationship:
            rq = rest.Request(self, "GET", self.__metadata__['relationship_index'])
        else:
            raise ValueError(content_type)
        rs = self._send(rq)
        indexes = rs.body or {}
        self._indexes[content_type] = dict(
            (index, Index(content_type, indexes[index]['template']))
            for index in indexes
        )
        return self._indexes[content_type]

    def get_index(self, content_type, index_name):
        """ Fetch a specific index from the current database, returning an
        :py:class:`Index` instance. If an index with the supplied `name` and
        content `type` does not exist, :py:const:`None` is returned.

        :param content_type: either :py:class:`neo4j.Node` or
            :py:class:`neo4j.Relationship`
        :param index_name: the name of the required index
        :return: an :py:class:`Index` instance or :py:const:`None`

        .. seealso:: :py:func:`get_or_create_index`
        .. seealso:: :py:class:`Index`
        """
        if index_name not in self._indexes[content_type]:
            self.get_indexes(content_type)
        if index_name in self._indexes[content_type]:
            return self._indexes[content_type][index_name]
        else:
            return None

    def get_or_create_index(self, content_type, index_name, config=None):
        """ Fetch a specific index from the current database, returning an
        :py:class:`Index` instance. If an index with the supplied `name` and
        content `type` does not exist, one is created with either the
        default configuration or that supplied in `config`::

            # get or create a node index called "People"
            people = graph_db.get_or_create_index(neo4j.Node, "People")

            # get or create a relationship index called "Friends"
            friends = graph_db.get_or_create_index(neo4j.Relationship, "Friends")

        :param content_type: either :py:class:`neo4j.Node` or
            :py:class:`neo4j.Relationship`
        :param index_name: the name of the required index
        :return: an :py:class:`Index` instance

        .. seealso:: :py:func:`get_index`
        .. seealso:: :py:class:`Index`
        """
        if index_name not in self._indexes[content_type]:
            self.get_indexes(content_type)
        if index_name in self._indexes[content_type]:
            return self._indexes[content_type][index_name]
        if content_type == Node:
            uri = self.__metadata__['node_index']
        elif content_type == Relationship:
            uri = self.__metadata__['relationship_index']
        else:
            raise ValueError(content_type)
        config = config or {}
        rs = self._send(rest.Request(self, "POST", uri, {"name": index_name, "config": config}))
        index = Index(content_type, rs.body["template"])
        self._indexes[content_type].update({index_name: index})
        return index

    def delete_index(self, content_type, index_name):
        """ Delete the entire index identified by the type and name supplied.

        :param content_type: either :py:class:`neo4j.Node` or
            :py:class:`neo4j.Relationship`
        :param index_name: the name of the required index
        :return: :py:const:`True` if the index was deleted, :py:const:`False`
            otherwise
        """
        if index_name not in self._indexes[content_type]:
            self.get_indexes(content_type)
        if index_name in self._indexes[content_type]:
            index = self._indexes[content_type][index_name]
            self._send(rest.Request(self, "DELETE", index.__uri__))
            del self._indexes[content_type][index_name]
            return True
        else:
            return False

    def get_indexed_node(self, index_name, key, value):
        """ Fetch the first node indexed with the specified details, returning
        :py:const:`None` if none found.

        :param index_name: the name of the required index
        :param key: the index key
        :param value: the index value
        :return: a :py:class:`Node` instance
        """
        index = self.get_index(Node, index_name)
        if index:
            nodes = index.get(key, value)
            if nodes:
                return nodes[0]
        return None

    def get_or_create_indexed_node(self, index_name, key, value, properties=None):
        """ Fetch the first node indexed with the specified details, creating
        and returning a new indexed node if none found.

        :param index_name: the name of the required index
        :param key: the index key
        :param value: the index value
        :param properties: properties for the new node, if one is created
            (optional)
        :return: a :py:class:`Node` instance
        """
        index = self.get_or_create_index(Node, index_name)
        return index.get_or_create(key, value, properties or {})

    def get_indexed_relationship(self, index_name, key, value):
        """ Fetch the first relationship indexed with the specified details,
        returning :py:const:`None` if none found.

        :param index_name: the name of the required index
        :param key: the index key
        :param value: the index value
        :return: a :py:class:`Relationship` instance
        """
        index = self.get_index(Relationship, index_name)
        if index:
            relationships = index.get(key, value)
            if relationships:
                return relationships[0]
        return None


class Cypher(Cacheable, Resource):

    class Query(object):

        def __init__(self, cypher, query):
            self._cypher = cypher
            self._query = query

        def execute(self, **params):
            try:
                results = self._cypher._post({
                    "query": self._query,
                    "params": params,
                })
            except ClientError as e:
                if e.exception:
                    # A CustomCypherError is a dynamically created subclass of
                    # CypherError with the same name as the underlying server
                    # exception
                    CustomCypherError = type(e.exception, (CypherError,), {})
                    raise CustomCypherError(e)
                else:
                    raise CypherError(e)
            else:
                return Cypher.ResultSet(results)

    class ResultSet(object):

        signature = ("columns", "data")

        @classmethod
        def _hydrated(cls, data):
            """ Takes assembled data...
            """
            record = namedtuple("Record", data["columns"], rename=True)
            return [record(*_hydrated(row)) for row in data["data"]]

        @staticmethod
        def _row_id(result):
            key, value = result
            if key[0] == "columns":
                return key[0:1]
            else:
                return key[0:2]

        def __init__(self, results):
            self._results = results
            self._columns = None
            self._record = None

        def __iter__(self):
            for row_id, result in groupby(self._results, self._row_id):
                if row_id[0] == "columns":
                    self._columns = tuple(_hydrated(assembled(result, key_offset=1)))
                    self._record = namedtuple("Record", self._columns,
                                              rename=True)
                else:
                    yield self._record(*_hydrated(assembled(result, key_offset=2)))

        @property
        def columns(self):
            return self._columns

    def query(self, query):
        return Cypher.Query(self, query)

    def execute(self, query, **params):
        return Cypher.Query(self, query).execute(**params)

    def execute_one(self, query, **params):
        for row in Cypher.Query(self, query).execute(**params):
            return row[0]


class _Entity(Resource):
    """ Base class from which :py:class:`Node` and :py:class:`Relationship`
    classes inherit. Provides property management functionality by defining
    standard Python container handler methods.
    """

    def __init__(self, uri):
        Resource.__init__(self, uri)
        self._properties = {}

    def __contains__(self, key):
        return key in self.get_properties()

    def __delitem__(self, key):
        self.update_properties({key: None})

    def __getitem__(self, key):
        return self.get_properties().get(key, None)

    def __iter__(self):
        return self.get_properties().__iter__()

    def __len__(self):
        return len(self.get_properties())

    def __nonzero__(self):
        return True

    def __setitem__(self, key, value):
        self.update_properties({key: value})

    @property
    def _properties_resource(self):
        return self._subresource("properties")

    def delete(self):
        """ Delete this entity from the database.
        """
        self._delete()

    def exists(self):
        """ Determine whether this entity still exists in the database.
        """
        # TODO: make this a property
        try:
            self._get()
        except ClientError as err:
            if err.status_code == NOT_FOUND:
                return False
            else:
                raise
        else:
            return True

    def get_properties(self):
        """ Fetch all properties.

        :return: dictionary of properties
        """
        if not self.is_abstract:
            self._properties = assembled(self._properties_resource._get()) or {}
        return self._properties

    def set_properties(self, properties):
        """ Replace all properties with those supplied.

        :param properties: dictionary of new properties
        """
        self._properties = dict(properties)
        if not self.is_abstract:
            if self._properties:
                self._properties_resource._put(compact(self._properties))
            else:
                self._properties_resource._delete()

    def delete_properties(self):
        """ Delete all properties.
        """
        self.set_properties({})

    def update_properties(self, properties):
        raise NotImplementedError("_Entity.update_properties")


class LabelSet(Resource):

    @classmethod
    def abstract(cls, *labels):
        """ Create and return a new abstract label set containing labels drawn
        from the arguments supplied.
        """
        instance = cls(None)
        instance._labels = set(labels)
        return instance

    def __init__(self, uri):
        Resource.__init__(self, uri)
        self._labels = set()

    def __eq__(self, other):
        other = _cast(other, Node)
        if self.__uri__:
            return Resource.__eq__(self, other)
        else:
            return self._labels == other._labels

    def __ne__(self, other):
        other = _cast(other, Node)
        if self.__uri__:
            return Resource.__ne__(self, other)
        else:
            return self._labels != other._labels

    def __repr__(self):
        if self.__uri__:
            return "{0}({1})".format(
                self.__class__.__name__,
                repr(str(self.__uri__)),
            )
        else:
            return "{0}.abstract({1})".format(
                self.__class__.__name__,
                ", ".join(repr(label) for label in sorted(self._labels)),
            )

    def __str__(self):
        return ":".join(sorted(self._labels))

    def __hash__(self):
        if self.__uri__:
            return hash(self.__uri__)
        else:
            return hash(frozenset(self._labels))

    def refresh(self):
        if self.__uri__:
            self._labels = set(assembled(self._get()))

    def __contains__(self, item):
        self.refresh()
        return item in self._labels

    def __iter__(self):
        self.refresh()
        return iter(self._labels)

    def __len__(self):
        self.refresh()
        return len(self._labels)

    def is_abstract(self):
        return self.__uri__ is None

    def add(self, *labels):
        labels = [str(label) for label in flatten(labels)]
        if self.__uri__:
            # TODO: batch
            self._post(labels)
            self.refresh()
        else:
            self._labels.update(labels)

    def remove(self, *labels):
        labels = [str(label) for label in flatten(labels)]
        if self.__uri__:
            # TODO: batch
            for label in labels:
                Resource(URI.join(self.__uri__, label))._delete()
            self.refresh()
        else:
            self._labels.remove(labels)

    def replace(self, *labels):
        labels = [str(label) for label in flatten(labels)]
        if self.__uri__:
            # TODO: batch
            self._put(labels)
            self.refresh()
        else:
            self._labels = set(labels)


class Node(_Entity):
    """ A node within a graph, identified by a URI. For example:

        >>> alice = Node("http://localhost:7474/db/data/node/1")

    Typically, concrete nodes will not be constructed directly in this way
    by client applications. Instead, methods such as
    :py:func:`GraphDatabaseService.create` build node objects indirectly as
    required. Once created, however, nodes can be treated like any other
    container types in order to manage properties::

        # get the `name` property of `node`
        name = node["name"]

        # set the `name` property of `node` to `Alice`
        node["name"] = "Alice"

        # delete the `name` property from `node`
        del node["name"]

        # determine the number of properties within `node`
        count = len(node)

        # determine existence of the `name` property within `node`
        if "name" in node:
            pass

        # iterate through property keys in `node`
        for key in node:
            value = node[key]

    :param uri: URI identifying this node
    """

    signature = ("self",)

    @classmethod
    def _hydrated(cls, data):
        obj = cls(data["self"])
        obj._metadata = Resource.Metadata(data)
        obj._properties = data.get("data", {})
        return obj

    @classmethod
    def abstract(cls, *labels, **properties):
        """ Create and return a new abstract node containing properties drawn
        from the keyword arguments supplied. An abstract node is not bound to
        a concrete node within a database but properties can be managed
        similarly to those within bound nodes::

            >>> alice = Node.abstract(name="Alice")
            >>> alice["name"]
            'Alice'
            >>> alice["age"] = 34
            alice.get_properties()
            {'age': 34, 'name': 'Alice'}

        If more complex property keys are required, abstract nodes may be
        instantiated with the ``**`` syntax::

            >>> alice = Node.abstract(**{"first name": "Alice"})
            >>> alice["first name"]
            'Alice'

        :param properties: node properties
        """
        instance = cls(None)
        instance._labels = set(labels)
        instance._labels_supported = True
        instance._properties = dict(properties)
        return instance

    def __init__(self, uri):
        _Entity.__init__(self, uri)
        self._labels = None
        self._labels_supported = None

    def __eq__(self, other):
        other = _cast(other, Node)
        if self.__uri__:
            return _Entity.__eq__(self, other)
        else:
            return self.labels == other.labels and \
                   self._properties == other._properties

    def __ne__(self, other):
        other = _cast(other, Node)
        if self.__uri__:
            return _Entity.__ne__(self, other)
        else:
            return self.labels != other.labels or \
                   self._properties != other._properties

    def __repr__(self):
        if self.__uri__:
            return "{0}({1})".format(
                self.__class__.__name__,
                repr(str(self.__uri__))
            )
        elif self._properties:
            return "node(**{1})".format(
                self.__class__.__name__,
                repr(self._properties)
            )
        else:
            return "node()".format(
                self.__class__.__name__
            )

    def __str__(self):
        """ Return Cypher/Geoff style representation of this node.
        """
        if self.is_abstract:
            return "({0})".format(json.dumps(self._properties, separators=(",", ":")))
        elif self._properties:
            return "({0} {1})".format(
                "" if self._id is None else self._id,
                json.dumps(self._properties, separators=(",", ":")),
            )
        else:
            return "({0})".format("" if self._id is None else self._id)

    def __hash__(self):
        if self.__uri__:
            return hash(self.__uri__)
        else:
            return hash((
                self.labels,
                tuple(sorted(self._properties.items())),
            ))

    @property
    def _id(self):
        """ Return the internal ID for this node.

        :return: integer ID of this node within the database or
            :py:const:`None` if abstract
        """
        if self.is_abstract:
            return None
        else:
            return int('0' + str(self.__uri__).rpartition('/')[-1])

    @property
    def labels(self):
        if self._labels_supported is None:
            try:
                self._labels = self._subresource("labels", LabelSet)
                self._labels_supported = True
            except KeyError:
                self._labels = None
                self._labels_supported = False
        return self._labels

    def delete_related(self):
        """ Delete this node, plus all related nodes and relationships.
        """
        self.cypher.query(
            "START a=node({a}) "
            "MATCH (a)-[rels*0..]-(z) "
            "FOREACH(rel IN rels: DELETE rel) "
            "DELETE a, z"
        ).execute(a=self._id)

    def isolate(self):
        """ Delete all relationships connected to this node, both incoming and
        outgoing.
        """
        self.cypher.query(
            "START a=node({A}) "
            "MATCH a-[r]-b "
            "DELETE r "
        ).execute(A=self._id)

    def match(self, rel_type=None, end_node=None, bidirectional=False,
              limit=None):
        """ Match one or more relationships attached to this node.

        :param rel_type: type of relationships to match or :py:const:`None` if
            any
        :param end_node: concrete end :py:class:`Node` to match or
            :py:const:`None` if any
        :param bidirectional: :py:const:`True` if reversed relationships should
            also be included
        :param limit: maximum number of relationships to match or
            :py:const:`None` if no limit

        .. seealso::
           :py:func:`GraphDatabaseService.match <py2neo.neo4j.GraphDatabaseService.match>`
        """
        return self.service_root.graph_db.match(self, rel_type, end_node, bidirectional, limit)

    def match_one(self, rel_type=None, end_node=None, bidirectional=False):
        """ Match a single relationship attached to this node.

        :param rel_type: type of relationships to match or :py:const:`None` if
            any
        :param end_node: concrete end :py:class:`Node` to match or
            :py:const:`None` if any
        :param bidirectional: :py:const:`True` if reversed relationships should
            also be included

        .. seealso::
           :py:func:`GraphDatabaseService.match <py2neo.neo4j.GraphDatabaseService.match>`
        """
        return self.service_root.graph_db.match(self, rel_type, end_node, bidirectional)

    def create_path(self, *items):
        """ Create a new path, starting at this node and chaining together the
        alternating relationships and nodes provided::

            (self)-[rel_0]->(node_0)-[rel_1]->(node_1) ...
                   |-----|  |------| |-----|  |------|
             item:    0        1        2        3

        Each relationship may be specified as one of the following:

        - an existing Relationship instance
        - a string holding the relationship type, e.g. "KNOWS"
        - a (`str`, `dict`) tuple holding both the relationship type and
          its properties, e.g. ("KNOWS", {"since": 1999})

        Nodes can be any of the following:

        - an existing Node instance
        - an integer containing the ID of an existing node
        - a `dict` holding a set of properties for a new node
        - a 3-tuple holding an index name, key and value for identifying
          indexed nodes, e.g. ("People", "email", "bob@example.com")
        - :py:const:`None`, representing an unspecified node that will be
          created as required

        :param items: alternating relationships and nodes
        :return: `Path` object representing the newly-created path
        """
        path = Path(self, *items)
        return path.create(self._graph_db)

    def get_or_create_path(self, *items):
        """ Identical to `create_path` except will reuse parts of the path
        which already exist.

        Some examples::

            # add dates to calendar, starting at calendar_root
            christmas_day = calendar_root.get_or_create_path(
                "YEAR",  {"number": 2000},
                "MONTH", {"number": 12},
                "DAY",   {"number": 25},
            )
            # `christmas_day` will now contain a `Path` object
            # containing the nodes and relationships used:
            # (CAL)-[:YEAR]->(2000)-[:MONTH]->(12)-[:DAY]->(25)

            # adding a second, overlapping path will reuse
            # nodes and relationships wherever possible
            christmas_eve = calendar_root.get_or_create_path(
                "YEAR",  {"number": 2000},
                "MONTH", {"number": 12},
                "DAY",   {"number": 24},
            )
            # `christmas_eve` will contain the same year and month nodes
            # as `christmas_day` but a different (new) day node:
            # (CAL)-[:YEAR]->(2000)-[:MONTH]->(12)-[:DAY]->(25)
            #                                  |
            #                                [:DAY]
            #                                  |
            #                                  v
            #                                 (24)

        """
        path = Path(self, *items)
        return path.get_or_create(self._graph_db)

    def update_properties(self, properties):
        """ Update properties with the values supplied.

        :param properties: dictionary of properties to integrate with existing
            properties
        """
        if self.__uri__:
            query, params = ["START a=node({A})"], {"A": self._id}
            for i, (key, value) in enumerate(properties.items()):
                value_tag = "V" + str(i)
                query.append("SET a.`" + key + "`={" + value_tag + "}")
                params[value_tag] = value
            query.append("RETURN a")
            data, metadata = cypher.execute(self._graph_db, " ".join(query), params)
            self._properties = data[0][0].__metadata__["data"]
        else:
            self._properties.update(properties)


class Relationship(_Entity):
    """ A relationship within a graph, identified by a URI.

    :param uri: URI identifying this relationship
    """

    signature = ("self", "type")

    @classmethod
    def _hydrated(cls, data):
        obj = cls(data["self"])
        obj._metadata = Resource.Metadata(data)
        obj._properties = data.get("data", {})
        return obj

    @classmethod
    def abstract(cls, start_node, type, end_node, **properties):
        """ Create and return a new abstract relationship.
        """
        instance = cls(None)
        instance._start_node = start_node
        instance._type = type
        instance._end_node = end_node
        instance._properties = dict(properties)
        return instance

    def __init__(self, uri):
        _Entity.__init__(self, uri)
        self._start_node = None
        self._type = None
        self._end_node = None

    def __eq__(self, other):
        other = _cast(other, Relationship)
        if self.__uri__:
            return _Entity.__eq__(self, other)
        else:
            return self._start_node == other._start_node and \
                   self._type == other._type and \
                   self._end_node == other._end_node and \
                   self._properties == other._properties

    def __ne__(self, other):
        other = _cast(other, Relationship)
        if self.__uri__:
            return _Entity.__ne__(self, other)
        else:
            return self._start_node != other._start_node or \
                   self._type != other._type or \
                   self._end_node != other._end_node or \
                   self._properties != other._properties

    def __repr__(self):
        if self.__uri__:
            return "{0}({1})".format(
                self.__class__.__name__,
                repr(str(self.__uri__))
            )
        elif self._properties:
            return "rel({1}, {2}, {3}, **{4})".format(
                self.__class__.__name__,
                repr(self.start_node),
                repr(self.type),
                repr(self.end_node),
                repr(self._properties)
            )
        else:
            return "rel({1}, {2}, {3})".format(
                self.__class__.__name__,
                repr(self.start_node),
                repr(self.type),
                repr(self.end_node)
            )

    def __str__(self):
        type_str = str(self.type)
        if not SIMPLE_NAME.match(type_str):
            type_str = json.dumps(type_str)
        if self._properties:
            return "{0}-[:{1} {2}]->{3}".format(
                str(self.start_node),
                type_str,
                json.dumps(self._properties, separators=(",", ":")),
                str(self.end_node),
            )
        else:
            return "{0}-[:{1}]->{2}".format(
                str(self.start_node),
                type_str,
                str(self.end_node),
            )

    def __hash__(self):
        if self.__uri__:
            return hash(self.__uri__)
        else:
            return hash(tuple(sorted(self._properties.items())))

    @property
    def _id(self):
        """ Return the internal ID for this relationship.

        :return: integer ID of this relationship within the database or
            :py:const:`None` if abstract
        """
        if self.is_abstract:
            return None
        else:
            return int('0' + str(self.__uri__).rpartition('/')[-1])

    @property
    def end_node(self):
        """ Return the end node of this relationship.
        """
        if self.__uri__ and not self._end_node:
            self._end_node = Node(self.__metadata__['end'])
        return self._end_node

    @property
    def start_node(self):
        """ Return the start node of this relationship.
        """
        if self.__uri__ and not self._start_node:
            self._start_node = Node(self.__metadata__['start'])
        return self._start_node

    @property
    def type(self):
        """ Return the type of this relationship as a string.
        """
        if self.__uri__ and not self._type:
            self._type = self.__metadata__['type']
        return self._type

    def update_properties(self, properties):
        """ Update the properties for this relationship with the values
        supplied.
        """
        if self.__uri__:
            query, params = ["START a=rel({A})"], {"A": self._id}
            for i, (key, value) in enumerate(properties.items()):
                value_tag = "V" + str(i)
                query.append("SET a.`" + key + "`={" + value_tag + "}")
                params[value_tag] = value
            query.append("RETURN a")
            data, metadata = cypher.execute(self._graph_db, " ".join(query), params)
            self._properties = data[0][0].__metadata__["data"]
        else:
            self._properties.update(properties)


class _UnboundRelationship(object):
    """ An abstract, partial relationship with no start or end nodes.
    """

    @classmethod
    def cast(cls, arg):
        if isinstance(arg, cls):
            return arg
        elif isinstance(arg, Relationship):
            return cls(arg.type, **arg.get_properties())
        elif isinstance(arg, tuple):
            if len(arg) == 1:
                return cls(str(arg[0]))
            elif len(arg) == 2:
                return cls(str(arg[0]), **arg[1])
            else:
                raise TypeError(arg)
        else:
            return cls(str(arg))

    def __init__(self, type, **properties):
        self._type = type
        self._properties = dict(properties)

    def __eq__(self, other):
        return self._type == other._type and \
               self._properties == other._properties

    def __ne__(self, other):
        return self._type != other._type or \
               self._properties != other._properties

    def __repr__(self):
        return "({0}, *{1}, **{2})".format(
            repr(str(self._type)),
            repr(self._properties),
        )

    def __str__(self):
        return "-[:{0}]->".format(
            json.dumps(str(self._type)),
        )

    def bind(self, start_node, end_node):
        return Relationship.abstract(start_node, self._type, end_node,
                                     **self._properties)


class Path(object):
    """ A representation of a sequence of nodes connected by relationships. for
    example::

        >>> from py2neo import neo4j, node
        >>> alice, bob, carol = node(name="Alice"), node(name="Bob"), node(name="Carol")
        >>> abc = neo4j.Path(alice, "KNOWS", bob, "KNOWS", carol)
        >>> abc.nodes
        [node(**{'name': 'Alice'}), node(**{'name': 'Bob'}), node(**{'name': 'Carol'})]
        >>> dave, eve = node(name="Dave"), node(name="Eve")
        >>> de = neo4j.Path(dave, "KNOWS", eve)
        >>> de.nodes
        [node(**{'name': 'Dave'}), node(**{'name': 'Eve'})]
        >>> abcde = neo4j.Path.join(abc, "KNOWS", de)
        >>> str(abcde)
        '({"name":"Alice"})-[:"KNOWS"]->({"name":"Bob"})-[:"KNOWS"]->({"name":"Carol"})-[:"KNOWS"]->({"name":"Dave"})-[:"KNOWS"]->({"name":"Eve"})'

    """

    signature = ("length", "nodes", "relationships", "start", "end")

    @classmethod
    def _hydrated(cls, data):
        return "PATH"

    def __init__(self, node, *rels_and_nodes):
        self._nodes = [_node(node)]
        self._nodes.extend(_node(n) for n in rels_and_nodes[1::2])
        if len(rels_and_nodes) % 2 != 0:
            # If a trailing relationship is supplied, add a dummy end node
            self._nodes.append(_node())
        self._relationships = [
            _UnboundRelationship.cast(r)
            for r in rels_and_nodes[0::2]
        ]

    def __repr__(self):
        out = ", ".join(repr(item) for item in round_robin(self._nodes, self._relationships))
        return "Path({0})".format(out)

    def __str__(self):
        out = []
        for i, rel in enumerate(self._relationships):
            out.append(str(self._nodes[i]))
            out.append(str(rel))
        out.append(str(self._nodes[-1]))
        return "".join(out)

    def __nonzero__(self):
        return bool(self._relationships)

    def __len__(self):
        return len(self._relationships)

    def __eq__(self, other):
        return self._nodes == other._nodes and \
               self._relationships == other._relationships

    def __ne__(self, other):
        return self._nodes != other._nodes or \
               self._relationships != other._relationships

    def __getitem__(self, item):
        size = len(self._relationships)
        def adjust(value, default=None):
            if value is None:
                return default
            if value < 0:
                return value + size
            else:
                return value
        if isinstance(item, slice):
            if item.step is not None:
                raise ValueError("Steps not supported in path slicing")
            start, stop = adjust(item.start, 0), adjust(item.stop, size)
            path = Path(self._nodes[start])
            for i in range(start, stop):
                path._relationships.append(self._relationships[i])
                path._nodes.append(self._nodes[i + 1])
            return path
        else:
            i = int(item)
            if i < 0:
                i += len(self._relationships)
            return Path(self._nodes[i], self._relationships[i], self._nodes[i + 1])

    def __iter__(self):
        return iter(
            _rel((self._nodes[i], rel, self._nodes[i + 1]))
            for i, rel in enumerate(self._relationships)
        )

    def order(self):
        """ Return the number of nodes within this path.
        """
        return len(self._nodes)

    def size(self):
        """ Return the number of relationships within this path.
        """
        return len(self._relationships)

    @property
    def nodes(self):
        """ Return a list of all the nodes which make up this path.
        """
        return list(self._nodes)

    @property
    def relationships(self):
        """ Return a list of all the relationships which make up this path.
        """
        return [
            _rel((self._nodes[i], rel, self._nodes[i + 1]))
            for i, rel in enumerate(self._relationships)
        ]

    @classmethod
    def join(cls, left, rel, right):
        """ Join the two paths `left` and `right` with the relationship `rel`.
        """
        if isinstance(left, Path):
            left = left[:]
        else:
            left = Path(left)
        if isinstance(right, Path):
            right = right[:]
        else:
            right = Path(right)
        left._relationships.append(_UnboundRelationship.cast(rel))
        left._nodes.extend(right._nodes)
        left._relationships.extend(right._relationships)
        return left

    def _create(self, graph_db, verb):
        nodes, path, values, params = [], [], [], {}
        def append_node(i, node):
            if node is None:
                path.append("(n{0})".format(i))
                values.append("n{0}".format(i))
            elif node.is_abstract:
                path.append("(n{0} {{p{0}}})".format(i))
                params["p{0}".format(i)] = compact(node._properties)
                values.append("n{0}".format(i))
            else:
                path.append("(n{0})".format(i))
                nodes.append("n{0}=node({{i{0}}})".format(i))
                params["i{0}".format(i)] = node._id
                values.append("n{0}".format(i))
        def append_rel(i, rel):
            if rel._properties:
                path.append("-[r{0}:`{1}` {{q{0}}}]->".format(i, rel._type))
                params["q{0}".format(i)] = compact(rel._properties)
                values.append("r{0}".format(i))
            else:
                path.append("-[r{0}:`{1}`]->".format(i, rel._type))
                values.append("r{0}".format(i))
        append_node(0, self._nodes[0])
        for i, rel in enumerate(self._relationships):
            append_rel(i, rel)
            append_node(i + 1, self._nodes[i + 1])
        clauses = []
        if nodes:
            clauses.append("START {0}".format(",".join(nodes)))
        clauses.append("{0} {1}".format(verb, "".join(path)))
        clauses.append("RETURN {0}".format(",".join(values)))
        query = " ".join(clauses)
        try:
            data, metadata = cypher.execute(graph_db, query, params)
            return Path(*data[0])
        except cypher.CypherError:
            raise NotImplementedError(
                "The Neo4j server at <{0}> does not support "
                "Cypher CREATE UNIQUE clauses or the query contains "
                "an unsupported property type".format(graph_db.__uri__)
            )

    def create(self, graph_db):
        """ Construct a path within the specified `graph_db` from the nodes
        and relationships within this :py:class:`Path` instance. This makes
        use of Cypher's ``CREATE`` clause.
        """
        return self._create(graph_db, "CREATE")

    def get_or_create(self, graph_db):
        """ Construct a unique path within the specified `graph_db` from the
        nodes and relationships within this :py:class:`Path` instance. This
        makes use of Cypher's ``CREATE UNIQUE`` clause.
        """
        return self._create(graph_db, "CREATE UNIQUE")


class Index(Resource):
    """ Searchable database index which can contain either nodes or
    relationships.

    .. seealso:: :py:func:`GraphDatabaseService.get_or_create_index`
    """

    def __init__(self, content_type, template_uri):
        Resource.__init__(
            self, template_uri.rpartition("/{key}/{value}")[0]
        )
        self._name = str(self.__uri__).rpartition("/")[2]
        self._content_type = content_type
        self._template_uri = template_uri

    def __repr__(self):
        return "{0}({1},'{2}')".format(
            self.__class__.__name__,
            repr(self._content_type.__name__),
            repr(self.__uri__)
        )

    def add(self, key, value, entity):
        """ Add an entity to this index under the `key`:`value` pair supplied::

            # create a node and obtain a reference to the "People" node index
            alice, = graph_db.create({"name": "Alice Smith"})
            people = graph_db.get_or_create_index(neo4j.Node, "People")

            # add the node to the index
            people.add("family_name", "Smith", alice)

        Note that while Neo4j indexes allow multiple entities to be added under
        a particular key:value, the same entity may only be represented once;
        this method is therefore idempotent.
        """
        self._post({
            "key": key,
            "value": value,
            "uri": str(entity.__uri__)
        })
        return entity

    def add_if_none(self, key, value, entity):
        """ Add an entity to this index under the `key`:`value` pair
        supplied if no entry already exists at that point::

            # obtain a reference to the "Rooms" node index and
            # add node `alice` to room 100 if empty
            rooms = graph_db.get_or_create_index(neo4j.Node, "Rooms")
            rooms.add_if_none("room", 100, alice)

        If added, this method returns the entity, otherwise :py:const:`None`
        is returned.
        """
        rs = self._send(rest.Request(self._graph_db, "POST", str(self.__uri__) + "?unique", {
            "key": key,
            "value": value,
            "uri": str(entity.__uri__)
        }))
        if rs.status == 201:
            return entity
        else:
            return None

    @property
    def content_type(self):
        """ Return the type of entity contained within this index. Will return
        either :py:class:`Node` or :py:class:`Relationship`.
        """
        return self._content_type

    @property
    def name(self):
        """ Return the name of this index.
        """
        return self._name

    def get(self, key, value):
        """ Fetch a list of all entities from the index which are associated
        with the `key`:`value` pair supplied::

            # obtain a reference to the "People" node index and
            # get all nodes where `family_name` equals "Smith"
            people = graph_db.get_or_create_index(neo4j.Node, "People")
            smiths = people.get("family_name", "Smith")

        ..
        """
        results = self._send(rest.Request(self._graph_db, "GET", self._template_uri.format(
            key=quote(key, ""),
            value=quote(value, "")
        )))
        return [
            self._content_type(result['self'])
            for result in results.body
        ]

    def create(self, key, value, abstract):
        """ Create and index a new node or relationship using the abstract
        provided.
        """
        batch = WriteBatch(self._graph_db)
        if self._content_type is Node:
            batch.create_node(abstract)
            batch.add_indexed_node(self, key, value, 0)
        elif self._content_type is Relationship:
            if len(abstract) == 3:
                (start_node, type_, end_node), properties = abstract, None
            elif len(abstract) == 4:
                start_node, type_, end_node, properties = abstract
            else:
                raise ValueError(abstract)
            if not isinstance(start_node, Node):
                raise TypeError(start_node)
            if not isinstance(end_node, Node):
                raise TypeError(end_node)
            batch.create_relationship(start_node, type_, end_node, properties)
            batch.add_indexed_relationship(self, key, value, 0)
        else:
            raise TypeError(self._content_type)
        entity, index_entry = batch.submit()
        return entity

    def _create_unique(self, key, value, abstract):
        """ Internal method to support `get_or_create` and `create_if_none`.
        """
        if self._content_type is Node:
            body = {
                "key": key,
                "value": value,
                "properties": abstract
            }
        elif self._content_type is Relationship:
            body = {
                "key": key,
                "value": value,
                "start": str(abstract[0].__uri__),
                "type": abstract[1],
                "end": str(abstract[2].__uri__),
                "properties": abstract[3] if len(abstract) > 3 else None
            }
        else:
            raise TypeError(self._content_type)
        return self._send(rest.Request(
            self._graph_db, "POST", str(self.__uri__) + "?unique", body)
        )

    def get_or_create(self, key, value, abstract):
        """ Fetch a single entity from the index which is associated with the
        `key`:`value` pair supplied, creating a new entity with the supplied
        details if none exists::

            # obtain a reference to the "Contacts" node index and
            # ensure that Alice exists therein
            contacts = graph_db.get_or_create_index(neo4j.Node, "Contacts")
            alice = contacts.get_or_create("name", "SMITH, Alice", {
                "given_name": "Alice Jane", "family_name": "Smith",
                "phone": "01234 567 890", "mobile": "07890 123 456"
            })

            # obtain a reference to the "Friendships" relationship index and
            # ensure that Alice and Bob's friendship is registered (`alice`
            # and `bob` refer to existing nodes)
            friendships = graph_db.get_or_create_index(neo4j.Relationship, "Friendships")
            alice_and_bob = friendships.get_or_create(
                "friends", "Alice & Bob", (alice, "KNOWS", bob)
            )

        ..
        """
        rs = self._create_unique(key, value, abstract)
        return self._content_type(rs.body["self"])

    def create_if_none(self, key, value, abstract):
        """ Create a new entity with the specified details within the current
        index, under the `key`:`value` pair supplied, if no such entity already
        exists. If creation occurs, the new entity will be returned, otherwise
        :py:const:`None` will be returned::

            # obtain a reference to the "Contacts" node index and
            # create a node for Alice if one does not already exist
            contacts = graph_db.get_or_create_index(neo4j.Node, "Contacts")
            alice = contacts.create_if_none("name", "SMITH, Alice", {
                "given_name": "Alice Jane", "family_name": "Smith",
                "phone": "01234 567 890", "mobile": "07890 123 456"
            })

        ..
        """
        rs = self._create_unique(key, value, abstract)
        if rs.status == 201:
            return self._content_type(rs.body["self"])
        else:
            return None

    def remove(self, key=None, value=None, entity=None):
        """ Remove any entries from the index which match the parameters
        supplied. The allowed parameter combinations are:

        `key`, `value`, `entity`
            remove a specific entity indexed under a given key-value pair

        `key`, `value`
            remove all entities indexed under a given key-value pair

        `key`, `entity`
            remove a specific entity indexed against a given key but with
            any value

        `entity`
            remove all occurrences of a specific entity regardless of
            key and value

        """
        if key and value and entity:
            self._send(rest.Request(
                self._graph_db, "DELETE", "{0}/{1}/{2}/{3}".format(
                    self.__uri__,
                    quote(key, ""),
                    quote(value, ""),
                    entity._id,
                )
            ))
        elif key and value:
            entities = [
                item['indexed']
                for item in self._send(rest.Request(
                    self._graph_db, "GET", self._template_uri.format(
                        key=quote(key, ""),
                        value=quote(value, "")
                    )
                )).body
            ]
            batch = WriteBatch(self._graph_db)
            for entity in entities:
                batch._append(rest.Request(
                    self._graph_db, "DELETE",
                    rest.URI(entity).reference,
                ))
            batch._submit()
        elif key and entity:
            self._send(rest.Request(
                self._graph_db, "DELETE", "{0}/{1}/{2}".format(
                    self.__uri__,
                    quote(key, ""),
                    entity._id,
                )
            ))
        elif entity:
            self._send(rest.Request(
                self._graph_db, "DELETE", "{0}/{1}".format(
                    self.__uri__,
                    entity._id,
                )
            ))
        else:
            raise TypeError("Illegal parameter combination for index removal")

    def query(self, query):
        """ Query the index according to the supplied query criteria, returning
        a list of matched entities::

            # obtain a reference to the "People" node index and
            # get all nodes where `family_name` equals "Smith"
            people = graph_db.get_or_create_index(neo4j.Node, "People")
            s_people = people.query("family_name:S*")

        The query syntax used should be appropriate for the configuration of
        the index being queried. For indexes with default configuration, this
        should be `Apache Lucene query syntax <http://lucene.apache.org/core/old_versioned_docs/versions/3_5_0/queryparsersyntax.html>`_.
        """
        return [
            self._content_type(item['self'])
            for item in self._send(rest.Request(self._graph_db, "GET", "{0}?query={1}".format(
                self.__uri__, quote(query, "")
            ))).body
        ]


def _cast(obj, cls=(Node, Relationship), abstract=None):
    if obj is None:
        return None
    elif isinstance(obj, Node) or isinstance(obj, dict):
        entity = _node(obj)
    elif isinstance(obj, Relationship) or isinstance(obj, tuple):
        entity = _rel(obj)
    else:
        raise TypeError(obj)
    if not isinstance(entity, cls):
        raise TypeError(obj)
    if abstract is not None and bool(abstract) != bool(entity.is_abstract):
        raise TypeError(obj)
    return entity


class _Batch(Resource):

    class Request(_Request):

        def to_dict(self, id_):
            return {
                "id": id_,
                "method": self.method,
                "to": str(self.__uri__),
                "body": self._body,
            }

    class Response(object):

        def __init__(self, result):
            self.id_ = result.get("id")
            self.__uri__ = result.get("from")
            self.body = result.get("body")
            self.status_code = result.get("status", 200)
            self.location = URI(result.get("location"))

    @staticmethod
    def _uri_for(entity, cls=(Node, Relationship), abstract=None):
        if isinstance(entity, int):
            return "{{{0}}}".format(entity)
        else:
            return _cast(entity, cls=cls, abstract=abstract).__relative_uri__

    def __init__(self, graph_db):
        Resource.__init__(self, graph_db._subresource("batch").__uri__)
        self.clear()

    def __len__(self):
        return len(self.requests)

    def __nonzero__(self):
        return bool(self.requests)

    def _append(self, request, **kwargs):
        self.requests.append(request)

    def _append_get(self, uri, **kwargs):
        self._append(_Batch.Request("GET", uri), **kwargs)

    def _append_put(self, uri, body=None, **kwargs):
        self._append(_Batch.Request("PUT", uri, body), **kwargs)

    def _append_post(self, uri, body=None, **kwargs):
        self._append(_Batch.Request("POST", uri, body), **kwargs)

    def _append_delete(self, uri, **kwargs):
        self._append(_Batch.Request("DELETE", uri), **kwargs)

    def _append_cypher(self, query, **params):
        if params:
            body = {"query": str(query), "params": dict(params)}
        else:
            body = {"query": str(query)}
        self._append_post(self.cypher.__relative_uri__, body)

    @property
    def _body(self):
        return [
            request.to_dict(id_)
            for id_, request in enumerate(self.requests)
        ]

    def clear(self):
        """ Clear all requests from this batch.
        """
        self.requests = []

    def _submit(self):
        """ Submit the current batch but do not parse the results. This is for
        internal use where the results are discarded.
        """
        try:
            results = self._post(self._body)
        except (ClientError, ServerError) as e:
            if e.exception:
                # A CustomBatchError is a dynamically created subclass of
                # BatchError with the same name as the underlying server
                # exception
                CustomBatchError = type(e.exception, (BatchError,), {})
                raise CustomBatchError(e)
            else:
                raise BatchError(e)
        else:
            self.clear()
            return results

    def submit(self):
        """ Submit the current batch of requests, iterating through the
        results.
        """
        for row_id, result in groupby(self._submit(), lambda _: _[0][0]):
            response = _Batch.Response(assembled(result, key_offset=1))
            body = response.body
            if isinstance(body, dict) and has_all(body, Cypher.ResultSet.signature):
                yield Cypher.ResultSet._hydrated(response.body)
            else:
                yield _hydrated(response.body)


class ReadBatch(_Batch):

    def __init__(self, graph_db):
        _Batch.__init__(self, graph_db)

    def _index(self, content_type, index):
        if isinstance(index, Index):
            if content_type != index._content_type:
                raise TypeError("Index is not for {0}s".format(content_type))
            return index
        else:
            return self.graph_db.get_or_create_index(content_type, str(index))

    def get_properties(self, entity):
        """ Fetch properties for the given entity.

        :param entity: concrete entity from which to fetch properties
        """
        entity = _cast(entity, abstract=False)
        self._append_get(entity._properties_resource)
        #self._get(rest.URI(entity.__metadata__["properties"]).reference)

    def get_indexed_nodes(self, index, key, value):
        """ Fetch all nodes indexed under the given key-value pair.

        :param index: index name or instance
        :param key: key under which nodes are indexed
        :param value: value under which nodes are indexed
        """
        index = self._index(Node, index)
        self._get(index._template_uri.format(
            key=quote(key, ""),
            value=quote(value, "")
        ))


class WriteBatch(_Batch):

    def __init__(self, graph_db):
        _Batch.__init__(self, graph_db)

    def create(self, abstract):
        """ Create a node or relationship based on the abstract entity
        provided. For example:

        ::

            batch = WriteBatch(graph_db)
            batch.create(node(name="Alice"))
            batch.create(node(name="Bob"))
            batch.create(rel(0, "KNOWS", 1))
            results = batch.submit()

        :param abstract: abstract node or relationship
        """
        entity = _cast(abstract, abstract=True)
        if isinstance(entity, Node):
            uri = self.graph_db._node_resource.__relative_uri__
            body = compact(entity._properties)
        elif isinstance(entity, Relationship):
            uri = URI.join(_Batch._uri_for(entity.start_node, abstract=False),
                           "relationships")
            body = {
                "type": entity._type,
                "to": str(_Batch._uri_for(entity.end_node, abstract=False))
            }
            if entity._properties:
                body["data"] = compact(entity._properties)
        else:
            raise TypeError(entity)
        self._append_post(uri, body)

    def get_or_create(self, rel_abstract):
        """ Use the abstract supplied to create a new relationship if one does
        not already exist.

        :param rel_abstract: relationship abstract to be fetched or created
        """
        rel = _cast(rel_abstract, cls=Relationship, abstract=True)
        if not (isinstance(rel._start_node, Node) or rel._start_node is None):
            raise TypeError("Relationship start node must be a "
                            "Node instance or None")
        if not (isinstance(rel._end_node, Node) or rel._end_node is None):
            raise TypeError("Relationship end node must be a "
                            "Node instance or None")
        if rel._start_node and rel._end_node:
            query = (
                "START a=node({A}), b=node({B}) "
                "CREATE UNIQUE (a)-[ab:`" + str(rel._type) + "` {P}]->(b) "
                "RETURN ab"
            )
        elif rel._start_node:
            query = (
                "START a=node({A}) "
                "CREATE UNIQUE (a)-[ab:`" + str(rel._type) + "` {P}]->() "
                "RETURN ab"
            )
        elif rel._end_node:
            query = (
                "START b=node({A}) "
                "CREATE UNIQUE ()-[ab:`" + str(rel._type) + "` {P}]->(b) "
                "RETURN ab"
            )
        else:
            raise ValueError("Either start node or end node must be "
                             "specified for a unique relationship")
        params = {"P": compact(rel._properties or {})}
        if rel._start_node:
            params["A"] = rel._start_node._id
        if rel._end_node:
            params["B"] = rel._end_node._id
        self._append_cypher(query, **params)

    def delete(self, entity):
        """ Delete the specified entity from the graph.

        :param entity: concrete node or relationship to be deleted
        """
        self._append_delete(_Batch._uri_for(entity, abstract=False))

    def set_property(self, entity, key, value):
        """ Set a single property on an entity.

        :param entity: concrete entity on which to set property
        :param key: property key
        :param value: property value
        """
        if value is None:
            self.delete_property(entity, key)
        else:
            self._append_put(URI.join(_Batch._uri_for(entity, abstract=False),
                                      "properties", key), value)

    def set_properties(self, entity, properties):
        """ Replace all properties on an entity.

        :param entity: concrete entity on which to set properties
        :param properties: dictionary of properties
        """
        self._append_put(URI.join(_Batch._uri_for(entity, abstract=False),
                                  "properties"), compact(properties))

    def delete_property(self, entity, key):
        """ Delete a single property from an entity.

        :param entity: concrete entity from which to delete property
        :param key: property key
        """
        self._append_delete(URI.join(_Batch._uri_for(entity, abstract=False),
                                     "properties", key))

    def delete_properties(self, entity):
        """ Delete all properties from an entity.

        :param entity: concrete entity from which to delete properties
        """
        self._append_delete(URI.join(_Batch._uri_for(entity, abstract=False),
                                     "properties"))

    def _node_uri(self, node):
        if isinstance(node, Node):
            return str(node.__uri__)
        else:
            return "{" + str(node) + "}"

    def _relationship_uri(self, relationship):
        if isinstance(relationship, Relationship):
            return str(relationship.__uri__)
        else:
            return "{" + str(relationship) + "}"

    def _index(self, content_type, index):
        if isinstance(index, Index):
            if content_type != index._content_type:
                raise TypeError("Index is not for {0}s".format(content_type))
            return index
        else:
            return self._graph_db.get_or_create_index(content_type, str(index))

    def _create_indexed_node(self, index, uri_suffix, key, value, properties):
        index_uri = self._index(Node, index).__uri__
        self._post(index_uri.reference + uri_suffix, body = {
            "key": key,
            "value": value,
            "properties": compact(properties or {})
        })

    def get_or_create_indexed_node(self, index, key, value, properties=None):
        """ Create and index a new node if one does not already exist,
            returning either the new node or the existing one.
        """
        if self._graph_db.neo4j_version >= (1, 9):
            self._create_indexed_node(index, "?uniqueness=get_or_create", key, value, compact(properties))
        else:
            self._create_indexed_node(index, "?unique", key, value, compact(properties))

    def create_indexed_node_or_fail(self, index, key, value, properties=None):
        """ Create and index a new node if one does not already exist,
            fail otherwise.
        """
        if self._graph_db.neo4j_version >= (1, 9):
            self._create_indexed_node(index, "?uniqueness=create_or_fail", key, value, compact(properties))
        else:
            raise NotImplementedError("Uniqueness mode `create_or_fail` "
                                      "requires version 1.9 or above")

    def _add_indexed_node(self, index, uri_suffix, key, value, node):
        index_uri = self._index(Node, index).__uri__
        self._post(index_uri.reference + uri_suffix, body = {
            "key": key,
            "value": value,
            "uri": self._node_uri(node)
        })

    def add_indexed_node(self, index, key, value, node):
        """ Add an existing node to the index specified.
        """
        self._add_indexed_node(index, "", key, value, node)

    def get_or_add_indexed_node(self, index, key, value, node):
        """ Add an existing node to the index specified if an entry does not
            already exist for the given key-value pair, returning either the
            added node or the one already in the index.
        """
        if self._graph_db.neo4j_version >= (1, 9):
            self._add_indexed_node(index, "?uniqueness=get_or_create", key, value, node)
        else:
            self._add_indexed_node(index, "?unique", key, value, node)

    def add_indexed_node_or_fail(self, index, key, value, node):
        """ Add an existing node to the index specified if an entry does not
            already exist for the given key-value pair, fail otherwise.
        """
        if self._graph_db.neo4j_version >= (1, 9):
            self._add_indexed_node(index, "?uniqueness=create_or_fail", key, value, node)
        else:
            raise NotImplementedError("Uniqueness mode `create_or_fail` "
                                      "requires version 1.9 or above")

    def remove_indexed_node(self, index, key=None, value=None, node=None):
        """Remove any entries from the index which pertain to the parameters
        supplied. The allowed parameter combinations are:

        `key`, `value`, `node`
            remove a specific node indexed under a given key-value pair

        `key`, `node`
            remove a specific node indexed against a given key but with
            any value

        `node`
            remove all occurrences of a specific node regardless of
            key and value

        """
        index_uri = self._index(Node, index).__uri__
        if key and value and node:
            self._delete("{0}/{1}/{2}/{3}".format(
                index_uri,
                quote(key, ""),
                quote(value, ""),
                node._id,
            ))
        elif key and node:
            self._delete("{0}/{1}/{2}".format(
                index_uri,
                quote(key, ""),
                node._id,
            ))
        elif node:
            self._delete("{0}/{1}".format(
                index_uri,
                node._id,
            ))
        else:
            raise TypeError("Illegal parameter combination for index removal")

    def _create_indexed_relationship(self, index, uri_suffix, key, value, start_node, type_, end_node, properties):
        index_uri = self._index(Relationship, index).__uri__
        self._post(index_uri.reference + uri_suffix, body = {
            "key": key,
            "value": value,
            "start": self._node_uri(start_node),
            "type": str(type_),
            "end": self._node_uri(end_node),
            "properties": properties or {}
        })

    def get_or_create_indexed_relationship(self, index, key, value, start_node, type_, end_node, properties=None):
        """ Create and index a new relationship if one does not already exist,
            returning either the new relationship or the existing one.
        """
        if self._graph_db.neo4j_version >= (1, 9):
            self._create_indexed_relationship(index, "?uniqueness=get_or_create", key, value, start_node, type_, end_node, properties)
        else:
            self._create_indexed_relationship(index, "?unique", key, value, start_node, type_, end_node, properties)

    def create_indexed_relationship_or_fail(self, index, key, value, start_node, type_, end_node, properties=None):
        """ Create and index a new relationship if one does not already exist,
            fail otherwise.
        """
        if self._graph_db.neo4j_version >= (1, 9):
            self._create_indexed_relationship(index, "?uniqueness=create_or_fail", key, value, start_node, type_, end_node, properties)
        else:
            raise NotImplementedError("Uniqueness mode `create_or_fail` "
                                      "requires version 1.9 or above")

    def _add_indexed_relationship(self, index, uri_suffix, key, value, relationship):
        index_uri = self._index(Relationship, index).__uri__
        self._post(index_uri.reference + uri_suffix, body = {
            "key": key,
            "value": value,
            "uri": self._relationship_uri(relationship)
        })

    def add_indexed_relationship(self, index, key, value, relationship):
        """ Add an existing relationship to the index specified.
        """
        self._add_indexed_relationship(index, "", key, value, relationship)

    def get_or_add_indexed_relationship(self, index, key, value, relationship):
        """ Add an existing relationship to the index specified if an entry does not
            already exist for the given key-value pair, returning either the
            added relationship or the one already in the index.
        """
        if self._graph_db.neo4j_version >= (1, 9):
            self._add_indexed_relationship(index, "?uniqueness=get_or_create", key, value, relationship)
        else:
            self._add_indexed_relationship(index, "?unique", key, value, relationship)

    def add_indexed_relationship_or_fail(self, index, key, value, relationship):
        """ Add an existing relationship to the index specified if an entry does not
            already exist for the given key-value pair, fail otherwise.
        """
        if self._graph_db.neo4j_version >= (1, 9):
            self._add_indexed_relationship(index, "?uniqueness=create_or_fail", key, value, relationship)
        else:
            raise NotImplementedError("Uniqueness mode `create_or_fail` "
                                      "requires version 1.9 or above")

    def remove_indexed_relationship(self, index, key=None, value=None, relationship=None):
        """Remove any entries from the index which pertain to the parameters
        supplied. The allowed parameter combinations are:

        `key`, `value`, `relationship`
            remove a specific relationship indexed under a given key-value pair

        `key`, `relationship`
            remove a specific relationship indexed against a given key but with
            any value

        `relationship`
            remove all occurrences of a specific relationship regardless of
            key and value

        """
        index_uri = self._index(Relationship, index).__uri__
        if key and value and relationship:
            self._delete("{0}/{1}/{2}/{3}".format(
                index_uri,
                quote(key, ""),
                quote(value, ""),
                relationship._id,
            ))
        elif key and relationship:
            self._delete("{0}/{1}/{2}".format(
                index_uri,
                quote(key, ""),
                relationship._id,
            ))
        elif relationship:
            self._delete("{0}/{1}".format(
                index_uri,
                relationship._id,
            ))
        else:
            raise TypeError("Illegal parameter combination for index removal")
