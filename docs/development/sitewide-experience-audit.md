---
title: Site-wide website quality and Zensical migration decision
description: Rendered links and fragments, search coverage, Lighthouse mobile baselines, accessibility and reversible Zensical qualification.
---

# Site-wide quality audit and migration decision

The next stage addresses the existing documentation archive rather than adding another package-integration catalog. Production remains **MkDocs Material** and the published Python package remains **1.2.0**.

## Five independent reviews

| Review | Source | Scope and limitation |
| --- | --- | --- |
| Link integrity | All built HTML pages and local `href`/`src` values | Actual relative targets, assets and HTML fragments under the repository's GitHub Pages prefix; excludes externally hosted targets |
| Search discovery | MkDocs `search/search_index.json` | Ten reader-intent topics and corresponding indexed pages, not live Lunr ranking |
| Mobile Lighthouse | Four representative routes, simulated mobile | Reproducible initial performance, accessibility, best-practices and SEO evidence, not a stable speed guarantee |
| Browser accessibility | Playwright and locally installed axe-core | Desktop/mobile interactive checks and automatically detectable serious issues; manual review still needed |
| Zensical comparison | MkDocs and Zensical 0.0.72 classic outputs | All built routes and core assets plus earlier eleven representative checks; no automatic production switch |

## Run the production site audits locally

Build the current documentation and its existing deterministic scientific gallery:

~~~bash
python scripts/generate_docs_gallery.py
mkdocs build --strict
python scripts/audit_sitewide_links.py --output build/sitewide-links.json
python scripts/audit_search_corpus.py --output build/site-search-corpus.json
~~~

The first CI baseline covered **368 generated pages and 152,683 local targets** with zero missing local files, but identified **80 broken named-fragment references** (mostly public plotting gallery → Python API and two links to the integration checklist). Those were corrected at the gallery generator and the navigator's declared section ID. A second audit reduced missing fragments from 80 to 8, pinpointing seven exported plotting functions without API documentation anchors and one omitted mathematical-reference section. These final eight targets now have explicit published entries. The strict link-audit gate must pass before declaring the site clean. Zensical rendered the same 368 page routes but initially produced one wrong relative tabular handoff link; this fallback is now explicitly rooted at the published Pages subpath and must be verified again. Zensical also uses a different search asset layout, so index existence alone is not evidence of equivalent search functionality. The migration decision remains HOLD.

The first site-wide pass is **diagnostic**, with detailed machine-readable evidence. Add `--strict` to the commands only after reviewing legacy broken-link findings and intended exclusions. It does not contact third-party URLs.

