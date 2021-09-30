"""crawler.py downloads the input apps from the Google Play Store.

usage: crawler.py [-h] -o OUTPUT_DIRECTORY_ROOT -i INPUT_APPS [INPUT_APPS ...]
                  -c COUNTRY [--credentials CREDENTIALS] [-p PROXY]
                  [-r] [-l NUM_REQUESTS NUM_SECONDS]

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_DIRECTORY_ROOT, --out OUTPUT_DIRECTORY_ROOT
                        directory to save downloaded .apk files
  -i INPUT_APPS [INPUT_APPS ...], --input_apps INPUT_APPS [INPUT_APPS ...]
                        app IDs OR the input filename containing one app / line
  -c COUNTRY, --country COUNTRY
                        country code
  --credentials CREDENTIALS
                        Google Play credentials file
  -p PROXY, --proxy PROXY
                        proxy (IP:PORT)
  -r, --random          enable to crawl apps in random order
  -l NUM_REQUESTS NUM_SECONDS, --limit NUM_REQUESTS NUM_SECONDS
                        rate limit: # of requests per # of seconds
"""

import datetime
import logging
import os
import os.path
import re
import time
from argparse import ArgumentParser, Namespace
from json import loads, JSONDecodeError
from queue import Queue
from random import shuffle
from shutil import rmtree
from time import sleep
from typing import List, Optional, Tuple
from urllib.request import ProxyHandler, build_opener, urlopen

from ratelimit import limits, sleep_and_retry

from PlaystoreDownloader.download import download, DownloadException

# Logging configuration.
logger = logging.getLogger(__name__)

ERRORS = {
    "Item not found": 1,
    "Your device is not compatible with this item": 2,
    "The Play Store application on your device is outdated": 4,
    "Google Play purchases are not supported in your country": 5,
    "This item is not available on your service provider": 8,
    "Rate limit triggered": 14
}

DOWNLOAD_QUEUE = Queue()

KEY = re.compile(r"(ds:.*?)'")
VALUE = re.compile(r"data:([\s\S]*?), sideChannel: \{\}\}\);<\/")
SCRIPT = re.compile(r"AF_initDataCallback[\s\S]*?<\/script")


def cmd_args() -> Namespace:
    """Parse the command line arguments.

    Returns:
        Parsed arguments
    """
    parser = ArgumentParser(
        description="Download the input apps from Google Play.")
    parser.add_argument(
        "-o",
        "--output_directory_root",
        type=str,
        required=True,
        help="directory to save downloaded .apk files")
    parser.add_argument(
        "-i",
        "--input_apps",
        nargs="+",
        required=True,
        help="app IDs OR the input filename containing one app per line")
    parser.add_argument(
        "-c",
        "--country",
        required=True,
        help="country code")
    parser.add_argument(
        "--credentials",
        default=None,
        help="Google Play credentials file"
    )
    parser.add_argument(
        "-p",
        "--proxy",
        default=None,
        help="proxy (IP:PORT)")
    parser.add_argument(
        "-r",
        "--random",
        action="store_true",
        help="enable to crawl apps in random order")
    parser.add_argument(
        "-l",
        "--limit",
        nargs=2,
        default=[1, 1],
        type=int,
        help="rate limit: # of requests per # of seconds",
        metavar=("NUM_REQUESTS", "NUM_SECONDS"))
    return parser.parse_args()


def google_location(proxy: Optional[str] = None) -> str:
    """Scrape the Google Play store location from the home page.

    Args:
        proxy: string with format "ip:port" if using a proxy
    Returns:
        country string or "Error getting location"
    """
    url = "https://play.google.com/store/apps"
    try:
        if proxy:
            handler = ProxyHandler(proxies={"http": proxy, "https": proxy})
            opener = build_opener(handler)
            resp = opener.open(url)
        else:
            resp = urlopen(url)
        dom = resp.read().decode()
        matches = SCRIPT.findall(dom)
        res = {}
        for match in matches:
            key_match = KEY.findall(match)
            value_match = VALUE.findall(match)
            if key_match and value_match:
                res[key_match[0]] = loads(value_match[0])
        location_key = max(res.keys(), key=lambda x: int(x.lstrip("ds:")))
        return res[location_key][4]
    except (KeyError, OSError, JSONDecodeError):
        return "Error getting location"


