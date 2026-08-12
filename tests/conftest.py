"""Shared fixtures for the sfui test suite.

The browser tests drive the real files in a real Chromium via
Playwright. The repository root is served over HTTP because the
components are ES modules and will not load from file:// URLs --
the same reason demo.html needs `python3 -m http.server`.
"""

import functools
import http.server
import pathlib
import threading

import pytest


REPO = pathlib.Path(__file__).resolve().parent.parent


@pytest.fixture(scope='session')
def repo_url():
    """Serve the repository root over HTTP for the browser tests."""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(REPO))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_address[1]}'
    server.shutdown()
    thread.join()


@pytest.fixture(scope='session')
def browser():
    sync_api = pytest.importorskip('playwright.sync_api')
    with sync_api.sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def make_page(browser, repo_url):
    """Open a test page in a fresh context.

    Each call gets its own context so cookie state never leaks
    between tests. The sf-theme cookie can be preset, and the
    emulated operating system color scheme chosen, before the page
    loads -- which is the order a real visit happens in.
    """
    contexts = []

    def factory(path='/tests/pages/theme.html', color_scheme='dark', cookie=None):
        context = browser.new_context(color_scheme=color_scheme)
        contexts.append(context)
        if cookie is not None:
            context.add_cookies([{'name': 'sf-theme', 'value': cookie, 'url': repo_url}])
        page = context.new_page()
        page.goto(repo_url + path)
        if 'tests/pages/' in path:
            page.wait_for_function('window.harnessReady === true')
        return page

    yield factory
    for context in contexts:
        context.close()
