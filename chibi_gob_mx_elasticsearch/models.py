#!/usr/bin/env python3
import sys
import fileinput
import json
from elasticsearch_dsl import Document, field, InnerDoc
import logging


logger = logging.getLogger( 'chibi_gob_mx_elasticsearch.models.open_data' )


from elasticsearch_dsl import analyzer, tokenizer

category = analyzer(
    'category',
    tokenizer=tokenizer( 'trigram', 'ngram', min_gram=4, max_gram=5 ),
    filter=[ "asciifolding", "lowercase" ],
)

titles = analyzer(
    'titles',
    tokenizer=tokenizer( 'trigram', 'ngram', min_gram=4, max_gram=5 ),
    filter=[ "asciifolding", "lowercase" ],
)

titles_space = analyzer(
    'titles_space',
    tokenizer='whitespace',
    filter=[ "asciifolding", "lowercase" ],
)

class Data_set_resource( InnerDoc ):
    title = field.Text(
        analyzer=titles,
        fields={
            'space': field.Text( analyzer=titles_space ),
            'keyword': field.Keyword(),
        } )
    description = field.Text(
        analyzer=titles,
        fields={
            'space': field.Text( analyzer=titles_space ),
            'keyword': field.Keyword(),
        } )
    download_link = field.Keyword()
    kind = field.Keyword()


class Metadata( InnerDoc ):
    language = field.Keyword()
    fuente = field.Keyword()
    frequency = field.Keyword()
    name_publisher = field.Keyword()
    email_publisher = field.Keyword()
    published = field.Date()


class User( InnerDoc ):
    name = field.Text(
        analyzer=titles,
        fields={
            'space': field.Text( analyzer=titles_space ),
            'keyword': field.Keyword(),
        } )
    url = field.Keyword()


class Activity( InnerDoc ):
    action = field.Text(
        analyzer=titles,
        fields={
            'space': field.Text( analyzer=titles_space ),
            'keyword': field.Keyword(),
        } )
    date = field.Date()
    user = field.Object( User )


class Dataset( Document ):
    resources = field.Object( Data_set_resource, multi=True )
    tags = field.Text(
        analyzer=titles, multi=True,
        fields={
            'space': field.Text( analyzer=titles_space, multi=True ),
            'keyword': field.Keyword( multi=True ),
        } )

    metadata = field.Object( Metadata )
    activity = field.Object( Activity, multi=True)
    url = field.Keyword()
    status = field.Keyword()
    created_at = field.Date()

    class Index:
        name = 'chibi_gob__open_data__dataset'
        settings = { 'number_of_shards': 2, 'number_of_replicas': 1 }

    @classmethod
    def url_is_scaned( cls, url ):
        logger.info( f"buscando dataset {url}" )
        if cls.search().filter( "term", url=url ).count() > 0:
            return True
        return False

    @classmethod
    def get_by_url( cls, url ):
        logger.info( f"get dataset {url}" )
        result = cls.search().filter( "term", url=url )[:1].execute()
        if result:
            return result[0]
        return None

    def save( self, *args, **kw ):
        super().save( *args, **kw )


class Resource( Document ):
    title = field.Text(
        analyzer=titles,
        fields={
            'space': field.Text( analyzer=titles_space ),
            'keyword': field.Keyword(),
        } )
    description = field.Text(
        analyzer=titles,
        fields={
            'space': field.Text( analyzer=titles_space ),
            'keyword': field.Keyword(),
        } )
    kind = field.Keyword()
    url = field.Keyword()
    created_at = field.Date()

    tags = field.Text(
        analyzer=titles, multi=True,
        fields={
            'space': field.Text( analyzer=titles_space, multi=True ),
            'keyword': field.Keyword( multi=True ),
        } )

    metadata = field.Object( Metadata )

    class Index:
        name = 'chibi_gob__open_data__dataset__resource'
        settings = { 'number_of_shards': 2, 'number_of_replicas': 1 }

    @classmethod
    def url_is_scaned( cls, url ):
        logger.info( f"buscando dataset {url}" )
        if cls.search().filter( "term", url=url ).count() > 0:
            return True
        return False

    def save( self, *args, **kw ):
        super().save( *args, **kw )
