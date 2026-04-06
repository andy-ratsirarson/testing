"""Click step handler: find and activate links or buttons."""

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from src.steps.fill_form import build_form_data


def execute_click(
    soup: BeautifulSoup,
    target: str,
    name: str,
    session: requests.Session,
    base_url: str,
) -> tuple[BeautifulSoup, str] | None:
    """Execute a click action on a link or button.

    target="link": find <a> by text, GET its href, return (new_soup, new_url)
    target="button": find <button>/<input type=submit> by text, submit parent form
    """
    name_lower = name.lower()

    if target == "link":
        # Find <a> by text content
        for link in soup.find_all("a"):
            if name_lower in link.get_text(strip=True).lower():
                href = link.get("href")
                if href:
                    full_url = urljoin(base_url, href)
                    response = session.get(full_url)
                    response.raise_for_status()
                    new_soup = BeautifulSoup(response.text, "html.parser")
                    return new_soup, response.url
        return None

    elif target == "button":
        # Find <button> or <input type=submit> by text/value
        element = _find_button(soup, name_lower)
        if element is None:
            return None

        # Find parent form
        form = element.find_parent("form")
        if form is None:
            return None

        action, form_data = build_form_data(form, {})
        full_url = urljoin(base_url, action)
        response = session.post(full_url, data=form_data)
        response.raise_for_status()
        new_soup = BeautifulSoup(response.text, "html.parser")
        return new_soup, response.url

    return None


def _find_button(soup: BeautifulSoup, name_lower: str) -> Tag | None:
    """Find a button or submit input by text/value."""
    # Check <button> elements
    for btn in soup.find_all("button"):
        if name_lower in btn.get_text(strip=True).lower():
            return btn

    # Check <input type=submit> elements
    for inp in soup.find_all("input", {"type": "submit"}):
        value = inp.get("value", "").lower()
        if name_lower in value:
            return inp

    return None
