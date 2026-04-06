"""Navigate step handler: fetch a URL and return parsed HTML."""

import requests
from bs4 import BeautifulSoup


def execute_navigate(url: str, session: requests.Session) -> tuple[BeautifulSoup, str]:
    """Fetch URL via session.get(), return (parsed_soup, final_url)."""
    response = session.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    return soup, response.url
