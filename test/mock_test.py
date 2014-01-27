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

from httpstream import get, ServerError
from httpstream.mock import MockConnection, MockResponse


def assert_response(response, status_code, reason):
    assert response.status_code == status_code
    assert response.reason == reason


def assert_response_ok(response):
    assert_response(response, 200, "OK")


def test_static_response():
    with MockConnection(lambda request: MockResponse()):
        assert_response_ok(get("http://example.com/"))


def test_list_of_responses():
    responses = [MockResponse()]
    with MockConnection(lambda request: responses.pop(0)):
        assert_response_ok(get("http://example.com/"))


def test_subsequent_mocked_connection_contexts():
    static_responder = lambda request: MockResponse()
    with MockConnection(static_responder):
        assert_response_ok(get("http://example.com/"))
    with MockConnection(static_responder):
        assert_response_ok(get("http://example.com/"))


def test_multiple_responses():
    responses = [
        MockResponse(),
        MockResponse(),
        MockResponse(),
        MockResponse(),
        MockResponse(),
    ]
    with MockConnection(lambda request: responses.pop(0)):
        while responses:
            assert_response_ok(get("http://example.com/"))


def test_returning_503_on_missing_response():
    responses = []

    def responder(request):
        try:
            return responses.pop(0)
        except IndexError:
            return MockResponse(503)

    with MockConnection(responder):
        try:
            get("http://example.com/")
        except ServerError as error:
            assert_response(error, 503, "Service Unavailable")
        else:
            assert False


def test_response_dictionary():
    responses = {
        ("GET", "http://example.com/"): MockResponse(),
    }

    def responder(request):
        try:
            return responses[(request.method, request.url)]
        except KeyError:
            return MockResponse(503)

    with MockConnection(responder):
        assert_response_ok(get("http://example.com/"))
        try:
            get("http://nowhere.net/")
        except ServerError as error:
            assert_response(error, 503, "Service Unavailable")
        else:
            assert False
