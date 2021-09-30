"""Download an app from Google Play."""

import logging
import os
import os.path
from typing import Optional

from .playstore.playstore import Playstore

# Logging configuration.
logger = logging.getLogger(__name__)

# Default credentials file location.
DEFAULT_CREDENTIALS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "credentials.json")


class DownloadException(Exception):
    """Exception that occurs during app download."""


def download(package: str,
             out: str,
             credentials: Optional[str] = None,
             proxy: Optional[str] = None,
             tag: Optional[str] = None,
             blobs: bool = False) -> None:
    """Download an app from Google Play.

    Args:
        package: Google Play application ID
        out: directory to save downloaded .apk
        credentials: filename for credentials
        proxy: string with format "ip:port" if using a proxy
        tag: optional string to prepend to the .apk filename
        blobs: boolean, True if additional .obb files should be downloaded

    Raises:
        DownloadException if the app failed to download.
    """
    try:
        if not credentials:
            credentials = DEFAULT_CREDENTIALS

        # Make sure to use a valid json file with the credentials.
        api = Playstore(credentials.strip(" '\""))

        try:
            # Get the application details.
            app = api.app_details(package.strip(" '\""), proxy=proxy).docV2
        except AttributeError as e:
            logger.critical(
                "Error when downloading '%s': unable to get app's details",
                package.strip(" '\"")
            )
            raise DownloadException(e)

        details = {
            "package_name": app.docid,
            "title": app.title,
            "creator": app.creator,
        }

        # The downloaded apk will be saved in the location chosen by the user.
        downloaded_apk_file_path = os.path.join(
            os.path.abspath(out.strip(" '\"")),
            "{}.apk".format(details["package_name"])
        )

        # If it doesn't already exist,
        # create the directory where to save the downloaded apk.
        apk_directory = os.path.dirname(downloaded_apk_file_path)
        if not os.path.isdir(apk_directory):
            os.makedirs(apk_directory, exist_ok=True)

        if tag and tag.strip(" '\""):
            # If provided, prepend the specified tag to the file name.
            downloaded_apk_file_path = os.path.join(
                apk_directory, "[{0}] {1}".format(
                    tag.strip(" '\""),
                    os.path.basename(downloaded_apk_file_path)
                ),
            )

        # The download of the additional .obb files is optional.
        success = api.download(
            details["package_name"],
            downloaded_apk_file_path,
            download_obb=blobs,
            proxy=proxy
        )

    except Exception as e:
        raise DownloadException(e)