def execute(app: str,
            app_folder: str,
            failure_file: str,
            transient_file: str,
            credentials: str,
            is_retry: bool,
            previous: Optional[Tuple[int, str]] = None,
            proxy: Optional[str] = None) -> bool:
    """Download the app.

    Args:
        app: Google Play application ID
        app_folder: directory to download the app
        failure_file: filename to output confirmed errors
        transient_file: filename to output transient errors
        credentials: filename for credentials
        is_retry: boolean, True if this is a retry
        previous: (previous code, previous message) if this is a retry
        proxy: string with format "ip:port" if using a proxy

    Returns:
        True if app is finished, False if app needs to be retried
    """
    try:
        download(app, app_folder, credentials=credentials, proxy=proxy)
    except DownloadException as e:
        # The app failed to download.
        # Remove the created directory.
        if os.path.exists(app_folder):
            rmtree(app_folder)

        # The error is related to the config file: do not auto retry.
        if "configuration file" in str(e) or "credentials" in str(e):
            print(e)
            return False

        # check error
        error_code = 15
        for msg in ERRORS:
            if msg in str(e):
                error_code = ERRORS[msg]
                break

        # Errors 1, 2, 5, and 8 are assumed to be valid Google Play errors.
        # Others are transient errors.

        if error_code >= 10:
            # Log transient errors.
            logger.error("%s: %s", app, str(e))
            with open(transient_file, "a") as f:
                f.write("{0}: {1}\n".format(app, str(e)))

        # Sleep if rate limit is triggered.
        if error_code == 100:
            sleep(30)

        if is_retry:
            # Log the latest valid error on retry.
            previous_code, previous_message = previous
            # If the second error is valid, take the second error
            # (first error can be valid or transient).
            if error_code < 10:
                with open(failure_file, "a") as f:
                    f.write("{0}: {1}\n".format(app, str(e).split(": ")[1]))
                return True
            # If the first error is valid and second error transient,
            # take the first error.
            if previous_code < 10:
                with open(failure_file, "a") as f:
                    f.write("{0}: {1}\n".format(
                        app, previous_message.split(": ")[1]))
                return True
            # If both errors are transient, consider the app unfinished.
            # Retry may occur manually.
            return False
        # Put the app back on the queue for retry (set to True) with the
        # first try error code and message.
        DOWNLOAD_QUEUE.put((app, True, (error_code, str(e))))
    else:
        # The app is finished (successful download).
        logger.info("%s: success", app)
        return True


def remove_finished_apps(apps: List[str], finished_file: str) -> List[str]:
    """Remove the finished apps from the app list.

    Args:
        apps: list of app IDs to crawl
        finished_file: file containing finished apps, one per line

    Returns:
        list of app IDs with finished apps removed
    """
    if os.path.exists(finished_file):
        with open(finished_file) as f:
            lines = [line.strip() for line in f]
        finished = set(filter(lambda line: line and line[0] != "#", lines))
        print_and_log("{0} in finished.txt".format(len(finished)))
        # Only keep input apps that have not been finished yet.
        apps = list(filter(lambda app: app not in finished, apps))
    return apps


def read_input_apps(apps: List[str]) -> List[str]:
    """Read input apps from a file or the command line.

    Args:
        apps: list of app IDs from the command line OR
              list of length 1 containing an input file with one app per line,
              e.g. [app.id.one, app.id.two], [app.id.one], [filename]
    Returns:
        list of app IDs
    """
    try:
        if len(apps) == 1 and os.path.isfile(apps[0]):
            with open(apps[0], 'r') as f:
                # Read apps from the file, ignoring blank lines and comments.
                return list(filter(lambda line: line and line[0] != "#",
                                   [line.strip() for line in f]))
        else:
            # Apps are already parsed as a list from the command line.
            return apps
    except OSError as e:
        print("Error {0} while processing input apps.".format(e))
        return []


