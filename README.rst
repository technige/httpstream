.. image:: https://travis-ci.org/nigelsmall/httpstream.png?branch=master
   :target: https://travis-ci.org/nigelsmall/httpstream


==========
HTTPStream
==========

*HTTPStream* is an HTTP client library for Python with an easy-to-use API and
support for incremental JSON document retrieval.


Installation
============

HTTPStream is hosted on PyPI and so to install, simply use ``pip``::

    pip install httpstream

No external dependencies are required, the entire package is self-contained and
relies only on standard library components.


Quick Start
===========

::

    >>> from httpstream import get
    >>> get("https://api.duckduckgo.com/?q=neo4j&format=json").content
    {'Abstract': 'Neo4j is an open-source graph database, implemented in Java.',
     'AbstractSource': 'Wikipedia',
     'AbstractText': 'Neo4j is an open-source graph database, implemented in Java.',
     'AbstractURL': 'https://en.wikipedia.org/wiki/Neo4j',
     'Answer': '',
     'AnswerType': '',
     'Definition': '',
     'DefinitionSource': '',
     'DefinitionURL': '',
     'Heading': 'Neo4j',
     'Image': 'https://i.duckduckgo.com/i/4d74091a.jpg',
     'Redirect': '',
     'RelatedTopics': [{'FirstURL': 'http://duckduckgo.com/noSQL',
       'Icon': {'Height': '', 'URL': '', 'Width': ''},
       'Result': '<a href="http://duckduckgo.com/noSQL">Structured storage</a> - A NoSQL database provides a mechanism for storage and retrieval of data that is modeled in means other than the tabular relations used in relational databases.',
       'Text': 'Structured storage - A NoSQL database provides a mechanism for storage and retrieval of data that is modeled in means other than the tabular relations used in relational databases.'},
      {'FirstURL': 'http://duckduckgo.com/CODASYL',
       'Icon': {'Height': '', 'URL': '', 'Width': ''},
       'Result': '<a href="http://duckduckgo.com/CODASYL">CODASYL</a> - CODASYL (often spelled Codasyl) is an acronym for "Conference on Data Systems Languages".',
       'Text': 'CODASYL - CODASYL (often spelled Codasyl) is an acronym for "Conference on Data Systems Languages".'},
      {'FirstURL': 'http://duckduckgo.com/Cypher_Query_Language',
       'Icon': {'Height': '', 'URL': '', 'Width': ''},
       'Result': '<a href="http://duckduckgo.com/Cypher_Query_Language">Cypher Query Language</a>',
       'Text': 'Cypher Query Language'},
      {'FirstURL': 'http://duckduckgo.com/c/Software_companies_of_Sweden',
       'Icon': {'Height': '', 'URL': '', 'Width': ''},
       'Result': '<a href="http://duckduckgo.com/c/Software_companies_of_Sweden">Software companies of Sweden</a>',
       'Text': 'Software companies of Sweden'},
      {'FirstURL': 'http://duckduckgo.com/c/Structured_storage',
       'Icon': {'Height': '', 'URL': '', 'Width': ''},
       'Result': '<a href="http://duckduckgo.com/c/Structured_storage">Structured storage</a>',
       'Text': 'Structured storage'},
      {'FirstURL': 'http://duckduckgo.com/c/NoSQL',
       'Icon': {'Height': '', 'URL': '', 'Width': ''},
       'Result': '<a href="http://duckduckgo.com/c/NoSQL">NoSQL</a>',
       'Text': 'NoSQL'},
      {'FirstURL': 'http://duckduckgo.com/c/Free_software_programmed_in_Java',
       'Icon': {'Height': '', 'URL': '', 'Width': ''},
       'Result': '<a href="http://duckduckgo.com/c/Free_software_programmed_in_Java">Free software programmed in Java</a>',
       'Text': 'Free software programmed in Java'}],
     'Results': [{'FirstURL': 'http://neo4j.org',
       'Icon': {'Height': 16,
        'URL': 'https://i.duckduckgo.com/i/neo4j.org.ico',
        'Width': 16},
       'Result': '<a href="http://neo4j.org"><b>Official site</b></a><a href="http://neo4j.org"></a>',
       'Text': 'Official site'}],
     'Type': 'A'}


Full Documentation
==================

For further information on how to use HTTPStream, check out the pages on
`Read the Docs <https://httpstream.readthedocs.org>`_.
