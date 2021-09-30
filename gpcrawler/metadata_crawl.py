"""metadata_crawl.py is a script to crawl Google Play for app metadata.

usage: metadata_crawl.py [-h] --input_apps INPUT_APPS --country COUNTRY
                         --output_directory_root OUTPUT_DIRECTORY_ROOT
                         [--num_workers NUM_WORKERS] [--proxy PROXY]
                         [--random] [--full_metadata]

Crawl Google Play for app metadata.

optional arguments:
  -h, --help            show this help message and exit
  --input_apps INPUT_APPS, -i INPUT_APPS
                        input file containing one app id per line
  --country COUNTRY, -c COUNTRY
                        two-letter country code
  --output_directory_root OUTPUT_DIRECTORY_ROOT, -o OUTPUT_DIRECTORY_ROOT
                        root folder for output files
  --num_workers NUM_WORKERS, -n NUM_WORKERS
                        number of worker threads
  --proxy PROXY, -p PROXY
                        HTTP(S) proxy (IP:PORT)
  --random, -r          randomize crawl order of apps
  --full_metadata, -f   save the full metadata

The input file should contain one application ID per line. Duplicate app ids
and comments (lines starting with '#' after stripping surrounding whitespace)
are ignored.

The program creates the output directory
    {OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}
and the output files:
        {OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}/log.txt
        {OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}/metadata.csv
Check log.txt for any program error messages.
The program exits before creating metadata.csv if input is invalid.

Metadata requests are logged to log.txt
    (error message on failure or the Google Play site location on success).
The site location can confirm if a proxy is working correctly.

By default, metadata.csv contains the following column headers:
        appId,version,updated,released,downloadLink,downloadLinkEnabled

If the --full-metadata flag is enabled,
metadata.csv contains the following column headers:
        appId,url,siteLocation,siteLanguage,title,description,
        summary,installs,numInstalls,minInstalls,score,ratings,
        reviews,histogram,price,free,currency,offersIAP,size,
        androidVersion,androidVersionText,developer,developerId,
        developerEmail,developerWebsite,developerAddress,privacyPolicy,
        developerInternalID,genre,genreId,contentRating,
        contentRatingDescription,adSupported,containsAds,
        released,updated,version,recentChanges,comments,
        similarURL,downloadLink,downloadLinkEnabled
"""

import argparse
import os
import os.path
from queue import Queue
from random import shuffle
from threading import Thread
from time import localtime, strftime
from typing import Any, Dict, List, Optional

import pandas as pd

from mpyscraper import GooglePlayScraperException, details


def get_metadata(queues: Dict[str, Queue], save_full: bool,
                 proxy: Optional[str]) -> None:
    """Get metadata for the input apps and save the response.

    Args:
        queues: dict containing the "app", "log" and "metadata" queues
            {"app":INPUT_APPS, "log":OUTPUT_LOGS, "metadata":OUTPUT_METADATA}
        save_full: bool, if the full metadata should be saved
        proxy: string with format "ip:port" if using a proxy, else None
    """
    def try_metadata(app: str, retry: bool = False) -> bool:
        """Make metadata requests and retry failures.

        Args:
            app: Google Play application ID
            retry: if this request is a retry
        Returns:
            True if request succeeded or if request is a retry (done with app)
            False otherwise (need to retry app)
        """
        try:
            metadata = details(app, proxy=proxy)
            if save_full:
                # We do not need to save the following fields: remove them
                # from the metadata.
                remove = ["descriptionHTML", "summaryHTML",
                          "recentChangesHTML", "screenshots", "icon",
                          "headerImage", "video", "videoImage"]
                for key in remove:
                    metadata.pop(key)
                # Push metadata to output queue.
                queues["metadata"].put(metadata)
            else:
                # Save a reduced copy of the metadata.
                reduced_metadata = {
                    "app": app,
                    "version": metadata["version"],
                    "updated": metadata["updated"],
                    "released": metadata["released"],
                    "dl": bool(metadata["downloadLink"]),
                    "dle": bool(metadata["downloadLinkEnabled"])
                }
                if reduced_metadata["released"]:
                    # The released date has format 'Oct 9, 2012'.
                    # Format as a string (to escape comma) for the CSV output.
                    metadata_str = "{app},{version},{updated},\"{released}\","\
                                   "{dl},{dle}\n"
                else:
                    metadata_str = "{app},{version},{updated},{released},"\
                                   "{dl},{dle}\n"
                # Push metadata to output queue.
                queues["metadata"].put(metadata_str.format(**reduced_metadata))
            # Success! Log the app and site location.
            queues["log"].put("{0}: siteLocation {1}, written\n".
                              format(app, metadata["siteLocation"]))
        except GooglePlayScraperException as e:
            # The request returned an HTTP error (e.g. 404).
            if not retry:
                # First request: return false to retry and confirm the error.
                return False
            queues["log"].put("{0}: {1}\n".format(app, e))
        except (ValueError, OSError) as e:
            # Catch other request errors (e.g. unreachable proxy).
            print("{0}: unknown failure {1}".format(app, e))
            queues["app"].put(app)
        # Done with this app: the request succeeded or has been retried.
        return True

    # Process apps from the input queue.
    while True:
        app = queues["app"].get()
        if app is None:
            break
        # Request metadata. Retry once if the first request failed.
        success = try_metadata(app)
        if not success:
            try_metadata(app, retry=True)
        queues["app"].task_done()


