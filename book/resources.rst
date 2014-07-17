Resources
=========

Often, it will be necessary to submit multiple HTTP requests to the same URI, particularly when
working with RESTful web services. The :class:`Resource <httpstream.Resource>` class provides a
way to wrap a reference to a single URI and fire GET, POST or other requests at it as required.

A ``Resource`` can be constructed by simply passing it the URI that it wraps. To then perform a
``POST``, for example, simply call the :func:`post <httpstream.Resource.post>` method::

    >>> from httpstream import Resource
    >>> resource = Resource("http://example.com/foo/bar")
    >>> resource.post({"stuff": [1, 2, 3]})
    201 Created

As well as using the ``Resource`` class directly, it can also be subclassed or wrapped by an
application class::

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

Resource Class
--------------

.. autoclass:: httpstream.Resource
    :members: get, put, post, delete, head, resolve
