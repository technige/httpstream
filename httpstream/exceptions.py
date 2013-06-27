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


import os
try:
    from http.client import HTTPException
except ImportError:
    from httplib import HTTPException
import logging


log = logging.getLogger("httpstream.http")


class Loggable(object):

    def __init__(self, cls, message):
        log.error("!!! {0}: {1}".format(cls.__name__, message))


class NetworkAddressError(Loggable, IOError):

    def __init__(self, message, netloc=None):
        self._netloc = netloc
        IOError.__init__(self, message)
        Loggable.__init__(self, self.__class__, message)

    @property
    def netloc(self):
        return self._netloc


class SocketError(Loggable, IOError):

    def __init__(self, code, netloc=None):
        self._code = code
        self._netloc = netloc
        message = os.strerror(code)
        IOError.__init__(self, message)
        Loggable.__init__(self, self.__class__, message)

    @property
    def code(self):
        return self._code

    @property
    def netloc(self):
        return self._netloc


class RedirectionError(Loggable, HTTPException):

    def __init__(self, *args, **kwargs):
        HTTPException.__init__(self, *args, **kwargs)
        Loggable.__init__(self, self.__class__, args[0])
