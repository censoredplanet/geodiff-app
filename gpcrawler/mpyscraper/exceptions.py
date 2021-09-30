"""exceptions.py defines Exceptions for mpyscraper."""


class GooglePlayScraperException(Exception):
    """Base exception class for mpyscraper."""


class InvalidURLError(GooglePlayScraperException):
    """Thrown when attempting to build an invalid Google Play URL."""


class NotFoundError(GooglePlayScraperException):
    """Thrown when an HTTP(S) request to Google Play returns a 404 error."""


class ExtraHTTPError(GooglePlayScraperException):
    """Thrown when an HTTP(S) request to Google Play returns a non-404 error."""
