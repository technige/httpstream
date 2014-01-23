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

HTTPStream defines four types of response objects. A standard ``Response`` is
generated on receipt of a 2xx status code and a ``ClientError`` and
``ServerError`` may be raised on receipt of 4xx and 5xx statuses respectively.
The fourth response type is ``Redirection`` which is generally consumed
internally but may also be returned under certain circumstances.

Response objects are file-like and as such may be ``read`` or iterated through
The ``iter_lines`` and ``iter_json`` methods may be used to step through
known types of content. The response object itself may also be iterated
directly and an appropriate type of iterator is selected depending on the
type of content available. The example below shows how to print each line of
textual content as it is received::

    >>> for line in res.get():
    ...     print line


.. autoclass:: httpstream.Request
    :members:

.. autoclass:: httpstream.Response
    :members:

.. autoclass:: httpstream.Redirection
    :show-inheritance:
    :members:

.. autoclass:: httpstream.ClientError
    :show-inheritance:
    :members:

.. autoclass:: httpstream.ServerError
    :show-inheritance:
    :members:


Incremental JSON Parsing
------------------------

.. autoclass:: httpstream.JSONStream
    :members:

.. autofunction:: httpstream.assembled

.. autofunction:: httpstream.grouped


Errors
------

.. autoexception:: httpstream.NetworkAddressError
    :members:
    :undoc-members:

.. autoexception:: httpstream.SocketError
    :members:
    :undoc-members:

.. autoexception:: httpstream.RedirectionError
    :members:
    :undoc-members:
