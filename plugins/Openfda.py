from yapsy.IPlugin import IPlugin
from modules.common.Downloads import Downloads
from modules.common import create_output_dir
from plugins.helpers.OpenfdaHelper import OpenfdaHelper
import logging
import multiprocessing as mp
import tqdm
import json
import os

logger = logging.getLogger(__name__)

"""
This module gathers all data related to OpenFDA FAERS database, with a focus on Drug Events.

In addition, a collection of blacklisted events is downloaded for later use in the ETL backend pipeline.
"""

class Openfda(IPlugin):
    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def _download_selected_event_files(self, repo_metadata, output):
        downloaded_files = dict()
        # Body
        if repo_metadata:
            logger.info("OpenFDA FAERs metadata received")
            fda_output = create_output_dir(os.path.join(output.prod_dir,"fda-inputs"))
            fda = OpenfdaHelper(fda_output)
            # Parallel data gathering
            logger.info("Prepare download pool of {} processes".format(mp.cpu_count()))
            download_pool = mp.Pool(mp.cpu_count())
            logger.info(mp.current_process())
            try:
                for _ in tqdm.tqdm(download_pool.map(fda._do_download_openfda_event_file,
                                                 repo_metadata['results']['drug']['event']['partitions']), total=len(repo_metadata['results']['drug']['event']['partitions'])):
                    logger.info('\rdone {0:%}'.format(_ / len(repo_metadata['results']['drug']['event']['partitions'])))
            except Exception as e:
                logger.info("Something went wrong: " + str(e))
        return downloaded_files

    def _download_openfda_faers(self, resource, output):
        logger.info("OpenFDA available files download, URI '{}' --- START ---".format(resource.uri))
        downloaded_files = dict()
        logger.info("Download OpenFDA FAERS repository metadata")
        download = Downloads.dowload_staging_http(output.staging_dir, resource)
        repo_metadata = {}
        with open(download, 'r') as f:
            repo_metadata = json.load(f)
        downloaded_event_files = self._download_selected_event_files(repo_metadata, output)
        downloaded_files.update(downloaded_event_files)
        return downloaded_files

    def process(self, conf, output, cmd_conf):
        self._logger.info("Openfda step")
        Downloads(output.prod_dir).exec(conf)

        self._download_openfda_faers(conf.etl.downloads, output)