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
    from http.client import (BadStatusLine, CannotSendRequest, HTTPConnection,
                             HTTPSConnection, HTTPException, responses)
except ImportError:
    from httplib import (BadStatusLine, CannotSendRequest, HTTPConnection,
                         HTTPSConnection, HTTPException, responses)
import json
import logging
from socket import error, gaierror, herror, timeout
from threading import local
import sys

from jsonstream import JSONStream

from . import __package__, __version__
from .exceptions import NetworkAddressError, RedirectionError, SocketError
from .numbers import *
from .uri import URI


default_charset = "ISO-8859-1"
default_chunk_size = 4096
default_max_redirects = 5

log = logging.getLogger(__name__)

redirects = {}

user_agent = "{0}/{1} ({2}; python/{3})".format(__package__, __version__,
                                                sys.platform,
                                                sys.version.partition(" ")[0])


class ConnectionPuddle(local):
    """ A collection of HTTP/HTTPS connections to a single network location
    (i.e. host:port). Connections may be acquired and will be created if
    necessary; after use, these must be released.
    """

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
    """ A collection of :py:class:`ConnectionPuddle` objects for various
    network locations.
    """

    _puddles = {}

    @classmethod
    def _get_puddle(cls, scheme, netloc):
        if ":" in netloc:
            key = (scheme, netloc)
        elif scheme == "https":
            key = (scheme, netloc + ":" + str(HTTPS_PORT))
        elif scheme == "http":
            key = (scheme, netloc + ":" + str(HTTP_PORT))
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
        if not uri:
            raise ValueError("No URI specified for request")
        self.method = method
        self.uri = uri
        self._headers = dict(headers or {})
        self._headers.setdefault("User-Agent", user_agent)
        self.body = body

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
        if isinstance(self._body, (dict, list, tuple)):
            return json.dumps(self._body, separators=(",", ":"))
        else:
            return self._body

    @body.setter
    def body(self, value):
        self._body = value

    @property
    def headers(self):
        if isinstance(self._body, (dict, list, tuple)):
            self._headers.setdefault("Content-Type", "application/json")
        return self._headers

    def _submit(self, method, uri, body, headers):
        uri = URI(uri)
        headers["Host"] = uri.netloc
        try:
            http = ConnectionPool.acquire(uri.scheme, uri.netloc)
        except KeyError:
            raise ValueError("Unsupported URI scheme " + repr(uri.scheme))

        def send(reconnect=None):
            if reconnect:
                log.warn("Reconnecting ({0})".format(reconnect))
                http.close()
                http.connect()
            log.info(">>> {0} <{1}> [{2}]".format(method, uri, len(body or "")))
            for key, value in headers.items():
                log.debug(">>> {0}: {1}".format(key, value))
            http.request(method, uri.reference, body, headers)
            return http.getresponse()

        try:
            try:
                response = send()
            except BadStatusLine as err:
                if err.line == repr(""):
                    response = send("bad status line")
                else:
                    raise
            except timeout:
                response = send("timeout")
        except (gaierror, herror) as err:
            raise NetworkAddressError(err.args[1], netloc=uri.netloc)
        except error as err:
            raise SocketError(err.args[0], netloc=uri.netloc)
        else:
            return http, response

    def submit(self, **kwargs):
        follow = kwargs.get("follow", default_max_redirects)
        fields = kwargs.get("fields")
        uri = URI(self.uri)
        if fields:
            try:
                uri = uri.format(**dict(fields))
            except TypeError:
                raise TypeError("Mapping required for field substitution")
        while uri:
            http, rs = self._submit(self.method, uri, self.body, self.headers)
            status_class = rs.status // 100
            if rs.getheader("Transfer-Encoding") == "chunked":
                content_length = "chunked"
            else:
                content_length = rs.getheader("Content-Length")
            log.info("<<< {0} {1} [{2}]".format(rs.status, responses[rs.status],
                                                content_length))
            for key, value in rs.getheaders():
                log.debug("<<< {0}: {1}".format(key, value))
            if status_class == 3:
                if follow:
                    location = rs.getheader("Location")
                    if location == uri:
                        raise RedirectionError("Circular redirection")
                    if rs.status in (MOVED_PERMANENTLY, PERMANENT_REDIRECT):
                        redirects[uri] = location
                    uri = location
                    follow -= 1
                else:
                    uri = None
                rs.read()
            elif status_class == 4:
                raise ClientError(http, uri, self, rs, **kwargs)
            elif status_class == 5:
                raise ServerError(http, uri, self, rs, **kwargs)
            else:
                return Response(http, uri, self, rs, **kwargs)
        raise RedirectionError("Too many redirects")


