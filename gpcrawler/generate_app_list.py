"""generate_app_list.py generates a list of popular apps.

usage: generate_app_list.py [-h] -o OUTPUT_DIRECTORY_ROOT [-g COUNTRY]
                            [-s SEARCH] [-c CATEGORY] [-t THREAD_COUNT]
                            [-p PROXY]

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_DIRECTORY_ROOT, --output_directory_root OUTPUT_DIRECTORY_ROOT
                        root directory for output files
  -g COUNTRY, --country COUNTRY
                        country code for crawl
  -s SEARCH, --search SEARCH
                        file containing list of search terms
  -c CATEGORY, --category CATEGORY
                        file containing list of categories
  -t THREAD_COUNT, --thread_count THREAD_COUNT
                        number of worker threads
  -p PROXY, --proxy PROXY
                        proxy (IP:PORT)
"""

import asyncio
import logging
import os.path
from argparse import ArgumentParser, Namespace
from concurrent.futures import ThreadPoolExecutor
from os import makedirs
from time import localtime, strftime
from typing import List

from mpyscraper import (CATEGORIES, GooglePlayScraperException, details,
                        filtered_collection, search)

logger = logging.getLogger(__name__)


def get_from_file(filename: str) -> List[str]:
    """Get list of apps ids or terms from the input file.

    Args:
        filename: input file containing one app id or term per line
    Returns:
        list of app ids or terms
    """
    with open(filename, "r") as f:
        return [line.strip() for line in f]


def get_category(app: str) -> None:
    """Get the category of an app.

    Args:
        app: Google Play application ID
    """
    try:
        category = details(app, proxy=PROXY)["genreId"]
        logger.info("DETAILS| %s: %s", app, category)
    except GooglePlayScraperException:
        logger.info("DETAILS| %s: error", app)


def organize_apps(filename: str, full: str, summary: str) -> None:
    """Organize apps in the file by category.

    Args:
        filename: log file containing app-category pairs
        full: output file for apps organized by category
        summary: output file for the category summary
    """
    apps = {}
    lines = get_from_file(filename)
    for line in lines:
        if line.startswith("DETAILS| "):
            app_id, category = line[9:].split(": ")
            apps.setdefault(category, []).append(app_id)
    # Write organized ids and category summary to files.
    with open(full, "w") as fullf, open(summary, "w") as summaryf:
        for category in CATEGORIES:
            if category in apps:
                fullf.write("# {0} {1}\n".format(
                    category, len(apps[category])))
                summaryf.write("# {0} {1}\n".format(
                    category, len(apps[category])))
                fullf.write("\n".join(apps[category]))
                fullf.write("\n")


async def crawl_async(app_list: List[str], thread_count: int) -> None:
    """Crawl Google Play asynchronously.

    Args:
        app_list: list of app ids
        thread_count: number of worker threads
    """
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        # Concurrently run category queries.
        loop = asyncio.get_event_loop()
        category_tasks = [loop.run_in_executor(executor, get_category, app)
                          for app in app_list]
        asyncio.gather(*category_tasks)
        # Wait for category queries to return.
        for response in asyncio.as_completed(category_tasks):
            await response


def crawl(app_list: List[str], thread_count: int) -> None:
    """Crawl Google Play to retrieve app metadata for the app list.

    Args:
        app_list: list of app ids
        thread_count: number of worker threads
    """
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(crawl_async(app_list, thread_count))
    loop.run_until_complete(future)


def main(args: Namespace) -> None:
    """Generate a list of popular apps on Google Play.

    Args:
        args: parsed command line arguments
    """
    current = strftime("%Y-%m-%d_%H-%M-%S", localtime())
    full_path = os.path.join(args.output_directory_root, args.country, current)
    if not os.path.exists(full_path):
        makedirs(full_path)

    filenames = {
        "log": os.path.join(full_path, "log.txt"),
        "app": os.path.join(full_path, "app_list.txt"),
        "full": os.path.join(full_path, "results.txt"),
        "summary": os.path.join(full_path, "summary.txt"),
        "category": os.path.join(full_path, "category.txt"),
        "search": os.path.join(full_path, "search.txt")
    }

    logging.basicConfig(
        format="",
        datefmt="%Y/%m/%d %H:%M:%S",
        level=logging.INFO,
        filename=filenames["log"]
    )

    logger.info("Starting crawl: %s", current)
    logger.info("Saving output files to %s", full_path)

    # We generate the app list by taking the union of several keyword searches
    # and the top 200 apps in each category.

    app_list = set()

    # Use default search terms if input file not provided.
    terms = ["vpn", "ad blocker", "privacy", "security", "crypto wallet"]
    if args.search:
        terms = get_from_file(args.search)

    with open(filenames["search"], "a") as f:
        for term in terms:
            if term.startswith("#"):
                continue
            f.write("# {0}\n".format(term))
            try:
                top_apps = search(term, proxy=PROXY)
                f.write("\n".join(top_apps))
                f.write("\n")
                app_list.update(top_apps)
                logger.info("SEARCH| %s: success", term)
            except GooglePlayScraperException:
                logger.info("SEARCH| %s: error", term)

    # Use all categories if input file not provided.
    categories = CATEGORIES
    if args.category:
        categories = get_from_file(args.category)

    with open(filenames["category"], "a") as f:
        for cat in categories:
            if cat not in CATEGORIES:
                continue
            f.write("# {0}\n".format(cat))
            try:
                top200 = filtered_collection(cat, proxy=PROXY)
                f.write("\n".join(top200))
                f.write("\n")
                app_list.update(top200)
                logger.info("CATEGORY| %s: success", cat)
            except GooglePlayScraperException:
                logger.info("CATEGORY| %s: error", cat)

    app_list.discard(None)

    logger.info("App list done: %s",
                strftime("%Y-%m-%d_%H-%M-%S", localtime()))
    logger.info("App list contains %d apps saved to %s",
                len(app_list), filenames["app"])

    with open(filenames["app"], "w") as f:
        f.write("\n".join(app_list))

    # Retrieve the category of each app in the list.
    crawl(app_list, args.thread_count)

    # Organize apps by category.
    logger.info("Finished crawl: %s",
                strftime("%Y-%m-%d_%H-%M-%S", localtime()))
    organize_apps(filenames["log"], filenames["full"], filenames["summary"])
    logger.info("Full organized results saved to %s, summary saved to %s",
                filenames["full"], filenames["summary"])


def cmd_args() -> Namespace:
    """Parse the command line arguments."""
    parser = ArgumentParser(description="Generate the app list.")
    parser.add_argument("-o", "--output_directory_root", required=True,
                        help="root directory for output files")
    parser.add_argument("-g", "--country", default="US",
                        help="country code for crawl")
    parser.add_argument("-s", "--search",
                        help="file containing list of search terms")
    parser.add_argument("-c", "--category",
                        help="file containing list of categories")
    parser.add_argument("-t", "--thread_count", type=int, default=20,
                        help="number of worker threads")
    parser.add_argument("-p", "--proxy", default=None,
                        help="proxy (IP:PORT)")
    return parser.parse_args()


if __name__ == '__main__':
    ARGS = cmd_args()
    PROXY = ARGS.proxy
    main(ARGS)
