#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013-2014, Nigel Small
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


""" HTTPStream is an HTTP client library for Python that wraps the
standard library HTTP client with a convenient resource-based interface
and also provides support for incremental JSON document retrieval and
RFC 6570 URI Templates.
"""


__author__ = "Nigel Small"
__copyright__ = "2013-2014, Nigel Small"
__email__ = "nigel@nigelsmall.com"
__license__ = "Apache License, Version 2.0"
__version__ = "1.3.0"


from .http import *
from .watch import watch


def head(uri, headers=None, redirect_limit=5, **kwargs):
    """ Issue an HTTP ``HEAD`` request to a given `uri`.

    :param uri: target URI for the request
    :param headers: dictionary of extra headers to send (optional)
    :param redirect_limit: maximum number of redirects to follow (optional, default=5)
    :param kwargs: see :func:`get <httpstream.get>` for other keyword arguments
    :return: file-like :class:`Response <httpstream.Response>` object from which
        content can be read
    """
    return Resource(uri).head(headers, redirect_limit, **kwargs)


def get(uri, headers=None, redirect_limit=5, **kwargs):
    """ Issue an HTTP ``GET`` request to a given `uri`.

    :param uri: target URI for the request
    :param headers: dictionary of extra headers to send (optional)
    :param redirect_limit: maximum number of redirects to follow (optional, default=5)
    :param product: name or (name, version) tuple to be passed in the ``User-Agent``
        header (optional)
    :param chunk_size: number of bytes to retrieve per chunk (optional, default=4096)
    :param cache: boolean flag to allow caching so response content can be stored
        for multiple reads (optional)
    :return: file-like :class:`Response <httpstream.Response>` object from which
        content can be read
    """
    return Resource(uri).get(headers, redirect_limit, **kwargs)


def put(uri, body=None, headers=None, **kwargs):
    """ Issue an HTTP ``PUT`` request to a given `uri`, optionally with a payload.

    :param uri: target URI for the request
    :param body: payload to be sent with the request (optional)
    :param headers: dictionary of extra headers to send (optional)
    :param kwargs: see :func:`get <httpstream.get>` for other keyword arguments
    :return: file-like :class:`Response <httpstream.Response>` object from which
        content can be read
    """
    return Resource(uri).put(body, headers, **kwargs)


def patch(uri, body=None, headers=None, **kwargs):
    """ Issue an HTTP ``PUT`` request to a given `uri`, optionally with a payload.

    :param uri: target URI for the request
    :param body: payload to be sent with the request (optional)
    :param headers: dictionary of extra headers to send (optional)
    :param kwargs: see :func:`get <httpstream.get>` for other keyword arguments
    :return: file-like :class:`Response <httpstream.Response>` object from which
        content can be read
    """
    return Resource(uri).patch(body, headers, **kwargs)


def post(uri, body=None, headers=None, **kwargs):
    """ Issue an HTTP ``POST`` request to a given `uri`, optionally with a payload.

    :param uri: target URI for the request
    :param body: payload to be sent with the request (optional)
    :param headers: dictionary of extra headers to send (optional)
    :param kwargs: see :func:`get <httpstream.get>` for other keyword arguments
    :return: file-like :class:`Response <httpstream.Response>` object from which
        content can be read
    """
    return Resource(uri).post(body, headers, **kwargs)


def delete(uri, headers=None, **kwargs):
    """ Issue an HTTP ``DELETE`` request to a given `uri`.

    :param uri: target URI for the request
    :param headers: dictionary of extra headers to send (optional)
    :param kwargs: see :func:`get <httpstream.get>` for other keyword arguments
    :return: file-like :class:`Response <httpstream.Response>` object from which
        content can be read
    """
    return Resource(uri).delete(headers, **kwargs)


def download(uri, name=None, headers=None, redirect_limit=5, **kwargs):
    if name is None:
        from .http import make_uri
        uri = make_uri(uri)
        name = uri.path.segments[-1]
    with get(uri) as source:
        with open(name, "wb") as destination:
            destination.write(source.read())
