"""
download_privacy.py downloads the privacy policies for a set of apps.

usage: download_privacy.py [-h] -d DRIVER_PATH -i INPUT_FILE
                           -o OUTPUT_DIRECTORY_ROOT -c COUNTRY
                           [-s SOCKS_PROXY] [-p HTTP_PROXY]

optional arguments:
  -d DRIVER_PATH, --driver_path DRIVER_PATH
        /path/to/chromedriver/executable

  -i INPUT_FILE, --input_file INPUT_FILE
        CSV with columns of privacy policy URLs per country

  -o OUTPUT_DIRECTORY_ROOT, --output_directory_root OUTPUT_DIRECTORY_ROOT
        directory to save downloaded privacy policy .html files

  -c COUNTRY, --country COUNTRY
        Two-letter country code corresponding with column in input file

  -s SOCKS_PROXY, --socks_proxy SOCKS_PROXY
        SOCKS5 proxy with format ip:port

  -p HTTP_PROXY, --http_proxy HTTP_PROXY
        HTTP(S) proxy with format ip:port

"""
import logging
import os.path
from argparse import ArgumentParser, Namespace
from queue import Queue
from threading import Thread
from time import localtime, strftime

# pylint: disable=import-error
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By

app_queue = Queue()  # pylint: disable=invalid-name
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


def init(args: Namespace, output_directory: str) -> None:
    """Send requests for privacy policy URLs and download the HTML pages."""
    options = webdriver.ChromeOptions()
    # Initialize the driver to run in incognito and headless mode.
    # Add proxy arguments (format "ip:port") if included in command line args.
    if args.socks_proxy:
        options.add_argument("--proxy-server=socks5://{0}".format(
            args.socks_proxy))
        ip, _ = args.socks_proxy.split(":")
        options.add_argument(
            "--host-resolver-rules=\"MAP * ~NOTFOUND , EXCLUDE {0}\"".format(
                ip))
    elif args.http_proxy:
        options.add_argument("--proxy-server=http={0};https={0}".format(
            args.http_proxy))

    options.add_argument('--incognito')
    options.add_argument('--headless')

    try:
        service = webdriver.chrome.service.Service(args.driver_path)
        driver = webdriver.Chrome(service=service, options=options)
    except WebDriverException as e:
        print("Error initalizing driver:", e)
        return

    # Verify location from the Google Play home page.
    try:
        driver.get("https://play.google.com")
        elements = driver.find_elements(by=By.CLASS_NAME, value="XjE2Pb")
        location = [elem for elem in elements if "Location" in elem.text]
        if location:
            print_and_log(location[0].text)
    except WebDriverException as e:
        print("Google Play Location not found")
        return

    while True:
        item = app_queue.get()
        if item is None:
            break
        app, url = item
        if pd.notna(url):
            # Make a request to the app's privacy policy URL
            # and save the resulting HTML.
            app_path = os.path.join(output_directory, "{0}.html".format(app))
            try:
                if not os.path.exists(app_path):
                    driver.get(url)
                    with open(app_path, "w") as f:
                        f.write(driver.page_source)
                    logger.info("%s: policy downloaded", app)
            except Exception as e:  # pylint: disable=broad-except
                print_and_log("{0}: {1}".format(
                    app, str(e).replace("\n", " ")))
        else:
            logger.info("%s: no privacy policy", app)
        app_queue.task_done()


def print_and_log(msg: str) -> None:
    """Print the message to the terminal and log file.

    Args:
        msg: log message
    """
    print(msg)
    logger.info(msg)


def main() -> None:
    """Download privacy policies for the input set of apps."""
    parser = ArgumentParser(
        description="Download the privacy policies for a set of apps.")
    parser.add_argument(
        "-d",
        "--driver_path",
        required=True,
        help="/path/to/chromedriver/executable")
    parser.add_argument(
        "-i",
        "--input_file",
        required=True,
        help="CSV with columns of privacy policy URLs per country")
    parser.add_argument(
        "-o",
        "--output_directory_root",
        required=True,
        help="directory to save downloaded privacy policy .html files")
    parser.add_argument(
        "-c",
        "--country",
        required=True,
        help="Two-letter country code corresponding with column in input file")
    parser.add_argument(
        "-s",
        "--socks_proxy",
        help="SOCKS5 proxy with format ip:port")
    parser.add_argument(
        "-p",
        "--http_proxy",
        help="HTTP(S) proxy with format ip:port")
    args = parser.parse_args()

    start_time = strftime("%Y-%m-%d_%H-%M-%S", localtime())
    output_directory = os.path.join(args.output_directory_root, args.country)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    log_file = os.path.join(output_directory, "log.txt")
    num_workers = 5

    logging.basicConfig(
        format="%(asctime)s> %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
        level=logging.INFO,
        filename=log_file
    )

    # Log crawl information.
    print_and_log("Input: {0}".format(args.input_file))
    print_and_log("Output directory: {0}".format(output_directory))
    print_and_log("Log file: {0}".format(log_file))
    print_and_log("Starting crawl: {0}".format(start_time))

    # Read input file.
    if os.path.exists(args.input_file):
        input_df = pd.read_csv(args.input_file, index_col=0)
        country_df = input_df[args.country]
    else:
        print_and_log("Error in input file: ending crawl")
        return

    # Add apps to queue.
    for item in country_df.iteritems():
        app_queue.put(item)

    # Start threads to download policies.
    for _ in range(0, num_workers):
        thread = Thread(target=init,
                        args=(args, output_directory),
                        daemon=True)
        thread.start()

    # Wait for requests to finish.
    app_queue.join()

    for _ in range(0, num_workers):
        app_queue.put(None)

    # Log finish time.
    finish_time = strftime("%Y-%m-%d_%H-%M-%S", localtime())
    print_and_log("Finished crawl: {0}".format(finish_time))


if __name__ == '__main__':
    main()
