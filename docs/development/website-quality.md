---
title: Website accessibility and discovery validation
description: How documentation builds are checked for semantic SEO metadata, link integrity, mobile rendering and browser accessibility without claiming full WCAG certification.
---

# Website quality and discoverability

The production website is built with **MkDocs Material**. It keeps the Python package release, scientific validation evidence and documentation-only experimental integrations clearly separated. No site audit alters a published estimator or raw participant data.

## Automated quality controls

| Test | Input | What it establishes | What it does not establish |
| --- | --- | --- | --- |
| Static source contracts | Markdown, local links, SVG references and JavaScript | Required pages and known dynamic links exist in the repository | That every browser can reach every external URL |
| Strict MkDocs build | Python docs, public API, deterministic gallery | The official site builds and API pages render under configured checks | That a successful plot validates statistical inference |
| Public metadata audit | Built HTML, CFF, sitemap and robots | Correct publication version, canonical URLs and citation identity for representative pages | Search-engine indexing or rich-result eligibility |
| Playwright desktop/mobile | Built site on the real GitHub Pages subpath | Images, interactions, route loading and browser screenshots | Full cross-browser and device coverage |
| Locally installed axe-core | Representative interactive pages | Tagged WCAG 2.0–2.2 accessibility issue report | Manual accessibility or WCAG certification |
| Zensical preview | Same source built separately in classic mode | Selected static route and asset compatibility | Approval to migrate production hosting |

The isolated accessibility runner installs [axe-core](https://github.com/dequelabs/axe-core) **only in CI** and injects it into a locally served copy of the generated documentation. It is **not** loaded for actual website visitors. Its results identify concrete failures and issues requiring manual review; automation alone cannot demonstrate complete WCAG compliance.

## Citation and discovery information

[Software citation](../start/cite-and-reproduce.md) is based on the repository's [CITATION.cff](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/main/CITATION.cff). The homepage exposes a static `SoftwareSourceCode` JSON-LD description aligned with version **1.2.0**, the MIT license and the official GitHub repository. A `robots.txt` file points to the MkDocs-generated sitemap.

These additions make source identification and crawling clearer. They **do not guarantee ranking or enhanced search results**. No DOI is present in the current CFF, and the page does not assert one.

## Accessibility issues discovered and addressed

The first optional axe-core run flagged an unnamed Material loading progressbar, top-tab text just below the 4.5:1 contrast threshold in the light indigo theme, and documentation links distinguishable only by color. A shared minimal CSS/JS refinement now adds a progressbar accessible name, more legible navigation/footer text and underlined inline documentation links. These are **specific remediations**, not a declaration of complete accessibility.

The browser report retains all automated findings with their node selectors and severity; zero findings on a small representative set would still require human testing with assistive technology.

## Regression governance

The site-quality and strict documentation gates must succeed before merging a website PR. Browser and alternate-generator previews provide independent audit artifacts. A future Zensical switch needs explicit human review of API references, site-wide navigation, search, keyboard behavior, mathematical typesetting, assets and historical links.

[Visual explorer](../tools/figure-storyboard.md) · [First analysis](../start/first-analysis.md) · [Citation and research reporting](../start/cite-and-reproduce.md) · [Zensical preview](zensical-preview.md)
