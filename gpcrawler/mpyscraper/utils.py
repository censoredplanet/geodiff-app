"""utils.py contains helper functions to make requests and parse response data."""

import json
from urllib.error import HTTPError
from urllib.request import urlopen, build_opener, ProxyHandler, Request
from urllib.parse import quote_plus
from typing import Any, Dict, List, Optional

from ratelimit import limits, sleep_and_retry

from .element import CLUSTER, nested_lookup
from .constants.regex import KEY, VALUE, SCRIPT, BUTTON, OFFER, DOWNLOAD
from .exceptions import InvalidURLError, NotFoundError, ExtraHTTPError


def _build_url(url_type: str, params: Dict[str, str]) -> str:
    """Build the formatted Google Play URL for the request type.

    Args:
        url_type: "details", "search", "collection", "filtered", or "ui"
        params: dictionary containing the format parameters (e.g. func, id, hl, gl)
    Returns:
        formatted url
    Raises:
        InvalidURLError if url_type or params are invalid
    """
    try:
        if url_type == "details":
            return "https://play.google.com/store/apps/{func}?id={id}{hl}{gl}".format(**params)
        if url_type == "search":
            return "https://play.google.com/store/{func}?q={id}{hl}{gl}&c=apps".format(**params)
        if url_type == "collection":
            return "https://play.google.com/store/apps/{func}/{id}{hl}{gl}".format(**params)
        if url_type == "filtered":
            return "https://play.google.com"\
                   "/store/apps/{collection}/category/{category}?{hl}{gl}".format(**params)
        if url_type == "ui":
            return "https://play.google.com"\
                    "/_/PlayStoreUi/data/batchexecute?{hl}{gl}".format(**params)
    except KeyError:
        raise InvalidURLError
    raise InvalidURLError


def _parse_response(dom: str) -> Dict[str, Any]:
    """Parse the Google Play metadata from the request response.

    Args:
        dom: a request response body as a string
    Returns:
        dict of the javascript callbacks, where the keys have format "ds:#"
        and the values are a nested list of Google Play metadata:
        {"ds:1": [GOOGLE_PLAY_METADATA], "ds:2": [GOOGLE_PLAY_METADATA], ...}
    """
    matches = SCRIPT.findall(dom)
    res = {}
    for match in matches:
        key_match = KEY.findall(match)
        value_match = VALUE.findall(match)

        if key_match and value_match:
            res[key_match[0]] = json.loads(value_match[0])
    return res


def _download_link(dom: str) -> (Optional[str], Optional[bool]):
    """Parse the download link from the request response.

    Args:
        dom: a request response body as a string
    Returns:
        (download link, download link enabled) as a string and boolean
        (None, None) if the download link is not found
    """
    button = BUTTON.findall(dom)
    for i in button:
        offers = OFFER.findall(i)
        if offers:
            download = DOWNLOAD.findall(i)[0]
            download = download.replace(">", "").split("content=")[1]
            link_disabled = i.find(' disabled>')
            download = download.replace('"', '')
            if link_disabled == -1:
                return download.replace("amp;", ""), True
            return download.replace("amp;", ""), False
    return None, None


@sleep_and_retry
@limits(calls=5, period=1)
def _request(url: str, proxy: Optional[str] = None) -> str:
    # type: (str) -> str
    """Make a HTTPS request to a Google Play URL (ratelimit 5 requests/second).

    Args:
        url: Google Play URL
        proxy: string with format "ip:port" if using a proxy
    Returns:
        the response body as a string
    """
    try:
        if proxy:
            proxy_handler = ProxyHandler(proxies={"http": proxy, "https": proxy})
            opener = build_opener(proxy_handler)
            resp = opener.open(url)
        else:
            resp = urlopen(url)
    except HTTPError as e:
        if e.code == 404:
            raise NotFoundError("Page not found(404).")
        raise ExtraHTTPError(
            "Page not found. Status code {} returned.".format(e.code)
        )

    return resp.read().decode()


