import datetime
import sys
from pathlib import Path

from google import auth
from google.auth import exceptions as auth_exceptions
from google.cloud import exceptions as cloud_exceptions
from google.cloud import storage
from loguru import logger

from platform_input_support.config import config

__all__ = ['GoogleHelperError', 'google']


class GoogleHelperError(Exception):
    """Google Helper Exception class."""


class GoogleHelper:
    def __init__(self):
        try:
            _, project_id = auth.default()
            logger.debug(f'gcp authenticated on project {project_id}')
        except auth_exceptions.DefaultCredentialsError as e:
            logger.critical(f'error : {e}')
            sys.exit(1)

        self.client = storage.Client()

        # check if the configured bucket exists
        try:
            if config.gcp_bucket_path is None:
                logger.critical('missing setting: gcp_bucket_path')
                sys.exit(1)

            if not self.bucket_exists(config.gcp_bucket_path):
                logger.critical(f'gcp bucket does not exist: {config.gcp_bucket_path}')
                sys.exit(1)
        except GoogleHelperError as e:
            logger.critical(f'error checking gcp bucket: {e}')
            sys.exit(1)

    @staticmethod
    def _parse_url(url: str) -> tuple[str, str | None]:
        url_parts = url.replace('gs://', '').split('/', 1)
        bucket_name = url_parts[0]
        file_path = url_parts[1] if len(url_parts) > 1 else None

        return bucket_name, file_path

    def bucket_exists(self, url: str) -> bool:
        bucket_name, _ = self._parse_url(url)

        logger.debug(f'checking if bucket exists: {bucket_name}')

        try:
            self.client.get_bucket(bucket_name)
            return True
        except cloud_exceptions.NotFound:
            logger.debug(f'bucket not found: {bucket_name}')
        except cloud_exceptions.GoogleCloudError as e:
            logger.error(f'error checking bucket: {e}')
        return False

    def stat(self, url: str) -> bool:
        bucket_name, file_path = self._parse_url(url)

        logger.debug(f'statting url: {url}')

        try:
            bucket = self.client.get_bucket(bucket_name)
            return bucket.blob(file_path).exists()
        except cloud_exceptions.NotFound:
            logger.debug(f'file not found: {url}')
        except cloud_exceptions.GoogleCloudError as e:
            logger.error(f'error checking gs object: {e}')
        return False

    def download(self, url: str, destination: Path):
        bucket_name, file_path = self._parse_url(url)

        try:
            bucket = self.client.get_bucket(bucket_name)
            blob = bucket.blob(file_path)
            blob.download_to_filename(destination)

            logger.debug(f'downloaded {url} to {destination}')
        except cloud_exceptions.NotFound:
            logger.error(f'bucket or file not found: {url}')
        except cloud_exceptions.GoogleCloudError as e:
            logger.error(f'error downloading file: {e}')

    def upload(self, source: str, destination: str):
        bucket_name, file_path = self._parse_url(destination)

        try:
            bucket = self.client.get_bucket(bucket_name)
            blob = bucket.blob(file_path)
            blob.upload_from_filename(source)

            logger.debug(f'file uploaded: {destination}')
        except cloud_exceptions.NotFound:
            logger.error(f'bucket not found: {bucket_name}')
        except cloud_exceptions.GoogleCloudError as e:
            logger.error(f'error uploading file: {e}')

    def list(self, url: str, include: str | None = None, exclude: str | None = None) -> list[str]:
        bucket_name, prefix = self._parse_url(url)
        file_list = []

        try:
            bucket = self.client.get_bucket(bucket_name)
            file_list = list(bucket.list_blobs(prefix=prefix))
        except cloud_exceptions.NotFound:
            logger.error(f'bucket not found: {bucket_name}')
            return []
        except cloud_exceptions.GoogleCloudError as e:
            logger.error(f'error listing gs objects: {e}')
            return []

        if include is not None:
            file_list = [blob for blob in file_list if include in blob.name]
        elif exclude is not None:
            file_list = [blob for blob in file_list if exclude not in blob.name]

        return [f'gs://{bucket_name}/{blob.name}' for blob in file_list]

    def get_creation_date(self, url: str) -> datetime.datetime | None:
        bucket_name, file_path = self._parse_url(url)

        try:
            bucket = self.client.get_bucket(bucket_name)
            blob = bucket.blob(file_path)
            blob.reload()
            return blob.time_created
        except cloud_exceptions.NotFound:
            logger.error(f'bucket or file not found: {url}')
        except cloud_exceptions.GoogleCloudError as e:
            logger.error(f'error getting creation date: {e}')
        return None


google = GoogleHelper()
