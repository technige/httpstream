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

from httpstream.packages.urimagic import URI

from ..http import connection_classes


class MockHTTPConnection(object):

    response = None
    scheme = "http"

    def __init__(self, host, port=None, strict=None, timeout=None,
                 source_address=None):
        self.__method = None
        self.__uri = URI.build(scheme=self.scheme, host=host, port=port)

    def connect(self):
        pass

    def close(self):
        pass

    def request(self, method, url, body=None, headers=None):
        self.__method = method
        self.__uri = self.__uri.resolve(url)

    def getresponse(self):
        response = self.response
        if not response:
            return MockHTTPResponse(503)
        elif isinstance(response, MockHTTPResponse):
            return response
        elif isinstance(response, list):
            try:
                return response.pop(0)
            except IndexError:
                return MockHTTPResponse(503)
        elif isinstance(response, dict):
            try:
                # TODO: make the key matching more comprehensive
                method_uri = (self.__method, self.__uri.string)
                return response[method_uri]
            except KeyError:
                return MockHTTPResponse(503)
        else:
            raise TypeError("Unusable response type "
                            "{0}".format(response.__class__))


class MockHTTPResponse(object):

    def __init__(self, status_code=200, content=None, headers=None):
        self.status = status_code or 200
        self.reason = httplib.responses[self.status]
        self.headers = headers or {}
        self.headers.setdefault("Content-Type", "text/plain")
        self.__body = bytearray(content or b"")

    def getheader(self, name, default=None):
        headers = self.headers.get(name) or default
        return headers

    def getheaders(self):
        return list(self.headers.items())

    def read(self, size=None):
        return self.__body


class MockedConnection(object):

    def __init__(self, response):
        self.__mock_http_class = type("MockHTTPConnection",
                                      (MockHTTPConnection,),
                                      {"response": response})
        self.__original_connection_classes = {}
        self.__mocked_connection_classes = {
            "http": self.__mock_http_class,
            "https": self.__mock_http_class,  # TODO: make a proper HTTPS one
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
