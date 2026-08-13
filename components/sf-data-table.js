/**
 * <sf-data-table> -- the Shaken Fist data table.
 *
 * Data in, events out. The component owns presentation and
 * interaction (rendering cells, column sorting, action
 * buttons) and knows nothing about what the data means: what
 * a count links to, which tone a status deserves, what an
 * action does -- that judgement belongs to the page, which
 * maps its own state onto the descriptors below. The split is
 * what makes the table reusable across Shaken Fist UIs, and
 * it is also why cells are structured descriptors rather than
 * markup: the page never hands the component HTML, so cell
 * content is always rendered as text.
 *
 * Properties:
 *   columns    Array of {label, align, sortable, title}.
 *              `align: 'num'` right-aligns the column for
 *              numeric data; anything else is left-aligned.
 *              `sortable: true` makes the header a button the
 *              viewer can sort by. `title` becomes a header
 *              tooltip. All but `label` are optional.
 *   rows       Array of rows, one array of cells per row, in
 *              the order the page considers natural (the
 *              order sorting returns to). A cell is either a
 *              primitive, rendered as plain text, or an
 *              object {sortValue, parts} where each part is
 *              one of:
 *                {text, tone, href, title, small, block}
 *                  a text span; with `href` a link opened in
 *                  a new tab. `small` shrinks it, `block`
 *                  puts it on its own line.
 *                {badge: text, tone, title}
 *                  an outline pill.
 *                {ribbon: [tone, ...], title}
 *                  a row of small boxes, one per entry -- a
 *                  decorative sparkline, hidden from
 *                  assistive tech, so pair it with a textual
 *                  part.
 *                {button: {label, action, data, disabled,
 *                          tone}}
 *                  an action button; see the event below.
 *              An object cell without `parts` is treated as a
 *              single part. Tones are 'accent', 'green',
 *              'amber', 'red', 'purple', 'pink', 'teal',
 *              'orange' or 'dim', naming the matching design
 *              token; anything else falls back to the default
 *              text color.
 *   emptyText  Message shown instead of the table when `rows`
 *              is empty (nothing at all is rendered when this
 *              is empty too). Keeping the element in the DOM
 *              and setting this, rather than swapping the
 *              element out for a message, is what preserves
 *              sort state across refreshes. Also settable as
 *              the empty-text attribute.
 *   footnote   Small dim text under the table when non-empty.
 *
 * Sorting never mutates `rows`: the component renders a
 * sorted view, so a page replacing `rows` on a poll tick
 * keeps the viewer's chosen order. A header click cycles
 * ascending, descending, then back to the natural order. The
 * sort key for a cell is `sortValue` when present, the cell
 * itself for primitives, else the first part's text or badge;
 * numbers compare numerically when both keys are numbers,
 * anything else compares as case-insensitive text, and
 * missing keys sort last in both directions.
 *
 * Events:
 *   sf-data-table-action  Fired when an enabled button part
 *                         is clicked, with {detail: {action,
 *                         data, rowIndex}}. `rowIndex` indexes
 *                         `rows` as supplied (natural order);
 *                         `data` is the page's own payload and
 *                         the reliable channel. What the
 *                         action does belongs to the page; the
 *                         table only reports the click.
 *   sf-data-table-sort    Fired on user sort changes (never
 *                         when the page replaces data), with
 *                         {detail: {column, direction}} where
 *                         direction is 'asc', 'desc' or null
 *                         for the return to natural order.
 *
 * Styling comes entirely from the sfui design tokens
 * (../tokens.css), with fallbacks matching the token defaults
 * so the table degrades sanely on a page that forgot the
 * stylesheet.
 */
import {css, html, LitElement, nothing} from '../lit-core.min.js';

const TONES = [
    'accent',
    'green',
    'amber',
    'red',
    'purple',
    'pink',
    'teal',
    'orange',
    'dim',
];

class SfDataTable extends LitElement {
    static properties = {
        columns: {attribute: false},
        rows: {attribute: false},
        emptyText: {type: String, attribute: 'empty-text'},
        footnote: {type: String},
        _sortColumn: {state: true},
        _sortDir: {state: true},
    };

