---
title: Screen-reader and keyboard review protocol
description: Human-executed accessibility acceptance checklist for the eyetrajectoriespy MkDocs Material documentation, including search, navigation, math, scientific diagrams and interactive tools.
---

# Manual accessibility review — protocol, not a certification

**Status: human review not yet performed or signed off.** The automated
Playwright and axe-core jobs are engineering screens only. A successful
workflow cannot establish WCAG 2.2 AA conformance, screen-reader usability, or
whether scientific equations and figures communicate their meaning.

This review follows the W3C's
[WCAG 2.2 standard](https://www.w3.org/TR/WCAG22/) and
[focus visible](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible) /
[focus not obscured](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum)
guidance. For assistive technology, use the actual OS and browser pairing;
do not equate Chromium's accessibility tree with spoken screen-reader output.

## Human testing matrix

Record actual browser, assistive technology version and configuration in the
results. **Do not fill outcomes from CI output.**

| Environment | Required manual scope |
|---|---|
| Windows + NVDA + Firefox | Heading/landmark navigation, search suggestions, live result announcements, content hierarchy, math |
| Windows + NVDA + Chrome | Keyboard focus order, sticky navigation, code blocks, interactive tools |
| macOS + VoiceOver + Safari | Landmark and rotor navigation, menu/drawer, search, theme switching |
| Mobile Android + TalkBack + Chrome (or iOS + VoiceOver + Safari) | Drawer, search, visible headings, focus restoration, zoom/reflow |

If a pairing is unavailable, record **not tested**, not pass. Review with
100%, 200% and 400% zoom/reflow where supported, light and dark themes,
and reduced-motion preference. Explicitly note which combinations were tested.

## Acceptance tasks

Use a keyboard alone first; repeat the tasks with actual screen-reader
speech enabled and inspect what is *announced*, not just DOM attributes.

| ID | Reader task and URL | What the reviewer must observe |
|---|---|---|
| A01 | Open [homepage](../index.md), press Tab | Main content access is discoverable; focus indicator remains visible, unobscured, with sensible sequence |
| A02 | Open [Find a topic](../start/find-a-topic.md), navigate headings and table | Heading levels, row/column relationships and link purposes are understandable |
| A03 | From homepage, press / then type `sparse fpca` | Search input is announced with a name; results and any count/state changes are perceivable without visual inspection |
| A04 | Use Up/Down, Enter, Escape in the search overlay | Selected item, activation, exit, focus restoration and no focus trap |
| A05 | Navigate the [first analysis](../start/first-analysis.md) and [guide index](../guides/index.md) | Main/breadcrumb/side navigation landmarks are navigable; headings are meaningful |
| A06 | On mobile, expand and collapse the navigation drawer | Toggle's accessible name/state is spoken; the drawer is operable; focus remains logical |
| A07 | Open [mathematical reference](../methods/mathematical-reference.md) | Equations can be read or a usable alternative is provided; do not infer math speech from visual MathJax rendering |
| A08 | Explore [scientific figures](../tools/figure-storyboard.md) | Each visual has a useful text description/caption and filter changes are understandable |
| A09 | Operate [integration navigator](../integrations/navigator.md) | Filter/control labels, option state, link purpose and status boundaries are perceivable |
| A10 | Operate [CSV readiness](../tools/data-readiness.md) with a local, non-sensitive sample | Controls, errors, result announcements and privacy explanation work via assistive technology |
| A11 | Read [limitations](../methods/limitations.md) and [research evidence](../research/index.md) | Caveats, negative findings and experimental/released boundaries are not conveyed only by color |
| A12 | Re-test A01–A04 in dark mode and at 200–400% zoom | No hidden focused controls, overlapping search results or lost functional content |

## Evidence worksheet — fill after a real review

Copy one row per **task × device/browser/assistive technology**.
Do not erase failures or convert untested checks into passes.

| Date (UTC) | Tester | Task | OS / browser / AT versions | Observation / spoken output | Result | Severity | Reproduction / screenshot |
|---|---|---|---|---|---|---|---|
| _not recorded_ | _unassigned_ | _pending_ | _not tested_ | _not observed_ | **NOT TESTED** | — | — |

Use results **PASS / FAIL / BLOCKED / NOT TESTED**. Severity for failures:
**critical** (task impossible or misleading safety/scientific interpretation),
**serious** (major functionality obstructed), **moderate**, **minor**. Document
the first wrong step and expected behavior for every failure. Link a GitHub
issue or repair PR. Re-test failed tasks against the exact deployed Pages
commit and log both initial and corrected outcomes.

## Sign-off gates

- [ ] Named human tester and tested assistive-technology combinations recorded.
- [ ] All 12 tasks executed with real spoken output; untested pairings explicitly recorded.
- [ ] No unresolved critical/serious blockers for tasks in the tested matrix.
- [ ] Focus visibility, obscuration and escape paths evaluated with keyboard alone.
- [ ] Scientific formula/figure alternatives independently understood, not merely rendered.
- [ ] Test date, source commit, public deployment and issue links preserved.
- [ ] A separate accessibility review and release decision signed by a responsible person.

These items are deliberately **unchecked**. Their completion requires human
observation and cannot be inferred from the automated CI gate.

## Automated evidence to bring to the reviewer

The [search/keyboard CI](sitewide-experience-audit.md) records the 23-query
research-intent benchmark, observed result ranks, task-family Hit@k and
automated browser/axe findings. Pair those logs with real-user review notes.
The original five stable search checks are hard regression gates; the
additional eighteen tasks are **exploratory diagnostics**, not a promise that
every query yields a relevant top result. Avoid copying sensitive participant
data or personal device logs into issues or screenshots.