def _parse_app_details(app: Optional[List[Any]]) -> Dict[str, Any]:
    """Parse app details from Google Play metadata.

    Args:
        app: Google Play metadata
    Returns:
        dict of app details
    """
    app_info = {}
    app_info["url"] = "https://play.google.com" + nested_lookup(app, [9, 4, 2])
    app_info["appId"] = nested_lookup(app, [12, 0])
    app_info["title"] = nested_lookup(app, [2])
    app_info["summary"] = nested_lookup(app, [4, 1, 1, 1, 1])
    app_info["developer"] = nested_lookup(app, [4, 0, 0, 0])
    app_info["developerId"] = nested_lookup(app, [4, 0, 0, 1, 4, 2]).split('?id=')[1]
    app_info["icon"] = nested_lookup(app, [1, 1, 0, 3, 2])
    app_info["score"] = nested_lookup(app, [6, 0, 2, 1, 1])
    app_info["scoreText"] = nested_lookup(app, [6, 0, 2, 1, 0])
    price = nested_lookup(app, [7, 0, 3, 2, 1, 0, 2])
    app_info["priceText"] = price if price != [] else 'Free'
    app_info["free"] = bool(price == [])
    return app_info


def _parse_app_list(apps: List[Any], num: Optional[int] = None,
                    detail: bool = False) -> List[Any]:
    """Parse apps from a list of Google Play metadata.

    Args:
        apps: list of Google Play metadata
        num: maximum number of apps to include (None)
        detail: include app details if True, else only app ids
    Returns:
        list of apps: detail=True (1), detail=False (2)
        (1) [{"url":"url1", "appId":"id1", ...}, {"url": "url2", "appId": "id2", ...}, ...]
        (2) ["id1", "id2", ...]
    """
    if detail:
        return [_parse_app_details(app) for idx, app in enumerate(apps)
                if not num or (num and idx < num)]
    return [nested_lookup(app, [12, 0]) for idx, app in enumerate(apps)
            if not num or (num and idx < num)]


def _get_ui_request(url: str, func: str, param: str,
                    proxy: Optional[str] = None) -> Any:
    """Make a POST request to the UI server for batch data.

    (1) Token requests simulate retrieving the next page of data for a search, collection, etc.
    (2) Permission requests get the permissions for a specific app.

    Args:
        url: Google Play URL (with "ui" format)
        func: "token" or "permission"
        param: the token ("token") or app id ("permission") for the POST data
        proxy: string with format "ip:port" if using a proxy
    Returns:
        list of Google Play metadata
    """
    ui_dict = {
        "token": '[[["qnKhOb","[[null,[[10,[10,50]],true,null,'\
                 '[96,27,4,8,57,30,110,79,11,16,49,1,3,9,12,104,55,56,51,10,34,31,77],'\
                 '[null,null,null,[[[[7,31],[[1,43,112,92,58,69,31,19,96]]]]]]],null,\\"{0}\\"]]"'\
                 ',null,"generic"]]]',
        "permission": '[[["xdSrCf","[[null,[\\"{0}\\",7],[]]]",null,"1"]]]'
    }
    body = 'f.req=' + quote_plus(ui_dict[func].format(param))
    data = body.encode('utf-8')
    req = Request(url=url, data=data, method="POST")
    resp = _request(req, proxy)
    retry = 0
    while resp.find("PlayDataError") != -1:
        if retry == 5:
            return resp
        resp = _request(req, proxy)
        retry += 1
    resp = json.loads(nested_lookup(json.loads(resp[5:]), [0, 2]))
    return resp


def _cluster_request(url: str, proxy: Optional[str] = None,
                     lang: Optional[str] = None,
                     country: Optional[str] = None) -> List[Any]:
    """Make requests to get the maximum amount of data for a query.

    In a browser, Google Play automatically makes requests to another "ui" server
    to load more data as the user scrolls a page (e.g. when loading search results).

    Args:
        url: Google Play URL
        proxy: string with format "ip:port" if using a proxy
        lang: language code (typically two letters)
        country: two-letter ISO 3166 country code
    Returns:
        list of apps
        ["id1", "id2", ...]
    """
    url_in = {"hl": "&hl=" + lang if lang else "",
              "gl": "&gl=" + country if country else ""}
    dom = _request(url, proxy)
    res = _parse_response(dom)
    apps = CLUSTER["apps"].extract_content(res)
    token = CLUSTER["token"].extract_content(res)
    results = _parse_app_list(apps)
    try:
        while token:
            url = _build_url("ui", url_in)
            resp = _get_ui_request(url, "token", token, proxy)
            apps = nested_lookup(resp, [0, 0, 0])
            results = results + _parse_app_list(apps)
            token = nested_lookup(resp, [0, 0, 7, 1])
    except:  # pylint: disable=bare-except
        return results
    return results
