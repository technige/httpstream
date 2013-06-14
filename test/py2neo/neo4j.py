

from httpstream import Resource as _Resource, URI

from .mixins import Cacheable


DEFAULT_SCHEME = "http"
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 7474


class Resource(object):
    """ Basic RESTful web resource with JSON metadata. Wraps an
    `httpstream.Resource`.
    """

    class Metadata(object):

        def __init__(self, resource):
            self._metadata = dict(resource.get())

        def __getitem__(self, key):
            if not isinstance(key, tuple):
                key = (key,)
            return self._metadata.get(key)

        def __iter__(self):
            return iter(self._metadata.items())

    def __init__(self, uri):
        self._resource = _Resource(uri)
        self._metadata = None

    @property
    def __uri__(self):
        return self._resource.__uri__

    @property
    def __metadata__(self):
        if not self._metadata:
            self.refresh()
        return self._metadata

    @property
    def service_root(self):
        return ServiceRoot.get_instance(self._resource.__uri__.base)

    def refresh(self):
        """ Refresh resource metadata.
        """
        self._metadata = Resource.Metadata(self._resource)

    def _request(self, method, body=None, headers=None):
        return self._resource.request(method, body, headers)

    def _get(self, headers=None):
        return self._resource.get(headers)

    def _put(self, body=None, headers=None):
        return self._resource.put(body, headers)

    def _post(self, body=None, headers=None):
        return self._resource.post(body, headers)

    def _delete(self, headers=None):
        return self._resource.delete(headers)

    def _subresource(self, *parts):
        return Resource(URI.join(self.__uri__, *parts))


class ServiceRoot(Cacheable, Resource):
    """ Neo4j REST API service root resource.
    """

    def __init__(self, uri=None):
        if uri is None:
            uri = "http://localhost:7474"
        Resource.__init__(self, uri)

    @property
    def graph_db(self):
        return GraphDatabaseService.get_instance(self.__metadata__["data"])


class GraphDatabaseService(Cacheable, Resource):

    def __init__(self, uri=None):
        if uri is None:
            Resource.__init__(self, ServiceRoot().graph_db.__uri__)
        else:
            Resource.__init__(self, uri)

    @property
    def write_batch(self):
        return WriteBatch(self.__metadata__["batch"])

    @property
    def cypher(self):
        return Cypher.get_instance(self.__metadata__["cypher"])

    @property
    def neo4j_version(self):
        return self.__metadata__["neo4j_version"]

    @property
    def node(self):
        return NodeResource(self.__metadata__["node"])


class _Batch(Resource):

    def __init__(self, uri):
        Resource.__init__(self, uri)
        #if not isinstance(graph_db, GraphDatabaseService):
        #    raise TypeError(graph_db)
        #self._graph_db...
        #self._create_node_uri = rest.URI(self._graph_db.__metadata__["node"]).reference
        #self._cypher_uri = rest.URI(self._graph_db._cypher_uri).reference
        self.clear()

    def __len__(self):
        return len(self.requests)

    def __nonzero__(self):
        return bool(self.requests)

    def append(self, request):
        self.requests.append(request)

    def clear(self):
        """ Clear all requests from this batch.
        """
        self.requests = []


class WriteBatch(_Batch):

    def create_node(self):
        return self.service_root.graph_db


class NodeResource(Cacheable, Resource):

    def get(self, id_):
        return self._subresource(id_)._get()

    def create(self):
        return self._post()


class Cypher(Cacheable, Resource):

    class Value(object):

        def __init__(self):
            self._value = None

        def __repr__(self):
            return repr(self._value)

        def put(self, key, value):
            self._value = value

    class Values(object):

        def __init__(self):
            self._values = []

        def __repr__(self):
            return repr(self._values)

        def put(self, column, key, value):
            while len(self._values) <= column:
                self._values.append(Cypher.Value())
            self._values[column].put(key, value)

    def execute(self, query):
        response = self._resource.post({"query": query})
        columns = Cypher.Values()
        row, values = None, Cypher.Values()
        for key, value in response:
            section = key[0]
            if section == "columns":
                columns.put(key[1], None, value)
            elif section == "data":
                if columns:
                    yield columns
                    columns = None
                if key[1] != row:
                    if row is not None:
                        yield values
                        values = Cypher.Values()
                    row = key[1]
                print(key, value)
                values.put(key[2], key[3:], value)
        if row is not None:
            yield values


if __name__ == "__main__":
    graph_db = GraphDatabaseService("http://localhost:7474/db/data/")
    print(graph_db.neo4j_version)
    for foo in graph_db.cypher.execute("START n=node(1000,1001) RETURN id(n),n"):
        print(foo)
