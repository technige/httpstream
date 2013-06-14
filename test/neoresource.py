

from httpstream import Resource


class Metadata(object):

    def __init__(self, resource):
        self._resource = resource
        self._metadata = None

    @property
    def resource(self):
        return self._resource

    def refresh(self):
        self._metadata = dict(self._resource.get())

    def __getitem__(self, key):
        if not self._metadata:
            self.refresh()
        if not isinstance(key, tuple):
            key = (key,)
        return self._metadata.get(key)

    def __iter__(self):
        return iter(self._metadata)


DEFAULT_SCHEME = "http"
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 7474


class NeoResource(object):
    """ Basic RESTful web resource with JSON metadata.
    """

    def __init__(self, uri):
        self._resource = Resource(uri)
        self.__metadata__ = Metadata(self._resource)

    @property
    def __uri__(self):
        return self._resource.__uri__

    @property
    def service_root(self):
        return ServiceRoot.get_instance(self._resource.__uri__.root)


class CacheableNeoResource(NeoResource):
    """ Resource with cached instances.
    """

    _instances = {}

    @classmethod
    def get_instance(cls, uri):
        if uri not in cls._instances:
            cls._instances[uri] = cls(uri)
        return cls._instances[uri]


class ServiceRoot(CacheableNeoResource):
    """ Neo4j REST API service root resource.
    """

    def __init__(self, uri=None):
        if uri is None:
            uri = "http://localhost:7474/"
        CacheableNeoResource.__init__(self, uri)

    @property
    def graph_db(self):
        return GraphDatabaseService.get_instance(self.__metadata__["data"])


class GraphDatabaseService(CacheableNeoResource):

    def __init__(self, uri=None):
        if uri is None:
            CacheableNeoResource.__init__(self, ServiceRoot().graph_db.__uri__)
        else:
            CacheableNeoResource.__init__(self, uri)

    @property
    def cypher(self):
        return Cypher.get_instance(self.__metadata__["cypher"])

    @property
    def neo4j_version(self):
        return self.__metadata__["neo4j_version"]


class Cypher(CacheableNeoResource):

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
