"""Fill form step handler: locate forms, build data, and submit."""

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag


def find_form_by_title(soup: BeautifulSoup, title: str) -> Tag | None:
    """Find <form> near a heading/legend/label matching title (case-insensitive).

    Search strategy:
    1. Check h1-h6, legend, label for text containing title
    2. Walk up to find nearest <form> ancestor
    3. Walk sideways to find nearest <form> sibling
    """
    title_lower = title.lower()

    # Search headings, legends, and labels
    candidates = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "legend", "label"])
    for element in candidates:
        if title_lower in element.get_text(strip=True).lower():
            # Walk up to find <form> ancestor
            parent = element.parent
            while parent:
                if parent.name == "form":
                    return parent
                parent = parent.parent

            # Walk sideways: check next siblings
            sibling = element.find_next_sibling("form")
            if sibling:
                return sibling

            # Check next element in document order
            form = element.find_next("form")
            if form:
                return form

    # Fallback: return first form on the page
    return soup.find("form")


def build_form_data(form: Tag, fields: dict[str, str]) -> tuple[str, dict]:
    """Extract form action URL and merge user fields with existing hidden inputs."""
    action = form.get("action", "")

    # Collect existing form data (hidden inputs, defaults)
    form_data: dict[str, str] = {}
    for input_tag in form.find_all("input"):
        name = input_tag.get("name")
        if name:
            value = input_tag.get("value", "")
            input_type = input_tag.get("type", "text").lower()
            if input_type == "hidden" or name in fields:
                form_data[name] = value

    # Also collect select and textarea defaults
    for select in form.find_all("select"):
        name = select.get("name")
        if name:
            selected = select.find("option", selected=True)
            if selected:
                form_data[name] = selected.get("value", selected.get_text())

    for textarea in form.find_all("textarea"):
        name = textarea.get("name")
        if name:
            form_data[name] = textarea.get_text()

    # Override with user-provided fields
    form_data.update(fields)

    return str(action), form_data


def submit_form(
    session: requests.Session,
    action_url: str,
    data: dict,
    base_url: str,
) -> BeautifulSoup:
    """POST form data using urljoin for URL resolution, return response soup."""
    full_url = urljoin(base_url, action_url)
    response = session.post(full_url, data=data)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")
