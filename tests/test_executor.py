"""Unit tests for step handlers and executor using the test server."""

import requests
from bs4 import BeautifulSoup

from src.steps.navigate import execute_navigate
from src.steps.fill_form import find_form_by_title, build_form_data, submit_form
from src.steps.click import execute_click


def test_navigate(test_server):
    """Navigate to test server root and verify soup content."""
    session = requests.Session()
    soup, url = execute_navigate(test_server, session)
    assert "Registration" in soup.get_text()
    assert url.startswith(test_server)


def test_fill_form(test_server):
    """Navigate then fill and submit form, verify submission."""
    session = requests.Session()
    soup, url = execute_navigate(test_server, session)

    form = find_form_by_title(soup, "Registration")
    assert form is not None

    action_url, form_data = build_form_data(form, {"firstname": "John", "lastname": "Doe"})
    assert form_data["firstname"] == "John"
    assert form_data["lastname"] == "Doe"
    assert form_data["csrf_token"] == "abc123"
    assert action_url == "/submit"

    result_soup = submit_form(session, action_url, form_data, url)
    assert "Submission successful" in result_soup.get_text()


def test_click_link(test_server):
    """Navigate then click a link, verify new page."""
    session = requests.Session()
    soup, url = execute_navigate(test_server, session)

    result = execute_click(soup, "link", "Next Page", session, url)
    assert result is not None
    new_soup, new_url = result
    assert "Next Page" in new_soup.get_text()


def test_click_button(test_server):
    """Navigate then click the submit button, verify form submission."""
    session = requests.Session()
    soup, url = execute_navigate(test_server, session)

    result = execute_click(soup, "button", "Submit", session, url)
    assert result is not None
    new_soup, new_url = result
    assert "Submission successful" in new_soup.get_text()
