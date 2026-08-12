"""Browser tests for the sfui components.

Each test drives the real component files in Chromium against the
contracts documented in their file headers: data in through
properties, events out, keyboard operation, and ARIA semantics.
Playwright CSS locators pierce open shadow DOM, which is how the
assertions reach the rendered buttons.
"""

import pytest


pytest.importorskip('playwright.sync_api')


TABS = '/tests/pages/tabs.html'
TOGGLE = '/tests/pages/toggle.html'


def events(page):
    return page.evaluate('window.events')


class TestSfTabs:
    def test_renders_a_button_per_tab(self, make_page):
        page = make_page(TABS)
        buttons = page.locator('sf-tabs button')
        assert buttons.count() == 3
        assert buttons.all_inner_texts()[0].strip() == 'Alpha'
        nav = page.locator('sf-tabs nav')
        assert nav.get_attribute('role') == 'tablist'

    def test_selection_semantics(self, make_page):
        page = make_page(TABS)
        alpha = page.locator('sf-tabs button', has_text='Alpha')
        assert alpha.get_attribute('aria-selected') == 'true'
        assert alpha.get_attribute('tabindex') == '0'
        beta = page.locator('sf-tabs button', has_text='Beta')
        assert beta.get_attribute('aria-selected') == 'false'
        assert beta.get_attribute('tabindex') == '-1'

    def test_click_selects_and_reports(self, make_page):
        page = make_page(TABS)
        page.locator('sf-tabs button', has_text='Beta').click()
        page.wait_for_function('window.events.length === 1')
        assert events(page) == [{'id': 'beta'}]
        assert page.locator('sf-tabs').get_attribute('selected') == 'beta'

    def test_reselecting_the_selected_tab_is_silent(self, make_page):
        page = make_page(TABS)
        page.locator('sf-tabs button', has_text='Alpha').click()
        assert events(page) == []

    def test_programmatic_selection_is_silent(self, make_page):
        page = make_page(TABS)
        page.evaluate('document.querySelector("sf-tabs").selected = "gamma"')
        page.wait_for_function(
            'document.querySelector("sf-tabs").getAttribute("selected") === "gamma"')
        assert events(page) == []

    def test_arrow_keys_move_selection_and_focus(self, make_page):
        page = make_page(TABS)
        alpha = page.locator('sf-tabs button', has_text='Alpha')
        alpha.focus()
        alpha.press('ArrowRight')
        page.wait_for_function('window.events.length === 1')
        assert events(page) == [{'id': 'beta'}]
        focused = page.evaluate(
            'document.querySelector("sf-tabs").shadowRoot.activeElement.dataset.id')
        assert focused == 'beta'

    def test_arrow_left_wraps_to_the_last_tab(self, make_page):
        page = make_page(TABS)
        alpha = page.locator('sf-tabs button', has_text='Alpha')
        alpha.focus()
        alpha.press('ArrowLeft')
        page.wait_for_function('window.events.length === 1')
        assert events(page) == [{'id': 'gamma'}]

    def test_count_badge_renders_a_severity_pill(self, make_page):
        page = make_page(TABS)
        badge = page.locator('sf-tabs button', has_text='Beta').locator('.badge')
        assert badge.inner_text().strip() == '3'
        assert 'urgent' in badge.get_attribute('class')

    def test_unknown_severity_falls_back_to_info_dot(self, make_page):
        page = make_page(TABS)
        badge = page.locator('sf-tabs button', has_text='Gamma').locator('.badge')
        classes = badge.get_attribute('class')
        assert 'dot' in classes
        assert 'info' in classes
        assert badge.get_attribute('aria-hidden') == 'true'


class TestSfThemeToggle:
    def test_renders_a_radiogroup_with_auto_checked(self, make_page):
        page = make_page(TOGGLE)
        group = page.locator('sf-theme-toggle [role="radiogroup"]')
        assert group.get_attribute('aria-label') == 'Color theme'
        auto = page.locator('sf-theme-toggle button', has_text='Auto')
        assert auto.get_attribute('aria-checked') == 'true'
        assert page.locator('sf-theme-toggle button').count() == 3

    def test_click_reports_and_reflects(self, make_page):
        page = make_page(TOGGLE)
        page.locator('sf-theme-toggle button', has_text='Light').click()
        page.wait_for_function('window.events.length === 1')
        assert events(page) == [{'preference': 'light'}]
        assert page.locator('sf-theme-toggle').get_attribute('preference') == 'light'

    def test_programmatic_preference_is_silent(self, make_page):
        page = make_page(TOGGLE)
        page.evaluate('document.querySelector("sf-theme-toggle").preference = "dark"')
        page.wait_for_function(
            'document.querySelector("sf-theme-toggle").getAttribute("preference") === "dark"')
        assert events(page) == []

    def test_arrow_keys_cycle_with_wrap(self, make_page):
        page = make_page(TOGGLE)
        auto = page.locator('sf-theme-toggle button', has_text='Auto')
        auto.focus()
        auto.press('ArrowLeft')
        page.wait_for_function('window.events.length === 1')
        assert events(page) == [{'preference': 'dark'}]

    def test_never_touches_cookies_or_the_document(self, make_page):
        """The component contract: the toggle reports choices and
        changes nothing itself -- theming is the page's job."""
        page = make_page(TOGGLE)
        page.locator('sf-theme-toggle button', has_text='Dark').click()
        page.wait_for_function('window.events.length === 1')
        assert page.context.cookies() == []
        assert page.evaluate('document.documentElement.dataset.theme') is None


class TestDemoPage:
    def test_demo_loads_clean_in_both_themes(self, make_page):
        page = make_page('/demo.html')
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
        page.reload()
        page.wait_for_function('document.querySelector("sf-tabs").shadowRoot !== null')
        for preference in ('light', 'dark'):
            page.evaluate(f'sfTheme.set("{preference}")')
            page.wait_for_function(
                f'document.documentElement.dataset.theme === "{preference}"')
        assert errors == []
