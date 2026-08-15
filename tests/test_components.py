"""Browser tests for the sfui components.

Each test drives the real component files in Chromium against the
contracts documented in their file headers: data in through
properties, events out, keyboard operation, and ARIA semantics.
Playwright CSS locators pierce open shadow DOM, which is how the
assertions reach the rendered buttons.
"""

import conftest


conftest.require_playwright()


TABS = '/tests/pages/tabs.html'
TOGGLE = '/tests/pages/toggle.html'
DATA_TABLE = '/tests/pages/data-table.html'


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

    def test_escaping_of_tab_id_with_quotes(self, make_page):
        page = make_page(TABS)
        page.evaluate("""() => {
            const tabs = document.querySelector('sf-tabs');
            tabs.tabs = [
                {id: 'alpha', label: 'Alpha', badge: null},
                {id: 'special"id', label: 'Special', badge: null},
            ];
            tabs.selected = 'alpha';
        }""")
        alpha = page.locator('sf-tabs button', has_text='Alpha')
        alpha.focus()
        alpha.press('ArrowRight')
        page.wait_for_function('window.events.length === 1')
        assert events(page) == [{'id': 'special"id'}]


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


def first_column(page):
    cells = page.locator('sf-data-table tbody tr td:first-child')
    return [text.strip() for text in cells.all_inner_texts()]


def wait_first_row(page, repo):
    page.wait_for_function(
        'document.querySelector("sf-data-table").shadowRoot'
        f'.querySelector("tbody tr td").textContent.trim() === "{repo}"')


