#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2012-2015, Nigel Small
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


from __future__ import print_function

import sys

from . import get, download


def _help(script):
    print("Usage: {script}", script=script)


def main():
    script, args = sys.argv[0], sys.argv[1:]
    if len(args) == 1:
        sys.stdout.write(get(args[0]).content)
    elif len(args) == 2:
        download(args[0], args[1])
    else:
        _help(script)


if __name__ == "__main__":
    main()
