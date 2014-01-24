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
from httpstream.mock.http import MockedConnection, MockHTTPResponse


def assert_response(response, status_code, reason):
    assert response.status_code == status_code
    assert response.reason == reason


def assert_response_ok(response):
    assert_response(response, 200, "OK")


def test_static_response():
    with MockedConnection(lambda method, uri: MockHTTPResponse()):
        assert_response_ok(get("http://example.com/"))


def test_list_of_responses():
    responses = [MockHTTPResponse()]
    with MockedConnection(lambda method, uri: responses.pop(0)):
        assert_response_ok(get("http://example.com/"))


def test_subsequent_mocked_connection_contexts():
    static_responder = lambda method, uri: MockHTTPResponse()
    with MockedConnection(static_responder):
        assert_response_ok(get("http://example.com/"))
    with MockedConnection(static_responder):
        assert_response_ok(get("http://example.com/"))


def test_multiple_responses():
    responses = [
        MockHTTPResponse(),
        MockHTTPResponse(),
        MockHTTPResponse(),
        MockHTTPResponse(),
        MockHTTPResponse(),
    ]
    with MockedConnection(lambda method, uri: responses.pop(0)):
        while responses:
            assert_response_ok(get("http://example.com/"))


def test_returning_503_on_missing_response():
    responses = []

    def responder(method, uri):
        try:
            return responses.pop(0)
        except IndexError:
            return MockHTTPResponse(503)

    with MockedConnection(responder):
        try:
            get("http://example.com/")
        except ServerError as error:
            assert_response(error, 503, "Service Unavailable")
        else:
            assert False


def test_response_dictionary():
    responses = {
        ("GET", "http://example.com/"): MockHTTPResponse(),
    }

    def responder(method, uri):
        try:
            return responses[(method, uri)]
        except KeyError:
            return MockHTTPResponse(503)

    with MockedConnection(responder):
        assert_response_ok(get("http://example.com/"))
        try:
            get("http://nowhere.net/")
        except ServerError as error:
            assert_response(error, 503, "Service Unavailable")
        else:
            assert False
