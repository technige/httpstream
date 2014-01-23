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

from httpstream import get
from httpstream.mock.http import MockedConnection, MockHTTPResponse


def test_mocked_connection_context_followed_by_normal_connection():
    responses = [MockHTTPResponse()]
    with MockedConnection(responses):
        response = get("http://example.com/")
        assert response.status_code == 200
        assert response.reason == "OK"
        assert response.content == ""
    response = get("http://localhost:8080/hello")
    assert response.is_text
    assert response.content == "hello, world"
