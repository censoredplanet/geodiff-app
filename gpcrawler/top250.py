"""top250.py gets the top apps on Google Play.

usage: top250.py [-h] -o OUTPUT

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        output file for results
"""

from argparse import ArgumentParser

from mpyscraper import GooglePlayScraperException, collection


def main():
    """Get the top apps on Google Play."""
    parser = ArgumentParser(description="Get the top apps on Google Play.")
    parser.add_argument("-o", "--output", required=True,
                        help="output file for results")
    args = parser.parse_args()

    try:
        top_apps = collection("topselling_free")
        with open(args.output, "w") as f:
            f.write("\n".join(top_apps))
    except GooglePlayScraperException as e:
        print("error:", e)


if __name__ == '__main__':
    main()
