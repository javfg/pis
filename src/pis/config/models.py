"""This module contains the models for the configuration settings."""

from pathlib import Path
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel

LOG_LEVELS = Literal['TRACE', 'DEBUG', 'INFO', 'SUCCESS', 'WARNING', 'ERROR', 'CRITICAL']
"""The log levels."""


def remote_uri_is_valid(uri: str) -> str:
    """Validate a remote URI.

    :param uri: The URI to validate.
    :type uri: str
    :return: The URI if it is valid.
    :rtype: str
    :raises AssertionError: If the URI does not contain a protocol.
    """
    assert '://' in uri, 'Remote URI must contain a protocol.'
    return uri


class BaseTaskDefinition(BaseModel, extra='allow'):
    """Base Task definition model.

    This model is the base on which :class:`pis.config.models.TaskDefinition`
    and :class:`pis.config.models.PretaskDefinition` are built. Specific
    tasks or pretasks subclass those to add custom attributes.
    """

    name: str


class TaskDefinition(BaseTaskDefinition, BaseModel, extra='allow'):
    """Task definition model.

    This model is used to define the tasks to be run by the application. It includes
    the destination as a required field, as the tasks are expected to create a resource.

    .. note:: PIS is not intended to be used by chaining tasks, as there is no way to
        generate a dependency graph, all tasks will be sent to the worker pool at the same
        time.
    """

    destination: Path


class PretaskDefinition(BaseTaskDefinition, BaseModel, extra='allow'):
    """Pretask definition model."""


class EnvSettings(BaseModel):
    """Environment settings model."""

    step: str | None = None
    config_file: Path | None = None
    work_dir: Path | None = None
    remote_uri: Annotated[str, AfterValidator(remote_uri_is_valid)] | None = None
    pool: int | None = None
    log_level: LOG_LEVELS | None = None


class CliSettings(BaseModel):
    """CLI settings model."""

    step: str = ''
    config_file: Path | None = None
    work_dir: Path | None = None
    remote_uri: Annotated[str, AfterValidator(remote_uri_is_valid)] | None = None
    pool: int | None = None
    log_level: LOG_LEVELS | None = None


class YamlSettings(BaseModel):
    """YAML settings model."""

    work_dir: Path | None = None
    remote_uri: Annotated[str, AfterValidator(remote_uri_is_valid)] | None = None
    pool: int | None = None
    log_level: LOG_LEVELS | None = None


class Settings(BaseModel):
    """Settings model.

    This model is used to define the settings for the application.

    It is constructed by merging the settings from the environment, CLI, and YAML
    configuration file. The fields are defined in order of precedence, with the
    environment settings taking precedence over the CLI settings, which take
    precedence over the YAML settings. All fields have defaults so that any field
    left unset after the merge will have a value.

    The :attr:`step` field is required, but has an empty string as a default value,
    so objects can be created without setting it. Its validation is handled by
    Config class.
    """

    step: str = ''
    """The step to run. This is a required field, and its validation is handled by
    :func:`pis.config.config.Config._validate_step`."""

    config_file: Path = Path('config.yaml')

    work_dir: Path = Path('./output')
    """The local working directory path. This is where resources will be downloaded
    and the manifest and logs will be written to before upload to the GCS bucket."""

    remote_uri: Annotated[str, AfterValidator(remote_uri_is_valid)] | None = None
    """The remote working URI. If present, this is where resources, logs and manifest
    will be uploaded to."""

    pool: int = 5
    """The number of workers in the pool where tasks will run."""

    log_level: LOG_LEVELS = 'INFO'
    """See :data:`LOG_LEVELS`."""

    def merge_model(self, incoming: BaseModel):
        """Merge the fields of another model into this model.

        :param incoming: The incoming model.
        :type incoming: BaseModel
        """
        for field_name in self.model_fields:
            if field_name in incoming.model_fields_set:
                field_value = getattr(incoming, field_name)
                setattr(self, field_name, field_value)
