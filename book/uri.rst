URIs and URI Templates
======================


Percent Encoding
----------------

Percent encoding is used within URI components to allow inclusion of certain
characters which are not within a permitted set.

.. autofunction:: httpstream.uri.percent_encode

.. autofunction:: httpstream.uri.percent_decode

.. seealso::
    `RFC 3986 § 2.1`_

.. _`RFC 3986 § 2.1`: http://tools.ietf.org/html/rfc3986#section-2.1


URIs
----

.. autoclass:: httpstream.uri.URI
    :members:
    :undoc-members:

.. seealso::
    `RFC 3986`_

.. _`RFC 3986`: http://tools.ietf.org/html/rfc3986


URI Templates
-------------

.. autoclass:: httpstream.uri.URITemplate
    :members:
    :undoc-members:

.. seealso::
    `RFC 6570`_

.. _`RFC 6570`: http://tools.ietf.org/html/rfc6570