    /*
     * sf.css's .sf-table is the CSS-only version of this look,
     * for server-rendered pages, and the th/td rules below copy
     * it measurement for measurement. The two must stay visually
     * in step: a change here belongs there as well.
     */
    static styles = css`
        :host {
            display: block;
        }
        .scroll {
            max-width: 100%;
            overflow-x: auto;
        }
        table {
            width: 100%;
            min-width: max-content;
            border-collapse: collapse;
        }
        th,
        td {
            text-align: left;
            padding: var(--sf-table-cell-pad, 0.5rem 0.8rem);
            border-bottom: 1px solid var(--sf-border, #2a2d3a);
            font-size: 0.88rem;
        }
        th {
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--sf-text-dim, #8b8fa3);
        }
        td {
            font-family: var(
                --sf-font-mono,
                "SF Mono",
                Consolas,
                "Liberation Mono",
                monospace
            );
        }
        tbody tr:hover {
            background: color-mix(
                in srgb,
                var(--sf-accent, #6c9eff) 8%,
                transparent
            );
        }
        th.num,
        td.num {
            text-align: right;
        }
        th button {
            appearance: none;
            background: none;
            border: none;
            color: inherit;
            cursor: pointer;
            font: inherit;
            letter-spacing: inherit;
            text-transform: inherit;
            padding: 0;
        }
        th button:hover {
            color: var(--sf-text, #e1e4ed);
        }
        .arrow {
            margin-left: 0.35em;
        }
        a {
            color: var(--sf-accent, #6c9eff);
            text-decoration: none;
        }
        a:hover {
            color: var(--sf-accent-hover, #8bb4ff);
            text-decoration: underline;
        }
        .part + .part {
            margin-left: 0.45em;
        }
        .part + .part.block {
            margin-left: 0;
        }
        .block {
            display: block;
        }
        .small {
            font-size: 0.8em;
        }
        .pill {
            border: 1px solid currentColor;
            border-radius: var(--sf-radius-sm, 4px);
            font-size: 0.78rem;
            font-weight: 600;
            padding: 1px 7px;
            white-space: nowrap;
        }
        .ribbon {
            display: inline-flex;
            gap: 2px;
        }
        .ribbon span {
            width: 3px;
            height: 8px;
            border-radius: 1px;
            color: var(--sf-text-dim, #8b8fa3);
            background: currentColor;
        }
        button.action {
            appearance: none;
            background: none;
            border: 1px solid currentColor;
            border-radius: var(--sf-radius-sm, 4px);
            color: var(--sf-text-dim, #8b8fa3);
            cursor: pointer;
            font: inherit;
            font-size: 0.78rem;
            padding: 2px 10px;
        }
        button.action:hover:enabled {
            background: color-mix(
                in srgb,
                currentColor 12%,
                transparent
            );
        }
        button.action:disabled {
            cursor: default;
            opacity: 0.5;
        }
        .empty {
            color: var(--sf-text-dim, #8b8fa3);
            font-size: 0.88rem;
            padding: 2rem;
            text-align: center;
        }
        .footnote {
            color: var(--sf-text-dim, #8b8fa3);
            font-size: 0.78rem;
            margin: 0.6rem 0 0;
        }
        .accent,
        a.accent:hover {
            color: var(--sf-accent, #6c9eff);
        }
        .green,
        a.green:hover {
            color: var(--sf-green, #4ade80);
        }
        .amber,
        a.amber:hover {
            color: var(--sf-amber, #fbbf24);
        }
        .red,
        a.red:hover {
            color: var(--sf-red, #f87171);
        }
        .purple,
        a.purple:hover {
            color: var(--sf-purple, #a78bfa);
        }
        .pink,
        a.pink:hover {
            color: var(--sf-pink, #f472b6);
        }
        .teal,
        a.teal:hover {
            color: var(--sf-teal, #2dd4bf);
        }
        .orange,
        a.orange:hover {
            color: var(--sf-orange, #fb923c);
        }
        .dim,
        a.dim:hover {
            color: var(--sf-text-dim, #8b8fa3);
        }
    `;

    constructor() {
        super();
        this.columns = [];
        this.rows = [];
        this.emptyText = '';
        this.footnote = '';
        this._sortColumn = null;
        this._sortDir = null;
    }

    render() {
        const rows = this.rows || [];
        if (!rows.length) {
            if (!this.emptyText) {
                return nothing;
            }
            return html`<div class="empty">${this.emptyText}</div>`;
        }
        const columns = this.columns || [];
        return html`
            <div class="scroll">
                <table>
                    <thead>
                        <tr>
                            ${columns.map((column, index) =>
                                this._headerCell(column, index),
                            )}
                        </tr>
                    </thead>
                    <tbody>
                        ${this._sortedView(rows).map(
                            (entry) => html`
                            <tr>
                                ${entry.row.map((cell, index) =>
                                    this._bodyCell(
                                        cell,
                                        index,
                                        entry.index,
                                    ),
                                )}
                            </tr>`,
                        )}
                    </tbody>
                </table>
            </div>
            ${
                this.footnote
                    ? html`<p class="footnote">${this.footnote}</p>`
                    : nothing
            }`;
    }

    _headerCell(column, index) {
        const cls = column.align === 'num' ? 'num' : nothing;
        const title = column.title || nothing;
        if (!column.sortable) {
            return html`
                <th scope="col" class=${cls} title=${title}>
                    ${column.label}</th>`;
        }
        const active =
            this._sortColumn === index && this._sortDir !== null;
        return html`
            <th scope="col"
                class=${cls}
                title=${title}
                aria-sort=${
                    active
                        ? this._sortDir === 'asc'
                            ? 'ascending'
                            : 'descending'
                        : nothing
                }>
                <button @click=${() => this._sort(index)}>
                    ${column.label}${
                        active
                            ? html`<span class="arrow"
                                  aria-hidden="true">${
                                      this._sortDir === 'asc'
                                          ? '▲'
                                          : '▼'
}</span>`
                            : nothing
                    }
                </button>
            </th>`;
    }