class Response(object):

    def __init__(self, http, uri, request, response, **kwargs):
        self._http = http
        self._uri = URI(uri)
        self._request = request
        self._response = response
        try:
            self._reason = kwargs.pop("reason")
        except KeyError:
            self._reason = None
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
    def __uri__(self):
        return self._uri

    @property
    def uri(self):
        return self._uri

    @property
    def request(self):
        return self._request

    @property
    def status_code(self):
        return self._response.status

    @property
    def reason(self):
        if self._reason:
            return self._reason
        else:
            return responses[self.status_code]

    @property
    def headers(self):
        return self._response.getheaders()

    @property
    def content_type(self):
        try:
            content_type = [
                _.strip()
                for _ in self._response.getheader("Content-Type").split(";")
            ]
        except AttributeError:
            return None
        return content_type[0]

    @property
    def charset(self):
        try:
            content_type = dict(
                _.strip().partition("=")[0::2]
                for _ in self._response.getheader("Content-Type").split(";")
            )
        except AttributeError:
            return default_charset
        return content_type.get("charset", default_charset)

    @property
    def is_json(self):
        return self.content_type in ("application/json",
                                     "application/x-javascript")

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
        if self.status_code == NO_CONTENT:
            return iter([])
        elif self.is_json:
            return iter(JSONStream(iterator))
        else:
            return iterator


class ClientError(Exception, Response):

    def __init__(self, http, uri, request, response, **kwargs):
        assert response.status // 100 == 4
        Response.__init__(self, http, uri, request, response, **kwargs)
        Exception.__init__(self, self.reason)


class ServerError(Exception, Response):

    def __init__(self, http, uri, request, response, **kwargs):
        assert response.status // 100 == 5
        Response.__init__(self, http, uri, request, response, **kwargs)
        Exception.__init__(self, self.reason)



class Resource(object):

    def __init__(self, uri, headers=None):
        if uri:
            self._uri = str(uri)
        else:
            self._uri = None
        if headers:
            self._headers = dict(headers)
        else:
            self._headers = {}

    def __repr__(self):
        """ Return a valid Python representation of this object.
        """
        return "{0}({1})".format(self.__class__.__name__, repr(self.__uri__))

    def __eq__(self, other):
        """ Determine equality of two objects based on URI.
        """
        return self.__uri__ == other.__uri__

    def __ne__(self, other):
        """ Determine inequality of two objects based on URI.
        """
        return self.__uri__ != other.__uri__

    @property
    def __uri__(self):
        if self._uri:
            return URI(redirects.get(self._uri, self._uri))
        else:
            return None

    def request(self, method, body=None, headers=None):
        request_headers = dict(self._headers)
        if headers:
            request_headers.update(headers)
        return Request(method, self.__uri__, body, request_headers)

    def get(self, headers=None, **kwargs):
        return self.request("GET", None, headers).submit(**kwargs)

    def put(self, body=None, headers=None, **kwargs):
        return self.request("PUT", body, headers).submit(**kwargs)

    def post(self, body=None, headers=None, **kwargs):
        return self.request("POST", body, headers).submit(**kwargs)

    def delete(self, headers=None, **kwargs):
        return self.request("DELETE", None, headers).submit(**kwargs)
