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

from httpstream import get, put, post, delete
from httpstream.mock import MockConnection, MockResponse
from httpstream.packages.urimagic import URI, URITemplate


BATCH = URITemplate("{+base}/db/data/batch")
CYPHER = URITemplate("{+base}/db/data/cypher")
DATA = URITemplate("{+base}/db/data/")
EXTENSIONS_INFO = URITemplate("{+base}/db/data/ext")
MANAGEMENT = URITemplate("{+base}/db/manage/")
NODE = URITemplate("{+base}/db/data/node")
NODE_INDEX = URITemplate("{+base}/db/data/index/node")
RELATIONSHIP_INDEX = URITemplate("{+base}/db/data/index/relationship")
RELATIONSHIP_TYPES = URITemplate("{+base}/db/data/relationship/types")
TRANSACTION = URITemplate("{+base}/db/data/transaction")


def get_service_root_responder(request):
    base = URI.build(scheme=request.uri.scheme, host_port=request.uri.host_port)
    return MockResponse(body={
        "management": MANAGEMENT.expand(base=base).string,
        "data": DATA.expand(base=base).string,
    })


def get_data_responder(request, version):
    base = URI.build(scheme=request.uri.scheme, host_port=request.uri.host_port)
    return MockResponse(body={
        "extensions": {},
        "node": NODE.expand(base=base).string,
        "node_index": NODE_INDEX.expand(base=base).string,
        "relationship_index": RELATIONSHIP_INDEX.expand(base=base).string,
        "extensions_info": EXTENSIONS_INFO.expand(base=base).string,
        "relationship_types": RELATIONSHIP_TYPES.expand(base=base).string,
        "batch": BATCH.expand(base=base).string,
        "cypher": CYPHER.expand(base=base).string,
        "transaction": TRANSACTION.expand(base=base).string,
        "neo4j_version": version,
    })


def post_node_responder(request):
    base = URI.build(scheme=request.uri.scheme, host_port=request.uri.host_port)
    # TODO: make these templates
    return MockResponse(status=201, body={
        "extensions": {},
        "paged_traverse": "http://localhost:7474/db/data/node/1033/paged/traverse/{returnType}{?pageSize,leaseTime}",
        "labels": "http://localhost:7474/db/data/node/1033/labels",
        "outgoing_relationships": "http://localhost:7474/db/data/node/1033/relationships/out",
        "traverse": "http://localhost:7474/db/data/node/1033/traverse/{returnType}",
        "all_typed_relationships": "http://localhost:7474/db/data/node/1033/relationships/all/{-list|&|types}",
        "property": "http://localhost:7474/db/data/node/1033/properties/{key}",
        "all_relationships": "http://localhost:7474/db/data/node/1033/relationships/all",
        "self": "http://localhost:7474/db/data/node/1033",
        "properties": "http://localhost:7474/db/data/node/1033/properties",
        "outgoing_typed_relationships": "http://localhost:7474/db/data/node/1033/relationships/out/{-list|&|types}",
        "incoming_relationships": "http://localhost:7474/db/data/node/1033/relationships/in",
        "incoming_typed_relationships": "http://localhost:7474/db/data/node/1033/relationships/in/{-list|&|types}",
        "create_relationship": "http://localhost:7474/db/data/node/1033/relationships",
        "data": {}
    }, headers={"Location": "http://localhost:7474/db/data/node/1033"})


def neo4j_2_0_0_responder(request):
    version = "2.0.0"
    if request.method == "GET" and request.uri.path == "/":
        response = get_service_root_responder(request)
    elif request.method == "GET" and request.uri.path == "/db/data/":
        response = get_data_responder(request, version=version)
    elif request.method == "POST" and request.uri.path == "/db/data/node":
        response = post_node_responder(request)
    else:
        response = MockResponse(404)
    response.headers.setdefault("Access-Control-Allow-Origin", "*")
    response.headers.setdefault("Server", "Jetty")
    return response


class MockNeo4j(MockConnection):

    def __init__(self, version="2.0.0"):
        if version == "2.0.0":
            responder = neo4j_2_0_0_responder
        else:
            raise ValueError("Unsupported server version")
        MockConnection.__init__(self, responder)

    def __enter__(self):
        return MockConnection.__enter__(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        MockConnection.__exit__(self, exc_type, exc_val, exc_tb)


def test_can_get_service_root():
    with MockNeo4j():
        response = get("http://localhost:7474/")
        assert response.is_json
        assert response.content == {
            'management': 'http://localhost:7474/db/manage/',
            'data': 'http://localhost:7474/db/data/',
        }


def test_can_get_database_root():
    with MockNeo4j():
        response = get("http://localhost:7474/db/data/")
        assert response.is_json
        assert response.content == {
            'extensions': {},
            'node': 'http://localhost:7474/db/data/node',
            'node_index': 'http://localhost:7474/db/data/index/node',
            'relationship_index': 'http://localhost:7474/db/data/'
                                  'index/relationship',
            'extensions_info': 'http://localhost:7474/db/data/ext',
            'relationship_types': 'http://localhost:7474/db/data/'
                                  'relationship/types',
            'batch': 'http://localhost:7474/db/data/batch',
            'cypher': 'http://localhost:7474/db/data/cypher',
            'transaction': 'http://localhost:7474/db/data/transaction',
            'neo4j_version': '2.0.0',
        }


def test_can_post_node():
    with MockNeo4j():
        response = post("http://localhost:7474/db/data/node")
        assert response.is_json
        assert response.content == {
            "extensions": {},
            "paged_traverse": "http://localhost:7474/db/data/node/1033/paged/traverse/{returnType}{?pageSize,leaseTime}",
            "labels": "http://localhost:7474/db/data/node/1033/labels",
            "outgoing_relationships": "http://localhost:7474/db/data/node/1033/relationships/out",
            "traverse": "http://localhost:7474/db/data/node/1033/traverse/{returnType}",
            "all_typed_relationships": "http://localhost:7474/db/data/node/1033/relationships/all/{-list|&|types}",
            "property": "http://localhost:7474/db/data/node/1033/properties/{key}",
            "all_relationships": "http://localhost:7474/db/data/node/1033/relationships/all",
            "self": "http://localhost:7474/db/data/node/1033",
            "properties": "http://localhost:7474/db/data/node/1033/properties",
            "outgoing_typed_relationships": "http://localhost:7474/db/data/node/1033/relationships/out/{-list|&|types}",
            "incoming_relationships": "http://localhost:7474/db/data/node/1033/relationships/in",
            "incoming_typed_relationships": "http://localhost:7474/db/data/node/1033/relationships/in/{-list|&|types}",
            "create_relationship": "http://localhost:7474/db/data/node/1033/relationships",
            "data": {}
        }
        assert response.headers.get("Location") == "http://localhost:7474/db/data/node/1033"
