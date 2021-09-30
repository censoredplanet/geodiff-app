"""regex.py contains precompiled regular expressions for mpyscraper."""

import re

SCRIPT = re.compile(r"AF_initDataCallback[\s\S]*?<\/script")
KEY = re.compile(r"(ds:.*?)'")
VALUE = re.compile(r"data:([\s\S]*?), sideChannel: \{\}\}\);<\/")
NOT_NUMBER = re.compile(r"[^\d]")
BUTTON = re.compile(r"<button[\s\S]*?<\/button>")
OFFER = re.compile(r"<span itemprop=\"offers\"[\s\S]*?<\/span>")
SPAN = re.compile(r"<[/]*span[ ]*[\S]*>")
DOWNLOAD = re.compile(r"<meta itemprop=\"url\" content=[\S]*>")