    _bodyCell(cell, columnIndex, rowIndex) {
        const column = (this.columns || [])[columnIndex] || {};
        const cls = column.align === 'num' ? 'num' : nothing;
        if (cell === null || cell === undefined) {
            return html`<td class=${cls}></td>`;
        }
        if (typeof cell !== 'object') {
            return html`<td class=${cls}>${cell}</td>`;
        }
        const parts = cell.parts || [cell];
        return html`
            <td class=${cls}>
                ${parts.map((part) => this._part(part, rowIndex))}
            </td>`;
    }

    _part(part, rowIndex) {
        if (part.button) {
            return this._buttonPart(part.button, rowIndex);
        }
        if (part.ribbon) {
            return this._ribbonPart(part);
        }
        if (part.badge !== undefined) {
            return this._badgePart(part);
        }
        return this._textPart(part);
    }

    _classes(part, extra) {
        const names = ['part'].concat(extra || []);
        if (TONES.includes(part.tone)) {
            names.push(part.tone);
        }
        if (part.small) {
            names.push('small');
        }
        if (part.block) {
            names.push('block');
        }
        return names.join(' ');
    }

    _textPart(part) {
        const title = part.title || nothing;
        if (part.href) {
            return html`<a class=${this._classes(part)}
                href=${part.href}
                target="_blank"
                rel="noopener"
                title=${title}>${part.text}</a>`;
        }
        return html`<span class=${this._classes(part)}
            title=${title}>${part.text}</span>`;
    }

    _badgePart(part) {
        return html`<span class=${this._classes(part, ['pill'])}
            title=${part.title || nothing}>${part.badge}</span>`;
    }

    _ribbonPart(part) {
        return html`<span class="part ribbon"
            aria-hidden="true"
            title=${part.title || nothing}>${part.ribbon.map(
                (tone) =>
                    html`<span class=${
                        TONES.includes(tone) ? tone : nothing
                    }></span>`,
            )}</span>`;
    }

    _buttonPart(spec, rowIndex) {
        return html`<button
            class=${this._classes(spec, ['action'])}
            ?disabled=${Boolean(spec.disabled)}
            @click=${() => this._action(spec, rowIndex)}>${
                spec.label
            }</button>`;
    }

    _action(spec, rowIndex) {
        if (spec.disabled) {
            return;
        }
        this.dispatchEvent(
            new CustomEvent('sf-data-table-action', {
                detail: {
                    action: spec.action,
                    data: spec.data || {},
                    rowIndex,
                },
                bubbles: true,
                composed: true,
            }),
        );
    }

    _sort(index) {
        if (this._sortColumn !== index) {
            this._sortColumn = index;
            this._sortDir = 'asc';
        } else if (this._sortDir === 'asc') {
            this._sortDir = 'desc';
        } else {
            this._sortColumn = null;
            this._sortDir = null;
        }
        this.dispatchEvent(
            new CustomEvent('sf-data-table-sort', {
                detail: {column: index, direction: this._sortDir},
                bubbles: true,
                composed: true,
            }),
        );
    }

    _sortedView(rows) {
        const entries = rows.map((row, index) => ({row, index}));
        if (this._sortColumn === null || this._sortDir === null) {
            return entries;
        }
        const column = this._sortColumn;
        const direction = this._sortDir === 'desc' ? -1 : 1;
        entries.sort((a, b) => {
            const keyA = this._sortKey(a.row[column]);
            const keyB = this._sortKey(b.row[column]);
            const missingA = this._missing(keyA);
            const missingB = this._missing(keyB);
            if (missingA || missingB) {
                if (missingA && missingB) {
                    return a.index - b.index;
                }
                return missingA ? 1 : -1;
            }
            const order = this._compare(keyA, keyB) * direction;
            return order !== 0 ? order : a.index - b.index;
        });
        return entries;
    }

    _sortKey(cell) {
        if (cell === null || cell === undefined) {
            return null;
        }
        if (typeof cell !== 'object') {
            return cell;
        }
        if ('sortValue' in cell) {
            return cell.sortValue;
        }
        const first = (cell.parts || [cell])[0] || {};
        if (first.text !== undefined) {
            return first.text;
        }
        if (first.badge !== undefined) {
            return first.badge;
        }
        return null;
    }

    _missing(key) {
        return (
            key === null ||
            key === undefined ||
            (typeof key === 'number' && Number.isNaN(key))
        );
    }

    _compare(keyA, keyB) {
        if (typeof keyA === 'number' && typeof keyB === 'number') {
            return keyA - keyB;
        }
        const textA = String(keyA).toLowerCase();
        const textB = String(keyB).toLowerCase();
        if (textA < textB) {
            return -1;
        }
        return textA > textB ? 1 : 0;
    }
}

customElements.define('sf-data-table', SfDataTable);
