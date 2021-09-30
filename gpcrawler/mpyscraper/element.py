"""Handle extraction of specific elements from response data."""

from html import unescape
from typing import Dict, Callable, List, Any, AnyStr, Optional

from .constants.regex import NOT_NUMBER


def nested_lookup(source: List[Any], indexes: List[int]) -> Any:
    """Recursively lookup an item in a nested list.

    Args:
        source: nested list
        indexes: list of indexes in order of nesting level
    Returns:
        the item in source located at the indexes
        source [
                'DEVELOPER',
                [None, None, None, None, [None, None, 'DEVELOPER_URL']],
                True
               ]
        indexes [1, 4, 2] returns 'DEVELOPER_URL'
    """
    if not source:
        return source
    if len(indexes) == 1:
        return source[indexes[0]]
    if indexes[0] >= len(source):
        return None
    return nested_lookup(source[indexes[0]], indexes[1::])


class ElementSpec:
    """Specification for a Google Play element."""
    def __init__(self, ds_num: int, extraction_map: List[int],
                 post_processor: Optional[Callable] = None,
                 post_processor_except_fallback: Any = None) -> None:
        self.ds_num = ds_num
        self.extraction_map = extraction_map
        self.post_processor = post_processor
        self.post_processor_except_fallback = post_processor_except_fallback

    def extract_content(self, source: Dict[str, Any]) -> Any:
        """Extract the element from the parsed Google Play response.

        Args:
            source: parsed response as a dict of javascript callbacks,
            where the keys have format "ds:#" and
            the values are a nested list of Google Play metadata:
            {
                "ds:1": [GOOGLE_PLAY_METADATA],
                "ds:2": [GOOGLE_PLAY_METADATA],
                ...
            }
        Returns:
            the Google Play element after post processing
            None if extraction fails
        """
        try:
            result = nested_lookup(
                source["ds:{}".format(self.ds_num)], self.extraction_map
            )
        except (KeyError, IndexError, TypeError):
            result = None

        if result is not None and self.post_processor is not None:
            try:
                result = self.post_processor(result)
            except:  # pylint: disable=bare-except
                result = self.post_processor_except_fallback

        return result


def unescape_text(text: AnyStr) -> AnyStr:
    """Replace HTML line breaks and return the unescaped text."""
    return unescape(text.replace("<br>", "\r\n"))


DETAIL = {
    "title": ElementSpec(5, [0, 0, 0]),
    "description": ElementSpec(5, [0, 10, 0, 1], unescape_text),
    "descriptionHTML": ElementSpec(5, [0, 10, 0, 1]),
    "summary": ElementSpec(5, [0, 10, 1, 1], unescape_text),
    "summaryHTML": ElementSpec(5, [0, 10, 1, 1]),
    "installs": ElementSpec(5, [0, 12, 9, 0]),
    "numInstalls": ElementSpec(5, [0, 12, 9, 2]),
    "minInstalls": ElementSpec(
        5, [0, 12, 9, 0], lambda s: int(NOT_NUMBER.sub("", s)) if s else 0
    ),
    "score": ElementSpec(6, [0, 6, 0, 1]),
    "ratings": ElementSpec(6, [0, 6, 2, 1]),
    "reviews": ElementSpec(6, [0, 6, 3, 1]),
    "histogram": ElementSpec(
        6,
        [0, 6, 1],
        lambda container: [
            container[1][1],
            container[2][1],
            container[3][1],
            container[4][1],
            container[5][1],
        ],
        [0, 0, 0, 0, 0],
    ),
    "price": ElementSpec(
        3, [0, 2, 0, 0, 0, 1, 0, 0], lambda price: (price / 1000000) or 0
    ),
    "free": ElementSpec(3, [0, 2, 0, 0, 0, 1, 0, 0], lambda s: s == 0),
    "currency": ElementSpec(3, [0, 2, 0, 0, 0, 1, 0, 1]),
    "offersIAP": ElementSpec(5, [0, 12, 12, 0], bool),
    "size": ElementSpec(8, [0]),
    "androidVersion": ElementSpec(8, [2], lambda s: s.split()[0]),
    "androidVersionText": ElementSpec(8, [2]),
    "developer": ElementSpec(5, [0, 12, 5, 1]),
    "developerId": ElementSpec(5, [0, 12, 5, 5, 4, 2], lambda s: s.split("id=")[1]),
    "developerEmail": ElementSpec(5, [0, 12, 5, 2, 0]),
    "developerWebsite": ElementSpec(5, [0, 12, 5, 3, 5, 2]),
    "developerAddress": ElementSpec(5, [0, 12, 5, 4, 0]),
    "privacyPolicy": ElementSpec(5, [0, 12, 7, 2]),
    "developerInternalID": ElementSpec(5, [0, 12, 5, 0, 0]),
    "genre": ElementSpec(5, [0, 12, 13, 0, 0]),
    "genreId": ElementSpec(5, [0, 12, 13, 0, 2]),
    "icon": ElementSpec(5, [0, 12, 1, 3, 2]),
    "headerImage": ElementSpec(5, [0, 12, 2, 3, 2]),
    "screenshots": ElementSpec(
        5, [0, 12, 0], lambda container: [item[3][2] for item in container], []
    ),
    "video": ElementSpec(5, [0, 12, 3, 0, 3, 2]),
    "videoImage": ElementSpec(5, [0, 12, 3, 1, 3, 2]),
    "contentRating": ElementSpec(5, [0, 12, 4, 0]),
    "contentRatingDescription": ElementSpec(5, [0, 12, 4, 2, 1]),
    "adSupported": ElementSpec(5, [0, 12, 14, 0], bool),
    "containsAds": ElementSpec(5, [0, 12, 14, 0], bool, False),
    "released": ElementSpec(5, [0, 12, 36]),
    "updated": ElementSpec(5, [0, 12, 8, 0]),
    "version": ElementSpec(8, [1]),
    "recentChanges": ElementSpec(5, [0, 12, 6, 1], unescape_text),
    "recentChangesHTML": ElementSpec(5, [0, 12, 6, 1]),
    "comments": ElementSpec(
        17, [0], lambda container: [item[4] for item in container], []
    ),
    "similarURL": ElementSpec(7, [1, 1, 0, 0, 3, 4, 2]),
}

CLUSTER = {
    "cluster": ElementSpec(3, [0, 1, 0, 0, 3, 4, 2]),
    "apps": ElementSpec(3, [0, 1, 0, 0, 0]),
    "token": ElementSpec(3, [0, 1, 0, 0, 7, 1])
}
