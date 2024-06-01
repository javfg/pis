from loguru import logger
from yapsy.IPlugin import IPlugin

from platform_input_support.manifest import ManifestStatus, get_manifest_service
from platform_input_support.modules.common.downloads import Downloads


class GO(IPlugin):
    """GO data collection step."""

    def __init__(self):
        """Go class constructor."""
        super().__init__()
        self.step_name = 'GO'

    def process(self, conf, output, cmd_conf=None):
        """GO data collection pipeline step implementation.

        :param conf: step configuration object
        :param output: data collection destination information object
        :param cmd_conf: NOT USED
        """
        logger.info('[STEP] BEGIN, GO')
        manifest_step = get_manifest_service().get_step(self.step_name)
        manifest_step.resources.extend(Downloads(output.prod_dir).exec(conf))
        get_manifest_service().compute_checksums(manifest_step.resources)
        if not get_manifest_service().are_all_resources_complete(manifest_step.resources):
            manifest_step.status_completion = ManifestStatus.FAILED
            manifest_step.msg_completion = 'COULD NOT retrieve all the resources'
        # TODO - Validation
        if manifest_step.status_completion != ManifestStatus.FAILED:
            manifest_step.status_completion = ManifestStatus.COMPLETED
            manifest_step.msg_completion = 'The step has completed its execution'
        logger.info('[STEP] END, GO')