class TestSfDataTable:
    def test_renders_headers_and_rows(self, make_page):
        page = make_page(DATA_TABLE)
        headers = page.locator('sf-data-table th')
        assert headers.count() == 5
        assert headers.first.get_attribute('scope') == 'col'
        issues = page.locator('sf-data-table th', has_text='Open Issues')
        assert issues.get_attribute('title') == 'Open issues per repository'
        assert page.locator('sf-data-table tbody tr').count() == 3

    def test_primitive_and_missing_cells(self, make_page):
        page = make_page(DATA_TABLE)
        second = page.locator('sf-data-table tbody tr').nth(1)
        assert second.locator('td').nth(3).inner_text().strip() == 'plain'
        third = page.locator('sf-data-table tbody tr').nth(2)
        assert third.locator('td').nth(4).inner_text().strip() == ''

    def test_num_column_right_aligns(self, make_page):
        page = make_page(DATA_TABLE)
        runs = page.locator('sf-data-table th', has_text='Runs')
        assert runs.evaluate('el => getComputedStyle(el).textAlign') == 'right'
        cell = page.locator('sf-data-table tbody tr').first.locator('td').nth(3)
        assert cell.evaluate('el => getComputedStyle(el).textAlign') == 'right'

    def test_link_parts(self, make_page):
        page = make_page(DATA_TABLE)
        link = page.locator('sf-data-table tbody a').first
        assert link.get_attribute('href') == 'https://example.com/sfui'
        assert link.get_attribute('target') == '_blank'
        assert link.get_attribute('rel') == 'noopener noreferrer'

    def test_tone_maps_to_the_token_color(self, make_page):
        page = make_page(DATA_TABLE)
        amber = page.locator('sf-data-table a.amber').first
        assert amber.evaluate('el => getComputedStyle(el).color') == 'rgb(251, 191, 36)'
        assert amber.get_attribute('title') == '#1, #2, #3'

    def test_badge_ribbon_and_block_parts(self, make_page):
        page = make_page(DATA_TABLE)
        pills = page.locator('sf-data-table .pill')
        assert pills.all_inner_texts() == ['↓ small', 'static']
        ribbon = page.locator('sf-data-table .ribbon')
        assert ribbon.get_attribute('aria-hidden') == 'true'
        assert ribbon.locator('span').count() == 3
        block = page.locator('sf-data-table span', has_text='no data')
        assert block.evaluate('el => getComputedStyle(el).display') == 'block'

    def test_null_parts_are_skipped(self, make_page):
        """The badge cell in the harness carries a null between its two
        badges, the shape a conditional parts list naturally takes."""
        page = make_page(DATA_TABLE)
        cell = page.locator('sf-data-table tbody tr').nth(2).locator('td').nth(2)
        assert cell.locator('.part').count() == 2

    def test_ribbon_boxes_take_tone_backgrounds(self, make_page):
        page = make_page(DATA_TABLE)
        box = page.locator('sf-data-table .ribbon span').first
        color = box.evaluate('el => getComputedStyle(el).backgroundColor')
        assert color == 'rgb(74, 222, 128)'

    def test_toned_button_takes_the_tone(self, make_page):
        page = make_page(DATA_TABLE)
        button = page.locator('sf-data-table button.action:enabled')
        styles = button.evaluate(
            'el => { const s = getComputedStyle(el);'
            '  return [s.color, s.borderTopColor]; }')
        assert styles == ['rgb(248, 113, 113)', 'rgb(248, 113, 113)']

    def test_disabled_button_dims_like_sf_btn(self, make_page):
        page = make_page(DATA_TABLE)
        button = page.locator('sf-data-table button.action[disabled]')
        styles = button.evaluate(
            'el => { const s = getComputedStyle(el);'
            '  return [s.color, s.borderTopColor]; }')
        assert styles == ['rgb(139, 143, 163)', 'rgb(139, 143, 163)']

    def test_caption_names_the_table(self, make_page):
        page = make_page(DATA_TABLE)
        caption = page.locator('sf-data-table caption')
        assert caption.inner_text() == 'Repository activity'

    def test_unsafe_href_schemes_render_as_text(self, make_page):
        """Refusal must survive the control-character spellings the
        WHATWG URL parser strips, and must not catch relative or
        fragment hrefs, which are legitimate links."""
        page = make_page(DATA_TABLE)
        page.evaluate(
            """document.querySelector('sf-data-table').rows = [
                [{text: 'evil', href: 'javascript:alert(1)'},
                 {text: 'sneaky', href: 'java\\tscript:alert(1)'},
                 {text: 'datauri', href: 'data:text/html,x'},
                 {text: 'fine', href: 'https://example.com/'},
                 {text: 'local', href: '#detail'}],
            ]""")
        page.wait_for_function(
            'document.querySelector("sf-data-table").shadowRoot'
            '.querySelectorAll("tbody a").length === 2')
        links = page.locator('sf-data-table tbody a')
        assert links.all_inner_texts() == ['fine', 'local']
        for refused in ('evil', 'sneaky', 'datauri'):
            assert page.locator(
                'sf-data-table tbody span', has_text=refused).count() == 1

    def test_sort_cycle_returns_to_natural_order(self, make_page):
        page = make_page(DATA_TABLE)
        assert first_column(page) == [
            'shakenfist/sfui', 'shakenfist/conductor', 'shakenfist/kerbside']
        header = page.locator('sf-data-table th', has_text='Repository')
        header.locator('button').click()
        wait_first_row(page, 'shakenfist/conductor')
        assert first_column(page) == [
            'shakenfist/conductor', 'shakenfist/kerbside', 'shakenfist/sfui']
        assert header.get_attribute('aria-sort') == 'ascending'
        header.locator('button').click()
        wait_first_row(page, 'shakenfist/sfui')
        assert first_column(page) == [
            'shakenfist/sfui', 'shakenfist/kerbside', 'shakenfist/conductor']
        assert header.get_attribute('aria-sort') == 'descending'
        header.locator('button').click()
        page.wait_for_function('window.events.length === 3')
        assert first_column(page) == [
            'shakenfist/sfui', 'shakenfist/conductor', 'shakenfist/kerbside']
        assert header.get_attribute('aria-sort') == 'none'
        assert events(page) == [
            {'column': 0, 'direction': 'asc'},
            {'column': 0, 'direction': 'desc'},
            {'column': 0, 'direction': None},
        ]

    def test_sorting_never_mutates_the_rows_property(self, make_page):
        page = make_page(DATA_TABLE)
        page.locator(
            'sf-data-table th', has_text='Repository').locator('button').click()
        wait_first_row(page, 'shakenfist/conductor')
        supplied = page.evaluate(
            "document.querySelector('sf-data-table').rows.map(r => r[0].text)")
        assert supplied == [
            'shakenfist/sfui', 'shakenfist/conductor', 'shakenfist/kerbside']

    def test_dropping_the_sorted_column_resets_the_sort(self, make_page):
        page = make_page(DATA_TABLE)
        header = page.locator('sf-data-table th', has_text='Repository')
        header.locator('button').click()
        wait_first_row(page, 'shakenfist/conductor')
        page.evaluate(
            """const table = document.querySelector('sf-data-table');
               const columns = table.columns.slice();
               columns[0] = {label: 'Repository'};
               table.columns = columns;""")
        wait_first_row(page, 'shakenfist/sfui')
        assert first_column(page) == [
            'shakenfist/sfui', 'shakenfist/conductor', 'shakenfist/kerbside']
        assert events(page) == [{'column': 0, 'direction': 'asc'}]

    def test_numeric_sort_uses_sort_values(self, make_page):
        page = make_page(DATA_TABLE)
        header = page.locator('sf-data-table th', has_text='Open Issues')
        header.locator('button').click()
        wait_first_row(page, 'shakenfist/conductor')
        assert first_column(page) == [
            'shakenfist/conductor', 'shakenfist/sfui', 'shakenfist/kerbside']

    def test_missing_sort_keys_sort_last_in_both_directions(self, make_page):
        page = make_page(DATA_TABLE)
        header = page.locator('sf-data-table th', has_text='Failure')
        header.locator('button').click()
        wait_first_row(page, 'shakenfist/kerbside')
        assert first_column(page)[-1] == 'shakenfist/conductor'
        header.locator('button').click()
        wait_first_row(page, 'shakenfist/sfui')
        assert first_column(page)[-1] == 'shakenfist/conductor'

    def test_replacing_rows_keeps_the_sort(self, make_page):
        page = make_page(DATA_TABLE)
        header = page.locator('sf-data-table th', has_text='Repository')
        header.locator('button').click()
        wait_first_row(page, 'shakenfist/conductor')
        page.evaluate(
            """document.querySelector('sf-data-table').rows = [
                [{text: 'zulu', sortValue: 'zulu'}, '0', null, '1', null],
                [{text: 'alpha', sortValue: 'alpha'}, '0', null, '1', null],
            ]""")
        wait_first_row(page, 'alpha')
        assert first_column(page) == ['alpha', 'zulu']
        assert header.get_attribute('aria-sort') == 'ascending'

    def test_action_button_reports_natural_row_index(self, make_page):
        page = make_page(DATA_TABLE)
        header = page.locator('sf-data-table th', has_text='Repository')
        header.locator('button').click()
        wait_first_row(page, 'shakenfist/conductor')
        page.locator('sf-data-table button.action:enabled').click()
        page.wait_for_function('window.events.length === 2')
        assert events(page)[-1] == {
            'action': 'build', 'data': {'name': 'sfui'}, 'rowIndex': 0}

    def test_disabled_button_is_silent(self, make_page):
        """A synthetic click event, not el.click(): the browser drops
        activations of a disabled button before listeners run, so
        only a dispatched event reaches the component's guard."""
        page = make_page(DATA_TABLE)
        disabled = page.locator('sf-data-table button.action[disabled]')
        assert disabled.count() == 1
        disabled.evaluate('el => el.dispatchEvent(new MouseEvent("click"))')
        assert events(page) == []

    def test_programmatic_assignments_are_silent(self, make_page):
        page = make_page(DATA_TABLE)
        page.evaluate(
            """const table = document.querySelector('sf-data-table');
               table.columns = table.columns.slice();
               table.rows = table.rows.slice();
               table.footnote = 'changed';""")
        page.wait_for_function(
            'document.querySelector("sf-data-table").shadowRoot'
            '.querySelector(".footnote").textContent === "changed"')
        assert events(page) == []

    def test_sort_survives_the_empty_state(self, make_page):
        """The documented reason emptyText exists: a rows -> [] -> rows
        round trip through the empty state keeps the viewer's sort."""
        page = make_page(DATA_TABLE)
        header = page.locator('sf-data-table th', has_text='Repository')
        header.locator('button').click()
        wait_first_row(page, 'shakenfist/conductor')
        page.evaluate(
            """const table = document.querySelector('sf-data-table');
               window.savedRows = table.rows;
               table.rows = [];
               table.emptyText = 'nothing';""")
        page.locator('sf-data-table .empty').wait_for()
        page.evaluate(
            "document.querySelector('sf-data-table').rows = window.savedRows")
        wait_first_row(page, 'shakenfist/conductor')
        assert header.get_attribute('aria-sort') == 'ascending'

    def test_sort_key_falls_back_to_first_part_text(self, make_page):
        """No sortValue anywhere: case-insensitive text comparison of
        the first part's text, with ties kept in natural order."""
        page = make_page(DATA_TABLE)
        page.evaluate(
            """document.querySelector('sf-data-table').rows = [
                [{text: 'Gamma'}, {text: 'tie'}, null, null, null],
                [{text: 'alpha'}, {text: 'tie'}, null, null, null],
                [{text: 'Beta'}, {text: 'tie'}, null, null, null],
            ]""")
        wait_first_row(page, 'Gamma')
        page.locator(
            'sf-data-table th', has_text='Repository').locator('button').click()
        wait_first_row(page, 'alpha')
        assert first_column(page) == ['alpha', 'Beta', 'Gamma']
        page.locator(
            'sf-data-table th', has_text='Open Issues').locator('button').click()
        wait_first_row(page, 'Gamma')
        assert first_column(page) == ['Gamma', 'alpha', 'Beta']

    def test_empty_rows_without_empty_text_render_nothing(self, make_page):
        page = make_page(DATA_TABLE)
        page.evaluate("document.querySelector('sf-data-table').rows = []")
        page.wait_for_function(
            'document.querySelector("sf-data-table").shadowRoot'
            '.querySelector("table") === null')
        assert page.locator('sf-data-table .empty').count() == 0
        assert page.locator('sf-data-table .footnote').count() == 0

    def test_idle_sortable_headers_announce_none(self, make_page):
        page = make_page(DATA_TABLE)
        sortable = page.locator('sf-data-table th', has_text='Repository')
        assert sortable.get_attribute('aria-sort') == 'none'
        fixed = page.locator('sf-data-table th', has_text='Actions')
        assert fixed.get_attribute('aria-sort') is None

    def test_empty_rows_render_the_empty_text(self, make_page):
        page = make_page(DATA_TABLE)
        page.evaluate(
            """const table = document.querySelector('sf-data-table');
               table.rows = [];
               table.emptyText = 'Nothing queued';""")
        empty = page.locator('sf-data-table .empty')
        empty.wait_for()
        assert empty.inner_text().strip() == 'Nothing queued'
        assert page.locator('sf-data-table table').count() == 0
        assert page.locator('sf-data-table .footnote').count() == 0

    def test_footnote_presence_follows_the_property(self, make_page):
        page = make_page(DATA_TABLE)
        footnote = page.locator('sf-data-table .footnote')
        assert footnote.inner_text().strip() == 'A footnote about the table.'
        page.evaluate("document.querySelector('sf-data-table').footnote = ''")
        page.wait_for_function(
            'document.querySelector("sf-data-table").shadowRoot'
            '.querySelector(".footnote") === null')


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