def logging(filename: str, queue: Queue) -> None:
    """Log crawl progress to file.

    Args:
        filename: output file
        queue: Queue of messages to write to the output file
    """
    while True:
        log = queue.get()
        if log == -1:
            break
        with open(filename, "a") as f:
            f.write(log)
        queue.task_done()


def write_full(filename: str, queue: Queue) -> None:
    """Write the full metadata to a csv.

    Args:
        filename: output .csv file
        queue: Queue of app metadata (a dictionary)
    """
    headers = []
    while True:
        metadata = queue.get()
        if metadata == -1:
            break
        try:
            app_df = pd.DataFrame.from_records([metadata], index="appId")
            if headers:
                # Headers exist: append the metadata row to the csv.
                app_df[headers].to_csv(filename, mode='a', header=False)
            else:
                # First row: write the headers and metadata row to the csv.
                headers = list(app_df.columns)
                app_df.to_csv(filename)
        except (KeyError, OSError) as e:
            print("Error writing metadata to file:", e)
        queue.task_done()


def read_apps(filename: str) -> List[str]:
    """Read the apps from the file, skipping duplicate apps and comments (#).

    Args:
        filename: input file containing one app id per line
    Returns:
        list of app ids
    """
    unique = set()
    apps = []
    with open(filename, "r") as f:
        for line in f:
            app = line.strip()
            # Skip comments and duplicates
            if app.startswith("#") or app in unique:
                continue
            unique.add(app)
            apps.append(app)
    return apps


