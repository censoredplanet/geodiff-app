"""mpyscraper provides functions to scrape data from Google Play."""

from .api import (
    google_location,
    details,
    similar,
    developer,
    search,
    collection,
    category,
    filtered_collection,
    permissions
)
from .exceptions import (
    GooglePlayScraperException,
    InvalidURLError,
    NotFoundError,
    ExtraHTTPError
)
from .constants.constant import (
    COLLECTIONS,
    CATEGORIES
)
