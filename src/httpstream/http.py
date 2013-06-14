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

from jsonstream import JSONStream

from .exceptions import TooManyRedirects
from .uri import URI


default_charset = "ISO-8859-1"
default_chunk_size = 4096
redirects = {}


class ConnectionPuddle(local):

    _http_classes = {
        "http": HTTPConnection,
        "https": HTTPSConnection,
    }

    def __init__(self, scheme, netloc):
        local.__init__(self)
        self._scheme = scheme
        self._netloc = netloc
        self._active = []
        self._passive = []

    @property
    def netloc(self):
        return self._netloc

    @property
    def scheme(self):
        return self._scheme

    def __repr__(self):
        return "({0}://{1} active={2} passive={3})".format(
            self.scheme, self.netloc, len(self._active), len(self._passive))

    def __hash__(self):
        return hash((self.scheme, self.netloc))

    def __len__(self):
        return len(self._active) + len(self._passive)

    def acquire(self):
        if self._passive:
            connection = self._passive.pop()
        else:
            connection = self._http_classes[self.scheme](self.netloc)
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
    def _get_puddle(cls, scheme, netloc):
        if ":" in netloc:
            key = (scheme, netloc)
        elif scheme == "https":
            key = (scheme, netloc + ":443")
        elif scheme == "http":
            key = (scheme, netloc + ":80")
        else:
            raise ValueError("Unknown scheme " + repr(scheme))
        if key not in cls._puddles:
            cls._puddles[key] = ConnectionPuddle(scheme, netloc)
        return cls._puddles[key]

    @classmethod
    def acquire(cls, scheme, netloc):
        puddle = cls._get_puddle(scheme, netloc)
        return puddle.acquire()

    @classmethod
    def release(cls, connection):
        if isinstance(connection, HTTPSConnection):
            schema = "https"
        elif isinstance(connection, HTTPConnection):
            schema = "http"
        else:
            raise TypeError("Unknown connection type " + repr(connection.__class__))
        puddle = cls._get_puddle(schema, "{0}:{1}".format(
            connection.host, connection.port))
        puddle.release(connection)


class Request(object):

    def __init__(self, method, uri, body=None, headers=None):
        self.method = method
        self._uri = uri
        self._body = body
        self._headers = dict(headers or {})
        self._headers.setdefault("Host", self.uri.netloc)

    @property
    def __uri__(self):
        return self.uri

    @property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, value):
        self._uri = URI(value)

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, value):
        if isinstance(value, dict):
            self._body = json.dumps(value, separators=(",", ":"))
            self._headers.setdefault("Content-Type", "application/json")
        else:
            self._body = value

    @property
    def headers(self):
        return self._headers

    def _submit(self, method, uri, body, headers):
        uri = URI(uri)
        try:
            http = ConnectionPool.acquire(uri.scheme, uri.netloc)
        except KeyError:
            raise ValueError("Unsupported URI scheme {0}".format(
                repr(uri.scheme)))
        try:
            http.request(method, uri.reference, body, headers)
            response = http.getresponse()
        except BadStatusLine as err:
            if err.line == repr(""):
                http.close()
                http.connect()
                http.request(method, uri.reference, body, headers)
                response = http.getresponse()
            else:
                raise err
        return http, response

    def submit(self, **kwargs):
        follow = kwargs.get("follow", 5)
        uri = self.uri
        while uri:
            http, rs = self._submit(self.method, uri, self.body, self.headers)
            if rs.status // 100 == 3:
                if follow:
                    location = rs.getheader("Location")
                    if rs.status in (301, 308):
                        # Moved Permanently, Permanent Redirect
                        redirects[uri] = location
                    uri = location
                    follow -= 1
                else:
                    uri = None
            else:
                return Response(http, self, rs, **kwargs)
        raise TooManyRedirects()


class Response(object):

    def __init__(self, http, request, response, **kwargs):
        self._http = http
        self._request = request
        self._response = response
        self._kwargs = kwargs

    def __del__(self):
        self._release()

    def __repr__(self):
        return "{0} {1}".format(self.status_code, self.reason)

    def __getitem__(self, key):
        if not self._response:
            return None
        return self._response.getheader(key)

    def _decode(self, data):
        return data.decode(self.charset)

    def _release(self):
        if self._http:
            try:
                self._response.read()
            except HTTPException:
                pass
            ConnectionPool.release(self._http)
            self._http = None

    @property
    def request(self):
        return self._request

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
        return content_type[0]

    @property
    def charset(self):
        try:
            content_type = dict(
                _.strip().partition("=")[0::2]
                for _ in self["Content-Type"].split(";")
            )
        except AttributeError:
            return default_charset
        return content_type.get("charset", default_charset)

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
            self._release()
        iterator = response_iterator(self._kwargs.get("chunk_size"))
        if self.content_type in ("application/json", "application/x-javascript"):
            return iter(JSONStream(iterator))
        else:
            return iterator


class Resource(object):

    def __init__(self, uri):
        self._uri = str(uri)

    @property
    def __uri__(self):
        return URI(redirects.get(self._uri, self._uri))

    def request(self, method, body=None, headers=None):
        return Request(method, self.__uri__, body, headers)

    def get(self, headers=None, **kwargs):
        return self.request("GET", None, headers).submit(**kwargs)

    def put(self, body=None, headers=None, **kwargs):
        return self.request("PUT", body, headers).submit(**kwargs)

    def post(self, body=None, headers=None, **kwargs):
        return self.request("POST", body, headers).submit(**kwargs)

    def delete(self, headers=None, **kwargs):
        return self.request("DELETE", None, headers).submit(**kwargs)
