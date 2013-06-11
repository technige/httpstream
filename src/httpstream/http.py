
try:
    from http.client import HTTPConnection, HTTPSConnection, responses
except ImportError:
    from httplib import HTTPConnection, HTTPSConnection, responses
import json
from threading import local

from .packages.jsonstream import JSONStream

from .uri import URI


DEFAULT_CHUNK_SIZE = 4096


class Connection(object):

    _ctor = {
        "http": HTTPConnection,
        "https": HTTPSConnection,
    }

    def __init__(self, hostname, port=None, scheme=None):
        if not scheme:
            scheme = "https" if port == 443 else "http"
        if not port:
            port = 443 if scheme == "https" else 80
        try:
            self._http = self._ctor[scheme](hostname, port)
        except KeyError:
            raise ValueError("Unsupported URI scheme {0}".format(repr(scheme)))
        self._response = None

    def connect(self):
        self._http.connect()

    def close(self):
        self._http.close()

    @property
    def status_code(self):
        if self._response:
            return self._response.status
        else:
            return None

    @property
    def reason(self):
        if self._response:
            return responses[self._response.status]
        else:
            return None

    def flush(self):
        if self._response:
            self._response.read()
        self._response = None

    def request(self, method, path, body=None, headers=None):
        self.flush()
        self._http.request(method, path, body, headers or {})
        self._response = self._http.getresponse()

    def response(self, chunk_size=None):
        chunk_size = chunk_size or DEFAULT_CHUNK_SIZE
        pending = []
        data = True
        while data:
            data = self._response.read(chunk_size)
            pending.append(data)
            decoded = None
            while data and not decoded:
                try:
                    decoded = ("".join(pending)).decode("utf-8")
                    pending = []
                    yield decoded
                except UnicodeDecodeError:
                    data = self._response.read(1)
                    pending.append(data)


class ConnectionPile(object):

    constructors = {
        "http": HTTPConnection,
        "https": HTTPSConnection,
    }

    def __init__(self, scheme, hostname, port):
        if scheme not in self.constructors:
            raise ValueError("Unsupported URI scheme {0}".format(repr(scheme)))
        self._scheme = scheme
        self._hostname = hostname
        self._port = port
        self._active = set()
        self._passive = set()

    def __len__(self):
        return len(self._active) + len(self._passive)

    def _new_connection(self):
        return self.constructors[self._scheme](self._hostname, self._port)

    def acquire(self):
        if not self._passive:
            self._passive.add(self._new_connection())
        connection = self._passive.pop()
        self._active.add(connection)
        return connection


class ConnectionPool(local):

    def __init__(self):
        local.__init__(self)
        self._connections = {}

    def acquire(self, scheme, hostname, port):
        key = (scheme, hostname, port)
        if key not in self._connections:
            if scheme == "http":
                self._connections[key] = [HTTPConnection(hostname, port)]
            elif scheme == "https":
                self._connections[key] = [HTTPSConnection(hostname, port)]
            else:
                raise ValueError("Unsupported URI scheme {0}".format(
                    repr(scheme)))
        return self._connections[key]

    def release(self, scheme, hostname, port):
        key = (scheme, hostname, port)


pool = ConnectionPool()


class Request(object):

    def __init__(self, method, uri, body=None, headers=None):
        self.method = str(method)
        self.uri = uri
        self.body = body
        self.headers = headers or {}
        self.headers.setdefault("Accept", "application/json")
        self.headers.setdefault("Content-Type", "application/json")
        self.headers.setdefault("X-Stream", "true")

    def stream(self, chunk_size=None):
        uri = URI(self.uri)
        http = pool.acquire(uri.scheme, uri.hostname, uri.port)
        http.request(self.method, uri.path,
                     json.dumps(self.body, separators=(",", ":")),
                     self.headers)
        return ResponseStream(self, http.getresponse(), chunk_size)


class ResponseStream(object):

    def __init__(self, request, response, chunk_size=None):
        self.request = request
        self.response = response
        self.chunk_size = chunk_size or DEFAULT_CHUNK_SIZE

    @property
    def status_code(self):
        return self.response.status

    @property
    def reason(self):
        return responses[self.response.status]

    def __repr__(self):
        return "{0} {1}".format(self.status_code, self.reason)

    def _chunks(self):
        pending = []
        data = True
        while data:
            data = self.response.read(self.chunk_size)
            pending.append(data)
            decoded = None
            while data and not decoded:
                try:
                    decoded = ("".join(pending)).decode("utf-8")
                    pending = []
                    yield decoded
                except UnicodeDecodeError:
                    data = self.response.read(1)
                    pending.append(data)

    def __iter__(self):
        return iter(JSONStream(self._chunks()))
