"""Scraping functions."""

from typing import Any, Dict, List, Optional

from .utils import (
    _build_url, _request, _parse_response,
    _get_ui_request, _cluster_request, _download_link
)
from .element import DETAIL

def google_location(proxy: Optional[str] = None) -> str:
    """Scrape the Google Play store location from the home page.

    Args:
        proxy: string with format "ip:port" if using a proxy
    Returns:
        country string
    """
    dom = _request("https://play.google.com/store/apps", proxy)
    res = _parse_response(dom)
    location_key = max(res.keys(), key=lambda x: int(x.lstrip("ds:")))
    return res[location_key][4]


def details(app_id: str, proxy: Optional[str] = None,
            lang: Optional[str] = None,
            country: Optional[str] = None) -> Dict[str, Any]:
    """Scrape the details for an app.

    Args:
        app_id: Google Play application ID
        proxy: string with format "ip:port" if using a proxy
        lang: language code (typically two letters)
        country: two-letter ISO 3166 country code
    Returns:
        dict containing app details
    """
    url_in = {"func": "details",
              "id": app_id,
              "hl": "&hl=" + lang if lang else "",
              "gl": "&gl=" + country if country else ""}
    url = _build_url("details", url_in)
    dom = _request(url, proxy)
    res = _parse_response(dom)
    location_key = max(res.keys(), key=lambda x: int(x.lstrip("ds:")))
    result = {"appId": app_id, "url": url,
              "siteLocation": res[location_key][4], "siteLanguage": res[location_key][5]}
    for key, spec in DETAIL.items():
        content = spec.extract_content(res)
        result[key] = content
    result["downloadLink"], result["downloadLinkEnabled"] = _download_link(dom)
    return result


def similar(app_id: str, proxy: Optional[str] = None,
            lang: Optional[str] = None,
            country: Optional[str] = None) -> List[Any]:
    """Scrape the similar app list for an app.

    Args:
        app_id: Google Play application ID
        proxy: string with format "ip:port" if using a proxy
        lang: language code (typically two letters)
        country: two-letter ISO 3166 country code
    Returns:
        list of similar apps
    """
    url_in = {"func": "details",
              "id": app_id,
              "hl": "&hl=" + lang if lang else "",
              "gl": "&gl=" + country if country else ""}
    url = _build_url("details", url_in)
    dom = _request(url, proxy)
    res = _parse_response(dom)
    url = DETAIL["similarURL"].extract_content(res)
    if not url:
        return []
    url = "https://play.google.com" + url
    return _cluster_request(url, proxy, lang, country)


def developer(dev_id: str, proxy: Optional[str] = None,
              lang: Optional[str] = None,
              country: Optional[str] = None) -> List[Any]:
    """Scrape the details for a developer.

    Args:
        dev_id: Google Play developer ID (numeric string) or name
        proxy: string with format "ip:port" if using a proxy
        lang: language code (typically two letters)
        country: two-letter ISO 3166 country code
    Returns:
        dict containing developer details
    """
    url_in = {"func": "dev" if dev_id.isnumeric() else "developer",
              "id": dev_id.replace(" ", "+"),
              "hl": "&hl=" + lang if lang else "",
              "gl": "&gl=" + country if country else ""}
    url = _build_url("details", url_in)
    return _cluster_request(url, proxy, lang, country)


def search(term: str, proxy: Optional[str] = None,
           lang: Optional[str] = None,
           country: Optional[str] = None) -> List[Any]:
    """Scrape the results of a search on Google Play.

    Args:
        term: search term
        proxy: string with format "ip:port" if using a proxy
        lang: language code (typically two letters)
        country: two-letter ISO 3166 country code
    Returns:
        list of apps related to the search term
    """
    url_in = {"func": "search",
              "id": term.replace(" ", "+"),
              "hl": "&hl=" + lang if lang else "",
              "gl": "&gl=" + country if country else ""}
    url = _build_url("search", url_in)
    return _cluster_request(url, proxy, lang, country)


def collection(collection_name: str, proxy: Optional[str] = None,
               lang: Optional[str] = None,
               country: Optional[str] = None) -> List[Any]:
    """Scrape the apps in a Google Play collection.

    Args:
        collection_name: Google Play collection ID
        proxy: string with format "ip:port" if using a proxy
        lang: language code (typically two letters)
        country: two-letter ISO 3166 country code
    Returns:
        list of apps in the collection
    """
    url_in = {"func": "collection",
              "id": collection_name.replace(" ", "+"),
              "hl": "&hl=" + lang if lang else "",
              "gl": "&gl=" + country if country else ""}
    url = _build_url("collection", url_in)
    return _cluster_request(url, proxy, lang, country)


def category(category_name: str, proxy: Optional[str] = None,
             lang: Optional[str] = None,
             country: Optional[str] = None) -> List[Any]:
    """Scrape the recommended apps in a Google Play category.

    Args:
        category_name: Google Play category ID
        proxy: string with format "ip:port" if using a proxy
        lang: language code (typically two letters)
        country: two-letter ISO 3166 country code
    Returns:
        list of recommended apps in the category
    """
    url_in = {"func": "category",
              "id": category_name,
              "hl": "&hl=" + lang if lang else "",
              "gl": "&gl=" + country if country else ""}
    url = _build_url("collection", url_in)
    return _cluster_request(url, proxy, lang, country)


def filtered_collection(category_name: str, collection_name: str = "top",
                        proxy: Optional[str] = None,
                        lang: Optional[str] = None,
                        country: Optional[str] = None) -> List[Any]:
    """Scrape the apps in a Google Play top collection.

    Args:
        category_name: Google Play category ID
        proxy: string with format "ip:port" if using a proxy
        lang: language code (typically two letters)
        country: two-letter ISO 3166 country code
    Returns:
        list of top apps in the category
    """
    url_in = {"category": category_name,
              "collection": collection_name,
              "hl": "&hl=" + lang if lang else "",
              "gl": "&gl=" + country if country else ""}
    url = _build_url("filtered", url_in)
    return _cluster_request(url, proxy, lang, country)


def permissions(app_id: str, proxy: Optional[str] = None,
                lang: Optional[str] = None,
                country: Optional[str] = None) -> Dict[str, List[Any]]:
    """Scrape the permissions for an app.

    Args:
        app_id: Google Play application ID
        proxy: string with format "ip:port" if using a proxy
        lang: language code (typically two letters)
        country: two-letter ISO 3166 country code
    Returns:
        dict containing app permissions
    """
    url_in = {"hl": "&hl=" + lang if lang else "",
              "gl": "&gl=" + country if country else ""}
    url = _build_url("ui", url_in)
    permissions_list = _get_ui_request(url, "permission", app_id, proxy)
    results = {}
    for permissions_category in permissions_list:
        for permission in permissions_category:
            if len(permission) == 2:
                if "Other" not in results:
                    results["Other"] = []
                results["Other"].append(permission[1])
            else:
                for subpermission in permission[2]:
                    if permission[0] not in results:
                        results[permission[0]] = []
                    results[permission[0]].append(subpermission[1])
    return results