def cmd_args() -> Dict[str, Any]:
    """Parse command line arguments.

    Returns:
        dict of arguments
    """
    description = "Crawl Google Play for app metadata."
    epilog = (
        "The input file should contain one application ID per line.\n"
        "Duplicate app ids and comments (lines starting with '#' after "
        "stripping surrounding whitespace) are ignored.\n\n"
        "The program creates the output directory "
        "{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}\n"
        "and the output files:\n\t"
        "{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}/log.txt\n\t"
        "{OUTPUT_DIRECTORY_ROOT}/{COUNTRY}/{CURRENT_TIMESTAMP}/metadata.csv\n"
        "Check log.txt for any program error messages. "
        "The program exits before creating metadata.csv if input is invalid.\n"
        "\nMetadata requests are logged to log.txt (error message "
        "on failure or the Google Play site location on success).\n"
        "The site location can confirm if a proxy is working correctly.\n\n"
        "By default, metadata.csv contains the following column headers:\n"
        "\tappId,version,updated,released,downloadLink,downloadLinkEnabled\n\n"
        "If the --full-metadata flag is enabled, "
        "metadata.csv contains the following column headers:\n"
        "\tappId,url,siteLocation,siteLanguage,title,description,\n"
        "\tsummary,installs,numInstalls,minInstalls,score,ratings,\n"
        "\treviews,histogram,price,free,currency,offersIAP,size,\n"
        "\tandroidVersion,androidVersionText,developer,developerId,\n"
        "\tdeveloperEmail,developerWebsite,developerAddress,privacyPolicy,\n"
        "\tdeveloperInternalID,genre,genreId,contentRating,\n"
        "\tcontentRatingDescription,adSupported,containsAds,\n"
        "\treleased,updated,version,recentChanges,comments,\n"
        "\tsimilarURL,downloadLink,downloadLinkEnabled\n"
    )
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog
    )
    parser.add_argument("--input_apps", "-i", required=True,
                        help="input file containing one app id per line")
    parser.add_argument("--country", "-c", required=True,
                        help="two-letter country code")
    parser.add_argument("--output_directory_root", "-o", required=True,
                        help="root folder for output files")
    parser.add_argument("--num_workers", "-n", type=int, default=10,
                        help="number of worker threads")
    parser.add_argument("--proxy", "-p", default=None,
                        help="HTTP(S) proxy (IP:PORT)")
    parser.add_argument("--random", "-r", action='store_true',
                        help="randomize crawl order of apps")
    parser.add_argument("--full_metadata", "-f", action='store_true',
                        help="save the full metadata")
    return parser.parse_args()


def main() -> None:
    """Crawl Google Play for app metadata."""
    args = cmd_args()

    # Make output directory and log crawl information.
    start_time = strftime("%Y-%m-%d_%H-%M-%S", localtime())
    output_directory = os.path.join(args.output_directory_root, args.country,
                                    start_time)
    log_file = os.path.join(output_directory, "log.txt")
    meta_file = os.path.join(output_directory, "metadata.csv")
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    message = "Input: {0}\nOutput: {1}\nLog file: {2}\nStarting crawl: {3}".\
              format(args.input_apps, meta_file, log_file, start_time)
    print(message)
    with open(log_file, "a") as f:
        f.write("{0}\n".format(message))

    if not os.path.exists(args.input_apps):
        print("Input apps file does not exist: ending crawl")
        with open(log_file, "a") as f:
            f.write("Input apps file does not exist: ending crawl\n")
        return

    # Init thread-safe queues for input apps, logging, and output metadata.
    queues = {
        "app": Queue(),
        "log": Queue(),
        "metadata": Queue()
    }

    # Read input apps and add them to the queue.
    apps = read_apps(args.input_apps)

    if args.random:
        shuffle(apps)

    for app in apps:
        queues["app"].put(app)

    # Start threads to make metadata requests.
    for _ in range(0, args.num_workers):
        thread = Thread(target=get_metadata,
                        args=(queues, args.full_metadata, args.proxy),
                        daemon=True)
        thread.start()
    log_thread = Thread(target=logging, args=(log_file, queues["log"]),
                        daemon=True)
    log_thread.start()
    if args.full_metadata:
        meta_thread = Thread(target=write_full,
                             args=(meta_file, queues["metadata"]),
                             daemon=True)
        meta_thread.start()
    else:
        with open(meta_file, "a") as f:
            f.write("appId,version,updated,released,"
                    "downloadLink,downloadLinkEnabled\n")
        meta_thread = Thread(target=logging,
                             args=(meta_file, queues["metadata"]),
                             daemon=True)
        meta_thread.start()

    # Wait for requests and logging to finish.
    queues["app"].join()

    for _ in range(0, args.num_workers):
        queues["app"].put(None)

    queues["log"].join()
    queues["log"].put(-1)

    queues["metadata"].join()
    queues["metadata"].put(-1)

    finish_time = strftime("%Y-%m-%d_%H-%M-%S", localtime())
    print("Finished crawl:", finish_time)
    with open(log_file, "a") as f:
        f.write("Finished crawl: {0}\n".format(finish_time))


if __name__ == '__main__':
    main()
