HTTPStream
==========

HTTPStream is a simple and pragmatic HTTP client library for Python that
provides support for incremental JSON document retrieval and RFC 6570 URI
Templates.


Resources
---------

A resource is an entity that exists on a distributed system, such as the World
Wide Web, and is identified by a URI. Commonly associated with the REST
architectural style, web resources are objects upon which HTTP methods like
GET and POST can be actioned.

HTTPStream is built around a core :py:class:`Resource <httpstream.Resource>`
class that embodies the concept of the web resource and instances can be
constructed by simply using the URI by which they are uniquely identified::

    >>> from httpstream import Resource
    >>> resource = Resource("http://example.com/foo/bar")

Although the ``Resource`` class can be used directly, applications may
alternatively either inherit from or wrap this class to provide more meaningful
naming::

    from httpstream import Resource

    class InheritedMailbox(Resource):

        def __init__(self, uri):
            Resource.__init__(self, uri)

        def deliver(self, message):
            self.post(message)

    class WrappedMailbox(object):

        def __init__(self, uri):
            self._resource = Resource(uri)

        def deliver(self, message):
            self._resource.post(message)

For simple HTTP access, resources can of course be created and used in an
immediate inline context::

    >>> from httpstream import Resource
    >>> results = Resource("https://api.duckduckgo.com/?q=neo4j&format=json").get().content

Methods such as :py:func:`get <httpstream.Resource.get>` return a
file-like :py:class:`Response <httpstream.Response>` object. The response
content can be either iterated through or retrieved at once::

    resource = Resource("http://example.com/")

    # print each line of the response in turn
    with resource.get() as response:
        for line in response:
            print line

    # print the entire response content at once
    with resource.get() as response:
        print response.content


.. autoclass:: httpstream.Resource
    :members: get, put, post, delete, head, resolve


Implicit Resources
------------------

A shorthand is also available for implicit resource creation::

    >>> from httpstream import get
    >>> results = get("https://api.duckduckgo.com/?q=neo4j&format=json").content

.. autofunction:: httpstream.get

.. autofunction:: httpstream.put

.. autofunction:: httpstream.post

.. autofunction:: httpstream.delete

.. autofunction:: httpstream.head


Resource Templates
------------------

    >>> from httpstream import ResourceTemplate
    >>> searcher = ResourceTemplate("https://api.duckduckgo.com/?q={query}&format=json")
    >>> results = searcher.expand(query="neo4j").get().content

.. autoclass:: httpstream.ResourceTemplate
    :members:
    :undoc-members:


Requests & Responses
--------------------

.. autoclass:: httpstream.Request
    :members:

.. autoclass:: httpstream.Response
    :members:


Incremental JSON Parsing
------------------------

.. autoclass:: httpstream.JSONStream
    :members:

.. autofunction:: httpstream.assembled

.. autofunction:: httpstream.grouped


URIs
----

.. autoclass:: httpstream.URI
    :members:
    :undoc-members:

.. autoclass:: httpstream.Authority
    :members:
    :undoc-members:

.. autoclass:: httpstream.Path
    :members:
    :undoc-members:

.. autoclass:: httpstream.Query
    :members:
    :undoc-members:


URI Templates
-------------

.. autoclass:: httpstream.URITemplate
    :members:
    :undoc-members:

.. seealso::
    `RFC 6570`_

.. _`RFC 6570`: http://tools.ietf.org/html/rfc6570


Percent Encoding
----------------

Percent encoding is used within URI components to allow inclusion of certain
characters which are not within a permitted set.

.. autofunction:: httpstream.percent_encode

.. autofunction:: httpstream.percent_decode

.. seealso::
    `RFC 3986 § 2.1`_

.. _`RFC 3986 § 2.1`: http://tools.ietf.org/html/rfc3986#section-2.1


Errors
------

