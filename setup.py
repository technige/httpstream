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


from distutils.core import setup

setup(
    name="httpstream",
    version="0.2",
    description="Stream based HTTP client",
    long_description="",
    author="Nigel Small",
    author_email="nigel@nigelsmall.com",
    url="https://github.com/nigelsmall/httpstream",
    scripts=[],
    package_dir={"": "src"},
    packages=[
        "httpstream",
        "httpstream.packages",
        "httpstream.packages.jsonstream",
    ],
    license="Apache License, Version 2.0",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Topic :: Software Development",
    ]
)
