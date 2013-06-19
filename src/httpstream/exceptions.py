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
    from http.client import HTTPException
except ImportError:
    from httplib import HTTPException


class TooManyRedirects(HTTPException):
    pass


class HTTPClientError(HTTPException):

    def __init__(self, status_code, reason=None):
        assert status_code // 100 == 4
        HTTPException.__init__(self)
        self.status_code = status_code
        self.reason = reason


class HTTPServerError(HTTPException):

    def __init__(self, status_code, reason=None):
        assert status_code // 100 == 5
        HTTPException.__init__(self)
        self.status_code = status_code
        self.reason = reason


class BadRequest(HTTPClientError):

    def __init__(self, reason=None):
        HTTPClientError.__init__(self, 400, reason or "Bad Request")


class Unauthorized(HTTPClientError):

    def __init__(self, reason=None):
        HTTPClientError.__init__(self, 401, reason or "Unauthorized")


class NotFound(HTTPClientError):

    def __init__(self, reason=None):
        HTTPClientError.__init__(self, 404, reason or "Not Found")


class Conflict(HTTPClientError):

    def __init__(self, reason=None):
        HTTPClientError.__init__(self, 409, reason or "Conflict")
