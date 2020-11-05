# -*- coding: utf-8 -*-

"""Console script for chibi_gob_mx_elasticsearch."""
import random
import argparse
import sys
import argparse
import sys
from chibi.config import basic_config
from chibi.file import Chibi_path
from chibi.config import configuration
from chibi_gob_mx.open_data import Open_data
from chibi_gob_mx.open_data.data_set import Data_set as Data_set_site
from chibi_gob_mx_elasticsearch.models import Dataset, Resource
from elasticsearch_dsl import Q
import logging
import time


logger = logging.getLogger( 'chibi_gob_mx_elasticsearch.cli' )


parser = argparse.ArgumentParser(
    description=(
        "descargar datos de articulos de "
        "https://datos.gob.mx hacia elasticsearhc" ),
    fromfile_prefix_chars='@'
)

parser.add_argument(
    "--log_level", dest="log_level", default="INFO",
    help="nivel de log",
)

parser.add_argument(
    "--reversed", '-r', dest="reversed", action="store_true",
    help="escanea en alrevez", )

parser.add_argument(
    "--random", dest="random", action="store_true",
    help="escanea aleatoriamente", )

parser.add_argument(
    "--resources", dest="do_resources", action="store_true",
    help="formateara los resources de los dataset", )

parser.add_argument(
    "--scan_no_ok", dest="scan_no_ok", action="store_true",
    help="reescanea los que no se encontraron", )

parser.add_argument(
    "--config_site", type=Chibi_path, dest="config_site",
    help="python, yaml o json archivo de config"
)


def prepare():
    #Dataset._index.delete()
    wait = False
    if not Dataset._index.exists():
        wait = True
        logger.info( 'creando el indice para dataset' )
        Dataset.init()
    if not Resource._index.exists():
        wait = True
        logger.info( 'creando el indice para resources' )
        Resource.init()

    if wait:
        time.sleep( 10 )


def main():
    args = parser.parse_args()
    basic_config( args.log_level )
    if args.config_site:
        load_config( args.config_site )

    prepare()
    data = Open_data()

    if args.do_resources:
        resources_count = 0
        for dataset in Dataset.search().scan():
            resources_count += len( dataset.resources )
            for resource in dataset.resources:
                if not Resource.url_is_scaned( resource.download_link ):
                    model = Resource(
                        title=resource.title, description=resource.description,
                        url=resource.download_link, tags=dataset.tags,
                        metadata=dataset.metadata )
                    model.save()
        logger.info( f"count dataset: {Dataset.search().count()}" )
        logger.info( f"count resources: {Resource.search().count()}" )
        logger.info( f"total resources: {resources_count}" )
    elif args.scan_no_ok:
        configuration.loggers.elasticsearch.level = 'INFO'
        no_ok = ~Q( 'term', status='ok' )
        for model in Dataset.search().filter( no_ok ).scan():
            try:
                if model.status == 'no_ok':
                    dataset = Data_set_site( model.url )
                    model.resources = dataset.info.resources
                    model.metadata = dataset.metadata
                    model.update(
                        metadata=dataset.metadata, **dataset.info,
                        status='missing activity' )
                elif model.status == 'missing activity':
                    model.activity = dataset.info.activity.info
                    model.update(
                        activity=dataset.activity.info, status='ok' )
                else:
                    logger.warning(
                        'intentando procesar un status '
                        'desconocido "{model.status}"' )
            except KeyboardInterrupt:
                raise
            except:
                pass
    else:
        if args.random:
            pages = list( data.pages )
            random.shuffle( pages )
            for page in pages:
                for dataset in page.datasets:
                    if not Dataset.url_is_scaned( dataset.url ):
                        try:
                            model = Dataset(
                                url=dataset.url,
                                metadata=dataset.metadata,
                                activity=dataset.activity.info,
                                **dataset.info, status='ok' )
                            model.save()
                            logger.info( f'guardado {dataset.url}' )
                        except Exception as e:
                            model = Dataset( url=dataset.url, status='no_ok' )
                            model.save()
                            logger.exception( f'saltando {dataset.url}' )
                    else:
                        logger.error( f'encontrado {dataset.url}' )
        else:
            for dataset in data:
                model = Dataset.url_is_scaned( dataset.url )
                if not model:
                    try:
                        model = Dataset(
                            url=dataset.url,
                            metadata=dataset.metadata,
                            activity=dataset.activity.info,
                            **dataset.info, status='ok' )
                        model.save()
                    except Exception as e:
                        model = Dataset( url=dataset.url, status='no_ok' )
                        model.save()
                        logger.error( f'saltando {dataset.url}' )
                else:
                    logger.error( f'encontrado {dataset.url}' )
                    continue
                    model.resources = dataset.info.resources
                    model.save()

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
