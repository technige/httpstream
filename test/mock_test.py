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


def test_mocked_connection_context():
    responses = [MockHTTPResponse()]
    with MockedConnection(responses):
        assert_response_ok(get("http://example.com/"))


def test_subsequent_mocked_connection_contexts():
    responses = [MockHTTPResponse()]
    with MockedConnection(responses):
        assert_response_ok(get("http://example.com/"))
    responses = [MockHTTPResponse()]
    with MockedConnection(responses):
        assert_response_ok(get("http://example.com/"))


def test_multiple_responses():
    responses = [
        MockHTTPResponse(),
        MockHTTPResponse(),
        MockHTTPResponse(),
        MockHTTPResponse(),
        MockHTTPResponse(),
    ]
    with MockedConnection(responses):
        while responses:
            assert_response_ok(get("http://example.com/"))


def test_missing_response_returns_503():
    responses = []
    with MockedConnection(responses):
        try:
            get("http://example.com/")
        except ServerError as error:
            assert_response(error, 503, "Service Unavailable")
        else:
            assert False


def test_single_response_will_be_repeated():
    with MockedConnection(MockHTTPResponse()):
        for i in range(5):
            assert_response_ok(get("http://example.com/"))


def test_response_dictionary():
    responses = {
        ("GET", "http://example.com/"): MockHTTPResponse(),
    }
    with MockedConnection(responses):
        assert_response_ok(get("http://example.com/"))
