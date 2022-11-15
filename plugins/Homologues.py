import os
import errno
import logging
import subprocess
from addict import Dict
from yapsy.IPlugin import IPlugin
from modules.common.Utils import Utils
from modules.common import create_folder
from modules.common.DownloadResource import DownloadResource
from manifest import ManifestResource, ManifestStatus, get_manifest_service

logger = logging.getLogger(__name__)


class Homologues(IPlugin):
    """
    Class to download resources from Ensembl FTP for use in ETL target step (specifically to generate homologues).

    Takes the `homology` section of the `config.yaml` file as an input which has the format:

    ```
      gs_output_dir: xxxx
      release: 104
      resources:
        - 'caenorhabditis_elegans'
        ... many more species
        - 'canis_lupus_familiaris'
    ```
    Each resource needs two files downloaded:
        Compara.104.ncrna_default.homologies.tsv.gz        13-Mar-2021 21:08           126747131
        Compara.104.protein_default.homologies.tsv.gz      13-Mar-2021 18:48           119129028

    These are saved as  `<release>-<species>-[protein|rna].tsv.gz

    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.step_name = "Homologues"

    @staticmethod
    def download_species(uri, release, staging, download, species: str) -> ManifestResource:
        """
        Download protein homology for species and suffix if file does not already exist.

        Most entries do not require suffix to be provided, but some such as sus_scrofa_usmarc have no standard ftp
        entries requiring a custom suffix.
        """
        protein_uri = f"{uri}{species}/{species}.json"
        # Create the resource info.
        resource_stage = Dict()
        resource_stage.uri = protein_uri
        resource_stage.output_filename = f'{release}-{species}.json'
        resource_stage.output_dir = staging
        return download.ftp_download(resource_stage)


    def extract_fields_from_json(self, input_file, conf, output, jq_cmd) -> str:
        """
        Extract the data defined by the JQ filter from the given input file

        :param input_file: source file to extract data from
        :param conf: configuration object
        :param output: information on where the output result should be place
        :param jq_cmd: JQ command for extracting data from the input file
        :return: destination file path of the extracted data content
        """
        head, tail = os.path.split(input_file)
        output_file = os.path.join(output.prod_dir, conf.path, str(conf.release), tail.replace('json', 'tsv'))
        self._logger.info(f"Extracting id and name from: {input_file}")
        with open(output_file, "ba+") as tsv:
            try:
                jqp = subprocess.Popen(f"{jq_cmd} '{conf.jq}' {input_file}",
                                       stdout=subprocess.PIPE,
                                       shell=True)
                tsv.write(jqp.stdout.read())
            except OSError as e:
                if e.errno == errno.ENOENT:
                    # handle file not found error.
                    self._logger.error(e)
                else:
                    # Something else went wrong
                    raise
        return output_file

    def process(self, conf, output, cmd_conf):
        """
        Homologues pipeline step implementation

        :param conf: step configuration object
        :param output: output information object for results from this step
        :param cmd_conf: command line configuration object for external tools
        """
        self._logger.info("[STEP] BEGIN, Homologues")
        download = DownloadResource(output.staging_dir)
        uri_release = conf.uri.replace("{release}", str(conf.release))
        create_folder(os.path.join(output.prod_dir, conf.path, str(conf.release)))
        jq_cmd = Utils.check_path_command("jq", cmd_conf.jq)
        manifest_step = get_manifest_service().get_step(self.step_name)
        for species in conf.resources:
            self._logger.debug(f'Downloading files for {species}')
            download_manifest = self.download_species(uri_release, conf.release, output.staging_dir, download, species)
            download_manifest.path_destination = \
                self.extract_fields_from_json(download_manifest.path_destination, conf, output, jq_cmd)
            self._logger.debug(
                f"Homologue '{species}' data download manifest destination path"
                f" set to '{download_manifest.path_destination}',"
                f" as final recipient for the sub-dataset"
            )
            download_manifest.msg_completion = \
                f"Homologue '{species}' data"
            download_manifest.status_completion = ManifestStatus.COMPLETED
            manifest_step.resources.append(download_manifest)
        get_manifest_service().compute_checksums(manifest_step.resources)
        manifest_step.status_completion = ManifestStatus.COMPLETED
        manifest_step.msg_completion = "The step has completed its execution"
        self._logger.info("[STEP] END, Homologues")
