#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2012-2013 Nigel Small
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

import json
from httpstream.jsonstream import JSONStream, assembled


def test_can_assemble_data():
    src = [
        {
            "person": {
                "name": "Alice Allison",
                "age": 34,
                "favourite_colours": ["purple", "red"]
            }
        },
        {
            "person": {
                "name": "Bob Robertson",
                "age": 66,
                "favourite_colours": ["blue", "green"]
            }
        },
        {
            "person": {
                "name": "Carol Carlsson",
                "age": 50,
                "favourite_colours": []
            }
        }
    ]
    data_in = json.dumps(src, ensure_ascii=False)
    data_out = assembled(JSONStream(data_in))
    assert data_out == src
