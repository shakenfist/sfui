"""Browser tests for the sf.css primitives that have behaviour.

Most of sf.css is appearance, which demo.html is for. The dialog is
the exception: showModal(), the top layer and ::backdrop are
platform behaviour the stylesheet has to work with, so the tests
open it the way docs/page-styles.md tells a page to and check the
result in both palettes.
"""

import pytest

import conftest


playwright_api = conftest.require_playwright()


DIALOG = '/tests/pages/dialog.html'

TRANSPARENT = 'rgba(0, 0, 0, 0)'


def backdrop_background(page):
    return page.evaluate(
        'getComputedStyle(document.getElementById("dialog"), "::backdrop").backgroundColor')


def open_modal(page):
    page.locator('#opener').click()
    page.wait_for_function('document.getElementById("dialog").open === true')


@pytest.mark.parametrize('scheme', ['light', 'dark'])
class TestSfDialog:
    def test_the_palette_is_the_one_asked_for(self, make_page, scheme):
        page = make_page(DIALOG, color_scheme=scheme)
        assert page.evaluate('document.documentElement.dataset.theme') == scheme

    def test_show_modal_opens_over_a_backdrop(self, make_page, scheme):
        page = make_page(DIALOG, color_scheme=scheme)
        open_modal(page)
        assert page.evaluate('document.getElementById("dialog").matches(":modal")')
        themed = backdrop_background(page)
        assert themed != TRANSPARENT
        # The user agent's own backdrop is not transparent either, so
        # also prove the value is sf.css's rather than the default.
        page.evaluate('document.getElementById("dialog").classList.remove("sf-dialog")')
        assert backdrop_background(page) != themed

    def test_backdrop_survives_an_unresolved_token(self, make_page, scheme):
        # Current Chromium inherits custom properties into ::backdrop
        # from the dialog, so making --sf-bg guaranteed-invalid there
        # reproduces what an older engine sees: the fallback, not a
        # transparent backdrop. Such an engine does not inherit
        # color-scheme either, so resetting it too gives Canvas the
        # light scheme's white in both palettes -- the worst case
        # the sf.css comment describes.
        page = make_page(DIALOG, color_scheme=scheme)
        open_modal(page)
        themed = backdrop_background(page)
        page.evaluate('document.getElementById("dialog").style.setProperty("--sf-bg", "initial")')
        page.evaluate('document.getElementById("dialog").style.setProperty("color-scheme", "normal")')
        fallback = backdrop_background(page)
        assert fallback != TRANSPARENT
        assert fallback != themed

    def test_modal_is_centered_in_the_viewport(self, make_page, scheme):
        # The .sf-page reset zeroes margins, and a modal dialog is
        # centered by the user agent's auto margin.
        page = make_page(DIALOG, color_scheme=scheme)
        open_modal(page)
        box = page.locator('#dialog').bounding_box()
        viewport = page.viewport_size
        assert abs(box['x'] - (viewport['width'] - box['x'] - box['width'])) < 1
        assert abs(box['y'] - (viewport['height'] - box['y'] - box['height'])) < 1

    def test_escape_closes_it(self, make_page, scheme):
        page = make_page(DIALOG, color_scheme=scheme)
        open_modal(page)
        page.keyboard.press('Escape')
        page.wait_for_function('document.getElementById("dialog").open === false')

    def test_enter_in_a_field_submits_the_primary_button(self, make_page, scheme):
        # Implicit submission uses the form's first submit button in
        # tree order. Cancel comes first in .sf-form-actions, so it
        # must be type="button" or Enter would mean Cancel.
        page = make_page(DIALOG, color_scheme=scheme)
        open_modal(page)
        page.locator('#regexp').fill('^nova/')
        page.locator('#regexp').press('Enter')
        page.wait_for_function('document.getElementById("dialog").open === false')
        return_value = page.evaluate('document.getElementById("dialog").returnValue')
        assert return_value == 'save', f'Enter closed the dialog with returnValue {return_value!r}, not the primary button'

    def test_invalid_field_keeps_red_under_keyboard_focus(self, make_page, scheme):
        # Opened from the keyboard, showModal() focuses the invalid
        # field, which then matches :focus-visible. The invalid rule
        # follows the focus rule in sf.css, so the border stays red.
        page = make_page(DIALOG, color_scheme=scheme)
        page.locator('#opener').focus()
        page.keyboard.press('Enter')
        page.wait_for_function('document.getElementById("dialog").open === true')
        assert page.evaluate('document.activeElement.id') == 'regexp'
        assert page.evaluate('document.getElementById("regexp").matches(":focus-visible")')
        red = page.evaluate('getComputedStyle(document.getElementById("red-probe")).color')
        border = page.evaluate('getComputedStyle(document.getElementById("regexp")).borderTopColor')
        assert border == red, f'focused invalid field border is {border}, not --sf-red {red}'

    def test_invalid_field_border_is_the_red_token(self, make_page, scheme):
        page = make_page(DIALOG, color_scheme=scheme)
        open_modal(page)
        red = page.evaluate('getComputedStyle(document.getElementById("red-probe")).color')
        border = page.evaluate('getComputedStyle(document.getElementById("regexp")).borderTopColor')
        assert border == red
