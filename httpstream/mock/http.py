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


from __future__ import unicode_literals

try:
    import http.client as httplib
except ImportError:
    import httplib
import json

from urimagic import URI

from ..http import connection_classes


__all__ = ["MockConnection", "MockRequest", "MockResponse"]

DEFAULT_ENCODING = "UTF-8"


class MockHTTPConnection(object):
    """ Emulates the HTTPConnection object from the standard library.
    """

    # TODO: add logging

    default_port = httplib.HTTP_PORT
    scheme = "http"

    @staticmethod
    def responder(request):
        pass

    def __init__(self, host, port=None, strict=None, timeout=None,
                 source_address=None):
        self.host = host
        self.port = int(port or self.default_port)
        self.__uri = URI.build(scheme=self.scheme, host=host, port=port)
        self.__request = None

    def connect(self):
        pass

    def close(self):
        pass

    def request(self, method, url, body=None, headers=None):
        self.__uri = self.__uri.resolve(url)
        self.__request = MockRequest(method, self.__uri.string, body, headers)

    def getresponse(self):
        return self.__class__.responder(self.__request)


class MockHTTPSConnection(MockHTTPConnection):
    """ Emulates the HTTPSConnection object from the standard library.
    """

    default_port = httplib.HTTPS_PORT
    scheme = "https"


class MockRequest(object):
    """ Container for arguments passed to the HTTPConnection.request method.
    """

    def __init__(self, method, url, body=None, headers=None):
        self.method = method
        self.url = url
        if body:
            self.body = bytes(body.encode(DEFAULT_ENCODING))
        else:
            self.body = bytes()
        self.headers = headers  # todo

    @property
    def uri(self):
        return URI(self.url)


class MockResponse(object):
    """ Emulates the HTTPResponse object from the standard library, also
    allowing construction of emulated responses.
    """

    def __init__(self, status=200, body=None, headers=None):
        self.status = status or 200
        self.reason = httplib.responses[self.status]
        self.headers = headers or {}
        if isinstance(body, dict):
            self.__body = bytearray(json.dumps(body).encode(DEFAULT_ENCODING))
            self.headers.setdefault("Content-Type", "application/json; charset=" + DEFAULT_ENCODING)
        elif body:
            self.__body = bytearray(body.encode(DEFAULT_ENCODING))  # TODO: content types
        else:
            self.__body = bytearray()
        self.headers.setdefault("Content-Length", len(self.__body))
        self.headers.setdefault("Content-Type", "text/plain")

    def getheader(self, name, default=None):
        headers = self.headers.get(name) or default
        return headers

    def getheaders(self):
        return list(self.headers.items())

    def read(self, size=None):
        if size is None:
            size = len(self.__body)
        part, self.__body = self.__body[:size], self.__body[size:]
        return part


class MockConnection(object):
    """ Context manager for Mock HTTP/HTTPS connections.
    """

    def __init__(self, responder):
        self.__original_connection_classes = {}
        self.__mocked_connection_classes = {
            "http": type(MockHTTPConnection.__class__.__name__,
                         (MockHTTPConnection,),
                         {"responder": staticmethod(responder)}),
            "https": type(MockHTTPSConnection.__class__.__name__,
                          (MockHTTPSConnection,),
                          {"responder": staticmethod(responder)}),
        }

    def __enter__(self):
        """ Replace the proper connection classes with mocked equivalents.
        """
        self.__original_connection_classes.update(connection_classes)
        connection_classes.update(self.__mocked_connection_classes)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Reset the connection classes back to normal.
        """
        connection_classes.update(self.__original_connection_classes)
