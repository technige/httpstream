HTTPStream
==========

```python
>>> from httpstream import Resource
>>> for key, value in Resource("https://api.duckduckgo.com/?q=neo4j&format=json").get():
...     print key, value
...
(u'Definition',)
(u'DefinitionSource',)
(u'Heading',) Neo4j
(u'AbstractSource',) Wikipedia
(u'Image',) https://i.duckduckgo.com/i/4d74091a.jpg
(u'RelatedTopics', 0, u'Result') <a href="http://duckduckgo.com/noSQL">Structured storage</a> - In computing, NoSQL is a broad class of database management systems identified by non-adherence to the widely used relational database management system model.
(u'RelatedTopics', 0, u'Icon', u'URL')
(u'RelatedTopics', 0, u'Icon', u'Height')
(u'RelatedTopics', 0, u'Icon', u'Width')
(u'RelatedTopics', 0, u'FirstURL') http://duckduckgo.com/noSQL
(u'RelatedTopics', 0, u'Text') Structured storage - In computing, NoSQL is a broad class of database management systems identified by non-adherence to the widely used relational database management system model.
(u'RelatedTopics', 1, u'Result') <a href="http://duckduckgo.com/CODASYL">CODASYL</a> - CODASYL is an acronym for "Conference on Data Systems Languages".
(u'RelatedTopics', 1, u'Icon', u'URL')
(u'RelatedTopics', 1, u'Icon', u'Height')
(u'RelatedTopics', 1, u'Icon', u'Width')
(u'RelatedTopics', 1, u'FirstURL') http://duckduckgo.com/CODASYL
(u'RelatedTopics', 1, u'Text') CODASYL - CODASYL is an acronym for "Conference on Data Systems Languages".
(u'RelatedTopics', 2, u'Result') <a href="http://duckduckgo.com/c/Software_companies_of_Sweden">Software companies of Sweden</a>
(u'RelatedTopics', 2, u'Icon', u'URL')
(u'RelatedTopics', 2, u'Icon', u'Height')
(u'RelatedTopics', 2, u'Icon', u'Width')
(u'RelatedTopics', 2, u'FirstURL') http://duckduckgo.com/c/Software_companies_of_Sweden
(u'RelatedTopics', 2, u'Text') Software companies of Sweden
(u'RelatedTopics', 3, u'Result') <a href="http://duckduckgo.com/c/Structured_storage">Structured storage</a>
(u'RelatedTopics', 3, u'Icon', u'URL')
(u'RelatedTopics', 3, u'Icon', u'Height')
(u'RelatedTopics', 3, u'Icon', u'Width')
(u'RelatedTopics', 3, u'FirstURL') http://duckduckgo.com/c/Structured_storage
(u'RelatedTopics', 3, u'Text') Structured storage
(u'RelatedTopics', 4, u'Result') <a href="http://duckduckgo.com/c/NoSQL">NoSQL</a>
(u'RelatedTopics', 4, u'Icon', u'URL')
(u'RelatedTopics', 4, u'Icon', u'Height')
(u'RelatedTopics', 4, u'Icon', u'Width')
(u'RelatedTopics', 4, u'FirstURL') http://duckduckgo.com/c/NoSQL
(u'RelatedTopics', 4, u'Text') NoSQL
(u'RelatedTopics', 5, u'Result') <a href="http://duckduckgo.com/c/Free_software_programmed_in_Java">Free software programmed in Java</a>
(u'RelatedTopics', 5, u'Icon', u'URL')
(u'RelatedTopics', 5, u'Icon', u'Height')
(u'RelatedTopics', 5, u'Icon', u'Width')
(u'RelatedTopics', 5, u'FirstURL') http://duckduckgo.com/c/Free_software_programmed_in_Java
(u'RelatedTopics', 5, u'Text') Free software programmed in Java
(u'AbstractText',) Neo4j is an open-source graph database, implemented in Java.
(u'Abstract',) Neo4j is an open-source graph database, implemented in Java.
(u'AnswerType',)
(u'Redirect',)
(u'Type',) A
(u'DefinitionURL',)
(u'Answer',)
(u'AbstractURL',) https://en.wikipedia.org/wiki/Neo4j
```
