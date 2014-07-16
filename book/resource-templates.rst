Resource Templates
==================

    >>> from httpstream import ResourceTemplate
    >>> searcher = ResourceTemplate("https://api.duckduckgo.com/?q={query}&format=json")
    >>> results = searcher.expand(query="neo4j").get().content

.. autoclass:: httpstream.ResourceTemplate
    :members:
    :undoc-members:
