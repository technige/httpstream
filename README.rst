==========
HTTPStream
==========

**HTTPStream** is a simple and pragmatic HTTP client library for Python that
provides support for incremental JSON document retrieval and RFC 6570 URI
Templates.


Installation
============

HTTPStream is hosted on PyPI and so to install, simply use ``easy_install``
or - preferably - ``pip``::

    easy_install httpstream
    pip install httpstream

No external dependencies are required, the entire package is self-contained and
relies only on standard library components.


Basic Usage
===========

HTTPStream is centred around ``Resource`` objects which are defined by a URI
and may be accessed via methods such as ``get`` and ``post``. A ``Resource``
may be declared as follows::

    >>> from httpstream import Resource
    >>> res = Resource("http://example.com/")

Once defined, accessor methods can be used on a resource in much the same way
as the Python built-in method, ``open``. These return file-like ``Response``
objects which may be read in full or iterated through. To retrieve the entire
response, simply access its ``content`` property. This returns data of a type
appropriate to that specified in the ``Content-Type`` header: a *string* for
``text/*`` content, a *dictionary* for ``application/json`` content or a
*bytearray* for everything else::

    >>> print res.get().content
    <!doctype html>
    <html>
    <head>
        <title>Example Domain</title>
        ...


Other Methods
=============

As well as ``get``, there are ``put``, ``post`` and ``delete`` methods
available. Both ``put`` and ``post`` can take optional payload data and all
methods can take a dictionary of header fields. For example::

    >> res.post("foo")
    >> res.post({"foo": "bar"})

The ``body`` can be either a string or a dictionary. If a dictionary is
passed, the payload is automatically converted to JSON and the
``Content-Type`` header field is set accordingly.


Responses
=========

HTTPStream defines four types of response objects returned from the methods
above. A standard ``Response`` is generated on receipt of a 2xx status code
and a ``ClientError`` and ``ServerError`` may be raised on receipt of 4xx
and 5xx statuses respectively. The fourth response type is ``Redirection``
which is generally consumed internally but may also be returned under certain
circumstances.

Response objects are file-like and as such may be ``read`` or iterated through
The ``iter_lines`` and ``iter_json`` methods may be used to step through
known types of content. The response object itself may also be iterated
directly and an appropriate type of iterator is selected depending on the
type of content available. The example below shows how to print each line of
textual content as it is received::

    >>> for line in res.get():
    ...     print line