def print_and_log(msg: str) -> None:
    """Print the message to the terminal and log file.

    Args:
        msg: log message
    """
    print(msg)
    logger.info(msg)


def crawl(args: Namespace) -> None:
    """Download the input apps from Google Play.

    Args:
        args: parsed command line arguments
    """
    apps = read_input_apps(args.input_apps)
    if not apps:
        print("No input apps found, ending crawl.")
        return
    input_total = len(apps)

    # Make output directories - out/country/date (no hour-min-sec).
    start_time = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    out_path = os.path.join(os.path.abspath(args.output_directory_root),
                            args.country,
                            start_time.split("_")[0])
    os.makedirs(out_path, exist_ok=True)

    # Output files: finished apps, download failures, transient errors, log.
    output_files = {
        "finished": os.path.join(out_path, "finished.txt"),
        "failure": os.path.join(out_path, "failure.txt"),
        "transient": os.path.join(out_path, "transient.txt")
    }
    logging.basicConfig(
        format="%(asctime)s> %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
        level=logging.INFO,
        filename=os.path.join(out_path, "info.log")
    )

    # Remove apps that have already been finished (used if restarting crawl).
    apps = remove_finished_apps(apps, output_files["finished"])
    print_and_log("{0} apps left to crawl of {1} in input list.".
                  format(len(apps), input_total))

    # Return if all apps are finished.
    if not apps:
        return

    # Crawl in random order if flag is enabled.
    if args.random:
        shuffle(apps)

    # Put apps on the download queue, ignoring duplicates.
    unique = set()
    for app in apps:
        if app not in unique:
            # The queue contains tuples (app, is_retry, (previous_code, msg)).
            # retry is False and no previous code for first download attempt.
            DOWNLOAD_QUEUE.put((app, False, None))
            unique.add(app)

    # Initialize execute function with the user-defined rate limit.
    execute_ratelimited = sleep_and_retry(
        limits(calls=args.limit[0], period=args.limit[1])(execute))

    print_and_log("Crawl start time: {0}".format(start_time))

    try:
        count = 0
        finished_count = 0
        while not DOWNLOAD_QUEUE.empty():
            app, retry, previous = DOWNLOAD_QUEUE.get()
            if count % 50 == 0:
                # Scrape Google Play location from the home page.
                print_and_log("Site Location: {0}".format(
                    google_location(proxy=args.proxy)))
            try:
                # Try download (calling execute with rate limit wrapper).
                executed = execute_ratelimited(app,
                                               os.path.join(out_path, app),
                                               output_files["failure"],
                                               output_files["transient"],
                                               args.credentials,
                                               is_retry=retry,
                                               previous=previous,
                                               proxy=args.proxy)
                # Add finished app to file.
                if executed:
                    finished_count += 1
                    with open(output_files["finished"], 'a') as f:
                        f.write("{0}\n".format(app))
            except OSError as e:
                print("Error while downloading {0}: {1}".format(app, str(e)))
            count += 1
            DOWNLOAD_QUEUE.task_done()
    except KeyboardInterrupt:
        # The user manually ended the crawl.
        pass

    end_time = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    elapsed = datetime.datetime.strptime(end_time, "%Y-%m-%d_%H-%M-%S") - \
        datetime.datetime.strptime(start_time, "%Y-%m-%d_%H-%M-%S")
    print_and_log("{0} apps finished during crawl.".format(finished_count))
    print_and_log("Crawl end time: {0}".format(end_time))
    print_and_log("Time elapsed: {0}".format(elapsed))


if __name__ == "__main__":
    ARGS = cmd_args()
    crawl(ARGS)
