Thanks for your work on this. I appreciate it. Some final
checks before I push.

## How to use this runbook

The pre-push audit splits into two waves:

**Wave 1 — mechanical.** Lint, the consistency checker, and
the test suite. Everything here is also what CI runs, so a
wave 1 failure would fail the pull request anyway; catching
it now is cheaper. Always run wave 1 first; wave 2 is only
worth spending on if wave 1 passes.

**Wave 2 — judgment.** Design-system conformance, code
quality, and documentation review. These need a reader, not
a grep.

## Wave 1: Mechanical checks

```
pre-commit run --all-files
```

runs shellcheck, actionlint, Biome (JavaScript and CSS lint
plus format checking), file hygiene, and
`tools/consistency-check.py` (the mechanical design-system
rules from docs/consistency-audit.md). Then run the test
suite (setup instructions are in docs/testing.md):

```
pytest tests/
```

If either fails, fix the cause and re-run before spending on
wave 2.

## Wave 2: Judgment checks

### Design-system conformance

Review the diff against the parts of the contract no checker
can prove:

- A new or changed component keeps application judgement out:
  data in through properties, events out, and the *meaning* of
  the data stays the host page's problem
  (docs/components.md).
- New colors are semantic token choices, not "looks right
  next to the thing beside it" (docs/design-tokens.md).
- A new primitive or component is rendered in `demo.html`, and
  has been looked at in **both** palettes: serve the
  repository root (`python3 -m http.server`) and flip the
  theme toggle. The consistency checker proves presence, not
  appearance.
- Anything added to the distributable set is in
  `tools/vendor.sh`'s file list and the Layout list in
  `docs/vendoring.md` (the checker cross-checks these, but
  whether a file *should* be distributable is judgment).

### Code quality

<!-- shared-block: comment-proportion v1 -->
Comment proportion (shared block; do not edit -- the canonical
copy lives in shakenfist/development at
`templates/shared-blocks/comment-proportion.md`):

- A comment or docstring earns its length by saying what the code
  cannot: the contract, the units, the failure modes, the reason a
  surprising choice is correct. Restating the code in prose is not
  documentation.
- Treat as candidates any added comment or docstring that is longer
  than the code it documents, and any comment block over roughly
  fifteen lines attached to a body under ten. These are candidates,
  not verdicts -- a subtle algorithm, a public API contract, or a
  hard-won bug explanation can justify the length.
- Where the length is not justified the finding is advisory, and
  the fix is to cut the restatement rather than delete the comment:
  keep the why, drop the line-by-line narration of the what.
- Prose that documents user-visible behaviour rather than the
  implementation usually belongs in `docs/`, with the comment
  reduced to a pointer.
<!-- shared-block-end -->

### Documentation review

Changes to component contracts belong in the component file
headers; changes to the system itself belong in `docs/`. A
user-visible change with no docs diff is a finding.

<!-- shared-block: readme-discipline v1 -->
README discipline (shared block; do not edit -- the canonical
copy lives in shakenfist/development at
`templates/shared-blocks/readme-discipline.md`):

- New user-visible features are documented in `docs/` (and
  `ARCHITECTURE.md` / `AGENTS.md` where appropriate), not by
  adding bullets to `README.md`.
- `README.md` is a pitch: what the project is, who it is for,
  minimal installation instructions, a small number of usage
  examples, and curated absolute links into `docs/`. It only
  changes when the pitch, the install story, or the
  documentation links change.
- README growth is itself a finding: if the diff adds README
  content that belongs in `docs/`, flag it as blocking and
  move it.
<!-- shared-block-end -->

Remember that `README.md` ships in every vendored copy, so a
README change lands in every consumer's static assets on
their next re-vendor.

The management session reviews all findings, fixes any
issues, and confirms the push.
