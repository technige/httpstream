#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013, Nigel Small
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


try:
    from http.client import HTTPConnection, HTTPSConnection, responses, HTTPException, CannotSendRequest, BadStatusLine
except ImportError:
    from httplib import HTTPConnection, HTTPSConnection, responses, HTTPException, CannotSendRequest, BadStatusLine
import json
from threading import local

from .packages.jsonstream import JSONStream

from .uri import URI


DEFAULT_CHARSET = "ISO-8859-1"
DEFAULT_CHUNK_SIZE = 4096
HTTP_CLASSES = {
    "http": HTTPConnection,
    "https": HTTPSConnection,
}


class ConnectionPuddle(local):

    def __init__(self, scheme, hostname, port):
        local.__init__(self)
        self._hostname = hostname
        self._port = port
        self._scheme = scheme
        self._active = []
        self._passive = []

    @property
    def hostname(self):
        return self._hostname

    @property
    def port(self):
        return self._port

    @property
    def scheme(self):
        return self._scheme

    def __repr__(self):
        return "({0}://{1}:{2} active={3} passive={4})".format(self.scheme, self.hostname, self.port, len(self._active), len(self._passive))

    def __hash__(self):
        return hash((self.scheme, self.hostname, self.port))

    def __len__(self):
        return len(self._active) + len(self._passive)

    def acquire(self):
        if self._passive:
            connection = self._passive.pop()
        else:
            connection = HTTP_CLASSES[self.scheme](self.hostname, self.port)
        self._active.append(connection)
        return connection

    def release(self, connection):
        try:
            self._active.remove(connection)
        except ValueError:
            pass
        if len(self._passive) < 2:
            self._passive.append(connection)
        else:
            connection.close()


class ConnectionPool(object):

    _puddles = {}

    @classmethod
    def _get_puddle(cls, scheme, hostname, port):
        key = (scheme, hostname, port)
        if key not in cls._puddles:
            cls._puddles[key] = ConnectionPuddle(scheme, hostname, port)
        return cls._puddles[key]

    @classmethod
    def acquire(cls, scheme, hostname, port):
        puddle = cls._get_puddle(scheme, hostname, port)
        return puddle.acquire()

    @classmethod
    def release(cls, connection):
        if isinstance(connection, HTTPSConnection):
            schema = "https"
        elif isinstance(connection, HTTPConnection):
            schema = "http"
        else:
            raise TypeError("Unknown connection type " + repr(connection.__class__))
        puddle = cls._get_puddle(schema, connection.host, connection.port)
        puddle.release(connection)


class RequestResponse(object):

    def __init__(self, method, uri, body=None, headers=None, **kwargs):
        # TODO: tidy this up a bit!
        self._method = method
        self.__uri__ = URI(uri)
        self._headers = headers or {}
        if isinstance(body, dict):
            self._body = json.dumps(body, separators=(",", ":"))
            self._headers.setdefault("Content-Type", "application/json")
        else:
            self._body = body
        scheme, port = self.__uri__.scheme, self.__uri__.port
        if not port:
            port = 443 if scheme == "https" else 80
        try:
            self._http = ConnectionPool.acquire(scheme, self.__uri__.hostname,
                                                port)
        except KeyError:
            raise ValueError("Unsupported URI scheme {0}".format(
                repr(self.__uri__.scheme)))
        try:
            self._http.request(method, self.__uri__.path, self._body, headers or {})
            self._response = self._http.getresponse()
        except BadStatusLine as err:
            if err.line == repr(""):
                self._http.close()
                self._http.connect()
                self._http.request(method, self.__uri__.path, self._body, headers or {})
                self._response = self._http.getresponse()
        self._kwargs = kwargs

    def __getitem__(self, key):
        if not self._response:
            return None
        return self._response.getheader(key)

    def _decode(self, data):
        return data.decode(self.charset)

    @property
    def uri(self):
        return self.__uri__

    @property
    def status_code(self):
        return self._response.status

    @property
    def reason(self):
        return responses[self._response.status]

    @property
    def headers(self):
        return self._response.getheaders()

    @property
    def content_type(self):
        try:
            content_type = [
                _.strip()
                for _ in self["Content-Type"].split(";")
            ]
        except AttributeError:
            return None
        return content_type[0].partition("/")[0::2]

    @property
    def charset(self):
        try:
            content_type = dict(
                _.strip().partition("=")[0::2]
                for _ in self["Content-Type"].split(";")
            )
        except AttributeError:
            return DEFAULT_CHARSET
        return content_type.get("charset", DEFAULT_CHARSET)

    def __iter__(self):
        def response_iterator(chunk_size):
            if chunk_size:
                pending = []
                data = True
                while data:
                    data = self._response.read(chunk_size)
                    pending.append(data)
                    decoded = None
                    while data and not decoded:
                        try:
                            decoded = self._decode("".join(pending))
                            pending = []
                            yield decoded
                        except UnicodeDecodeError:
                            data = self._response.read(1)
                            pending.append(data)
            else:
                yield self._decode(self._response.read())
            if self._http:
                ConnectionPool.release(self._http)
                self._http = None
        iterator = response_iterator(self._kwargs.get("chunk_size"))
        if self.content_type == ("application", "json"):
            return iter(JSONStream(iterator))
        else:
            return iterator


class Resource(object):

    def __init__(self, uri):
        self.__uri__ = URI(uri)

    def get(self, headers=None, **kwargs):
        return RequestResponse("GET", self.__uri__, headers, **kwargs)

    def put(self, body, headers=None, **kwargs):
        return RequestResponse("PUT", self.__uri__, body, headers, **kwargs)

    def post(self, body, headers=None, **kwargs):
        return RequestResponse("POST", self.__uri__, body, headers, **kwargs)

    def delete(self, headers=None, **kwargs):
        return RequestResponse("DELETE", self.__uri__, headers, **kwargs)
