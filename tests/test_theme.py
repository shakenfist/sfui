"""Browser tests for sf-theme.js, the theme boot script.

These drive the contract documented in the sf-theme.js file
header: cookie semantics, the auto state following the operating
system, and the stamping of a concrete data-theme before pages
paint.
"""

import pytest


pytest.importorskip('playwright.sync_api')


def resolved_theme(page):
    return page.evaluate('document.documentElement.dataset.theme')


def sf_theme_cookie(context):
    for cookie in context.cookies():
        if cookie['name'] == 'sf-theme':
            return cookie['value']
    return None


def test_auto_follows_os_scheme(make_page):
    for scheme in ('dark', 'light'):
        page = make_page(color_scheme=scheme)
        assert resolved_theme(page) == scheme
        assert page.evaluate('sfTheme.preference') == 'auto'


def test_cookie_preference_beats_os_scheme(make_page):
    page = make_page(color_scheme='dark', cookie='light')
    assert resolved_theme(page) == 'light'
    assert page.evaluate('sfTheme.preference') == 'light'


def test_set_stores_cookie_and_restamps(make_page):
    page = make_page(color_scheme='dark')
    page.evaluate('sfTheme.set("light")')
    assert resolved_theme(page) == 'light'
    assert sf_theme_cookie(page.context) == 'light'


def test_set_auto_deletes_cookie(make_page):
    page = make_page(color_scheme='dark', cookie='light')
    page.evaluate('sfTheme.set("auto")')
    assert resolved_theme(page) == 'dark'
    assert sf_theme_cookie(page.context) is None


def test_set_rejects_unknown_preference(make_page):
    page = make_page()
    message = page.evaluate(
        '(() => { try { sfTheme.set("sepia"); return null; } catch (error) { return error.message; } })()')
    assert 'must be auto' in message
    assert sf_theme_cookie(page.context) is None


def test_os_change_restamps_while_auto(make_page):
    page = make_page(color_scheme='dark')
    assert resolved_theme(page) == 'dark'
    page.emulate_media(color_scheme='light')
    page.wait_for_function('document.documentElement.dataset.theme === "light"')


def test_os_change_ignored_with_explicit_preference(make_page):
    page = make_page(color_scheme='dark', cookie='dark')
    page.emulate_media(color_scheme='light')
    page.wait_for_function('matchMedia("(prefers-color-scheme: light)").matches')
    assert resolved_theme(page) == 'dark'


def test_toggle_wiring_changes_theme(make_page):
    """The documented host-page wiring: a click on the toggle ends up
    in sfTheme.set(), which stamps the document and writes the
    cookie."""
    page = make_page(color_scheme='light')
    page.locator('sf-theme-toggle button', has_text='Dark').click()
    page.wait_for_function('document.documentElement.dataset.theme === "dark"')
    assert sf_theme_cookie(page.context) == 'dark'
    assert page.evaluate('sfTheme.preference') == 'dark'