The link audit resolves the real public `/eyetrajectoriespy/` subpath, including named fragment anchors, instead of assuming source Markdown paths are published URLs. [OpenTelemetry's link-checking workflow](https://opentelemetry.io/site/build/link-checking/) provides a useful precedent for distinguishing production-local link checks from remote network validation.

## Reader-intent search cases

The baseline checks discoverability of first analysis, pymovements, SyeLink, sparse FPCA, missing gaze, citation, illustrated methods, integration choice, API reference and W3 inference. It reports indexed page coverage and missing keyword combinations separately. This corpus review is **not** a simulation of live search relevance or a search-engine optimization claim.

## Mobile performance and browser outcomes

The first simulated-mobile Lighthouse run (one run per URL) scored **40/100 homepage**, **82/100 first analysis**, **71/100 visual storyboard**, and **64/100 integration navigator**. Homepage LCP was approximately **10.0 seconds** with **1.5 seconds total blocking time** in that CI simulation. These are diagnostic *lab values*, not real-user Core Web Vitals or a release target.

The website previously loaded MathJax 3 on every page, regardless of whether the page contained mathematics. A conditional loader now requests the existing MathJax source **only on pages with mathematical expressions**, and rerenders equations after MkDocs instant navigation. A browser smoke test checks that the homepage makes no MathJax injection and that the mathematical-reference page requests the engine on demand. This performance intervention is to be evaluated through repeated Lighthouse baselines rather than treated as an automatically proven speedup.

With the successful full-site audit (368 pages, zero local broken files/fragment references), the production docs workflow now enforces **strict link and search-corpus gates**. These checks exclude unknown external URL health and do not prove browser search ranking.



A separate non-deploying CI job runs the pinned [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci) tool on the generated site under its true repository subpath. Raw results and a four-route machine-readable category/metric summary are retained as GitHub Actions artifacts only: no third-party Lighthouse upload occurs. The first actual CI baseline gave simulated mobile performance scores of **59** (homepage), **83** (first analysis), **75** (visual gallery), and **74** (integration navigator). Their accessibility scores were 95–97; best-practices and SEO scores were 100. The homepage had a roughly **9.99-second simulated LCP** dominated by text render delay (not a large image download); font and global script/style scheduling are investigation targets. Meaningful performance thresholds require repeated comparable runs and reviewed variance.

The existing Chromium/axe browser check remains separate. A passing automated audit does not certify full WCAG compliance or user experience across all devices.

## Reversible homepage performance experiment (25 October 2026)

A website-only change removes Google Fonts autoloading via Material's
documented system-font setting (`theme.font: false`). System fallback removes
a third-party render dependency and browser request, though font metrics and
line breaks may vary by device. This targets the observed text-render component
of homepage LCP; it is **not** itself a measured speedup.

The formerly global integration navigator, local CSV inspector, method sharing
and synthetic exploration scripts are now downloaded **only when their page
controls exist**. A small shared loader supports MkDocs instant navigation,
and explicit browser regression checks cover the method selector, integration
navigator and CSV readiness interface. The existing MathJax on-demand behavior
and reproducibility links remain. Site-wide links and search-corpus checks
remain strict.

The independent Lighthouse job now collects **three simulated mobile runs
per route** across the same four routes and retains individual results alongside
min/median/max summaries. CI evidence must be reviewed before claiming a
speedup: this document contains no new post-change scores or field Core Web
Vitals measurements. The browser preview also tests a real interactive search
for the SyeLink documentation, beyond static index keyword presence.

## Navigation pruning: qualified experiment and production candidate (25 October 2026)

Production activation is proposed in a **separate, reversible PR** after the
successfully merged [non-deploying comparison #494](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/494).
Material's [`navigation.prune`](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#navigation-pruning)
shrinks the large, repeated sidebar tree while retaining section-index
navigation. The same option cannot be used with `navigation.expand`.

### Paired full-archive evidence from #494

| Qualification measure | Unpruned | Pruned |
|---|---:|---:|
| Generated routes | 368 | 368 |
| Main-content text hashes matching | 368 | 368 |
| Search-index entries | 4,069 | 4,069, identical |
| Generated HTML (sum of pages) | 75.25 MB | 26.62 MB |
| Gzip-compressed HTML (sum of pages) | 7.26 MB | 4.14 MB |
| Statically reachable pages from homepage | 355 | 355 |
| Newly statically unreachable pages | — | 0 |

All baseline/candidate built links and fragments passed; representative
desktop/mobile Chromium checks for deep routes, section gateways, actual
Material search and drawer navigation passed. Sampled axe-core checks reported
no serious or critical findings. **This is not proof of manual WCAG conformance,
better search ranking, faster real-user loads or a field Core Web Vitals gain.**

The paired non-deploying workflow keeps generating **both builds** even after
the production default changes. The production `mkdocs.yml` flag can be
reverted in one line and all historical deep links are retained. The thirteen
pre-existing pages not reachable by static links are now enumerated by the
reachability audit for a separate editorial fix; they were **not caused by
pruning**.

Review repeated [simulated mobile Lighthouse audits](website-quality.md)
and post-merge Pages deployment before describing the candidate as live.
The published `eyetrajectoriespy==1.2.0` API, scientific estimators and
unqualified inference claims are untouched.

## Zensical production decision: HOLD

The earlier 11-page Zensical static comparison passed, but eleven pages cannot establish equivalence for this large documentation archive. The expanded report now compares **every generated HTML route**, selected custom JS/CSS assets and available search artifacts.

**Do not change production from MkDocs yet.** First qualify equivalent or better:

1. Full historic/deep URL coverage and fragments, including redirects.
2. Search results for the ten reader-intent queries and working instant navigation.
3. Generated `mkdocstrings` API references, figures, math and citation pages.
4. Desktop/mobile performance, keyboard workflows and accessibility.
5. Reversible protected-main build and Pages release governance.

Zensical's [official migration guidance](https://zensical.org/docs/compatibility/mkdocs/migration/) explicitly supports keeping the MkDocs build as a safety net.

!!! warning "Research qualification stays separate"
    This is website quality work, not a revision of the released estimator API or the unresolved [whole-function inference #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [missing-gaze #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) constraints.

[Website quality controls](website-quality.md) · [Zensical preview](zensical-preview.md) · [Citation and reproducibility](../start/cite-and-reproduce.md)
