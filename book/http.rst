HTTP Resources & Streaming
==========================

Resources
---------

Resources are one of the core features provided by httpstream. As defined by
the HTTP specification, a resource is an entity identified by a URI and
therefore an httpstream ``Resource`` can be constructed simply using a URI:

    >>> from httpstream import Resource
    >>> resource = Resource("http://example.com/foo/bar")

Although the ``Resource`` class can be used directly, applications may wish to
either inherit from or wrap this class to provide more meaningful naming::

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

For simple HTTP access, resources can be created and used in an immediate
inline context::

    >>> from httpstream import Resource
    >>> results = Resource("https://api.duckduckgo.com/?q=neo4j&format=json").get().content
    
A shorthand is also available for implicit resource creation::

    >>> from httpstream import get
    >>> results = get("https://api.duckduckgo.com/?q=neo4j&format=json").content


Resource Templates
------------------

    >>> from httpstream import ResourceTemplate
    >>> searcher = ResourceTemplate("https://api.duckduckgo.com/?q={query}&format=json")
    >>> results = searcher.expand(query="neo4j").get().content



.. autoclass:: httpstream.http.Resource
    :members: get, put, post, delete, resolve

Requests & Responses
--------------------

.. autoclass:: httpstream.http.Request
    :members:

.. autoclass:: httpstream.http.Response
    :members:

Incremental JSON Parsing
------------------------

.. autoclass:: httpstream.jsonstream.JSONStream
    :members:

Errors
------

