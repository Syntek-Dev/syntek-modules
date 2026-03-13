# SEO & AI Discoverability Checklist

**Last Updated**: 13/03/2026 **Version**: 1.0.0 **Maintained By**: Development Team **Language**:
British English (en_GB) **Timezone**: Europe/London

---

## Table of Contents

- [Overview](#overview)
- [Beginner — Search Engine SEO](#beginner--search-engine-seo)
- [Beginner — AI Discoverability](#beginner--ai-discoverability)
- [Intermediate — Search Engine SEO](#intermediate--search-engine-seo)
- [Intermediate — AI Discoverability](#intermediate--ai-discoverability)
- [Advanced — Search Engine SEO](#advanced--search-engine-seo)
- [Advanced — AI Discoverability (GEO)](#advanced--ai-discoverability-geo)
- [Root Files Quick Reference](#root-files-quick-reference)

---

## Overview

This checklist covers all levels of SEO and AI discoverability implementation, from essential root
files through to advanced Generative Engine Optimisation (GEO). Use it to audit existing projects or
guide new implementations.

**How to use this checklist:**

- Work through each tier in order — Beginner first, then Intermediate, then Advanced
- Tick items off as they are implemented
- Use `/syntek-dev-suite:seo` to implement any section
- Reference `examples/seo/SEO.md` for framework-specific code examples

---

## Beginner — Search Engine SEO

### Root Files & Config

- [ ] `robots.txt` — crawler access rules
- [ ] `sitemap.xml` — XML sitemap submitted to Google Search Console and Bing Webmaster Tools
- [ ] `favicon.ico` / `site.webmanifest` — site icon and PWA config

### HTML Head — Essential Meta

- [ ] Meta title (`<title>` tag)
- [ ] Meta description
- [ ] Meta robots (`noindex`, `nofollow`, `noarchive`, etc.)
- [ ] Canonical tags (`<link rel="canonical">`)
- [ ] Viewport meta tag (mobile responsiveness)
- [ ] Charset declaration (UTF-8)
- [ ] Favicon / icon links

### On-Page Basics

- [ ] Heading hierarchy (H1–H6, one H1 per page)
- [ ] Image alt text on all images
- [ ] Descriptive, keyword-aware URLs (short, readable slugs)
- [ ] Internal linking between related pages
- [ ] Mobile-friendly / responsive design
- [ ] HTTPS (SSL/TLS certificate)
- [ ] Page load speed (compress images, minify CSS/JS)
- [ ] Custom 404 error page

### Content Basics

- [ ] Unique, helpful content per page
- [ ] Keyword research and natural keyword usage
- [ ] Content freshness (regular updates)

### Accounts & Tools

- [ ] Google Search Console (verify site, submit sitemap)
- [ ] Bing Webmaster Tools (verify site, submit sitemap)
- [ ] Google Business Profile (for local businesses)

---

## Beginner — AI Discoverability

- [ ] `llms.txt` — Markdown file at site root for LLM agents
- [ ] `llms-full.txt` — full content version for AI agents
- [ ] Allow AI crawlers in `robots.txt` (GPTBot, ClaudeBot, PerplexityBot, Google-Extended)
- [ ] Clear, direct answers in first paragraph of content (BLUF — Bottom Line Up Front)
- [ ] Plain language, well-structured prose (easy for AI to parse and chunk)

---

## Intermediate — Search Engine SEO

### Structured Data & Rich Results

- [ ] Schema.org / JSON-LD markup (`LocalBusiness`, `Organization`, `Product`, `FAQ`, `Event`, etc.)
- [ ] Breadcrumb structured data
- [ ] Review / rating structured data
- [ ] Sitelinks search box markup

### HTML Head — Social & Sharing

- [ ] Open Graph tags (`og:title`, `og:description`, `og:image`, `og:url`, `og:type`)
- [ ] Twitter Card tags (`twitter:card`, `twitter:title`, `twitter:description`, `twitter:image`)

### HTML Head — International & Language

- [ ] Hreflang tags (multilingual / regional targeting)
- [ ] `Content-Language` meta tag

### Indexing & Crawl Efficiency

- [ ] IndexNow protocol (push-based instant indexing for Bing, Yandex, Seznam, DuckDuckGo)
- [ ] XML sitemap segmentation (separate sitemaps for posts, pages, images, videos)
- [ ] Sitemap index file (for large sites)
- [ ] Crawl budget management (avoid crawl traps, parameter handling)
- [ ] Pagination handling (`rel="next"` / `rel="prev"` or load-more patterns)

### Technical Performance

- [ ] Core Web Vitals (LCP, INP, CLS) — measured and within thresholds
- [ ] Image optimisation (WebP/AVIF format, lazy loading, responsive `srcset`)
- [ ] Minified and deferred CSS/JS
- [ ] Content Delivery Network (CDN)
- [ ] Server response time / TTFB optimisation
- [ ] Gzip / Brotli compression

### Content & Authority

- [ ] Internal linking strategy (topical clusters, pillar pages)
- [ ] Backlink profile building (earned links, digital PR)
- [ ] Content audits (update stale content, consolidate thin pages)
- [ ] Duplicate content management (canonicals, redirects)
- [ ] 301 redirect chains (find and fix)

### Local SEO

- [ ] Google Business Profile optimisation
- [ ] Local schema markup (`LocalBusiness`, address, opening hours)
- [ ] NAP consistency (Name, Address, Phone across directories)
- [ ] Local citations and directory listings

---

## Intermediate — AI Discoverability

### Content Structure for AI

- [ ] Question-format H2/H3 headings (mirror natural language queries)
- [ ] Concise, citable statistics and data points in content
- [ ] FAQ sections with direct answers
- [ ] Comparison tables and structured lists
- [ ] "Last updated" timestamps on content
- [ ] Author bylines with credentials / expertise signals

### Technical for AI

- [ ] Server-side rendering (SSR) — avoid content hidden behind JavaScript
- [ ] No critical content behind logins, paywalls, or interactive elements
- [ ] Clean HTML (minimal JavaScript-rendered content for key pages)
- [ ] RSS / Atom feeds (content discovery for aggregators and AI)

### AI Crawler Management

- [ ] Monitor server logs for AI bot traffic (GPTBot, ClaudeBot, PerplexityBot, etc.)
- [ ] Distinguish training bots vs. retrieval bots in `robots.txt`
- [ ] AI-specific sitemap references in `llms.txt`

---

## Advanced — Search Engine SEO

### Technical Architecture

- [ ] JavaScript rendering audit (ensure Googlebot can render JS content)
- [ ] Dynamic rendering for JS-heavy sites
- [ ] Log file analysis (crawl patterns, bot behaviour, crawl waste)
- [ ] Orphan page detection and resolution
- [ ] Redirect mapping and migration planning
- [ ] Edge SEO (Cloudflare Workers, CDN-level optimisations)
- [ ] HTTP/2 or HTTP/3 server configuration
- [ ] Preconnect, prefetch, preload resource hints

### Advanced Structured Data

- [ ] Product schema with `shippingDetails`, `returnPolicy` (e-commerce)
- [ ] Organisation-level schema as fallback
- [ ] `VideoObject` / `HowTo` / `Recipe` schema
- [ ] Event schema with dates and locations
- [ ] Speakable schema (voice search optimisation)
- [ ] `SameAs` links (connect social profiles to Knowledge Graph)

### Advanced Indexing

- [ ] Google Indexing API (for job postings, livestreams, etc.)
- [ ] IndexNow automation (CI/CD integration, post-deploy hooks)
- [ ] Programmatic sitemap generation from database / CMS
- [ ] Noindex / nofollow strategy for faceted navigation and filters

### Security & Trust

- [ ] HTTPS everywhere (HSTS headers, no mixed content)
- [ ] `security.txt` (`/.well-known/security.txt`)
- [ ] Content Security Policy (CSP) headers
- [ ] Permissions-Policy headers

### App & Cross-Platform

- [ ] `/.well-known/assetlinks.json` (Android app linking)
- [ ] `/.well-known/apple-app-site-association` (iOS deep linking)
- [ ] AMP pages (where still relevant)

### Performance Monitoring

- [ ] Real User Monitoring (RUM) for Core Web Vitals
- [ ] Synthetic testing (Lighthouse CI, WebPageTest)
- [ ] Crawl anomaly alerting

### Other Root Files

- [ ] `humans.txt` (credits / team info)
- [ ] `ads.txt` / `sellers.json` (if running programmatic ads)
- [ ] `/.well-known/change-password` (password change redirect)

---

## Advanced — AI Discoverability (GEO)

### Generative Engine Optimisation (GEO)

- [ ] Optimise content for AI citation (be the source AI quotes)
- [ ] Original research, proprietary data, unique case studies (citation magnets)
- [ ] Entity-based content strategy (build brand entity recognition)
- [ ] Third-party authority signals (earned media, press mentions, Wikipedia presence)
- [ ] Content chunking strategy (structure content so RAG systems can extract cleanly)
- [ ] Fan-out query coverage (cover sub-queries that AI decomposes complex questions into)
- [ ] Platform-specific optimisation (ChatGPT, Perplexity, Google AI Overviews, Gemini, Claude)

### AI Monitoring & Measurement

- [ ] Track AI referral traffic in analytics (ChatGPT, Perplexity, etc. as referrers)
- [ ] Monitor brand mentions in AI-generated answers
- [ ] AI citation frequency tracking
- [ ] Share of voice in AI search results
- [ ] Prompt-level monitoring (what prompts surface your brand)

### Technical AI Readiness

- [ ] Ensure content is not trapped in PDFs, images, or iframes
- [ ] Multimodal optimisation (alt text, captions, transcripts for video/audio)
- [ ] API documentation with `llms.txt` for developer-facing products
- [ ] Machine-readable data formats alongside human-readable content

---

## Root Files Quick Reference

| File                                      | Purpose                           |
| ----------------------------------------- | --------------------------------- |
| `/robots.txt`                             | Crawler access rules              |
| `/sitemap.xml`                            | URL list for search engines       |
| `/sitemap-index.xml`                      | Index of multiple sitemaps        |
| `/llms.txt`                               | AI agent content guide (Markdown) |
| `/llms-full.txt`                          | Full content version for AI       |
| `/favicon.ico`                            | Site icon                         |
| `/site.webmanifest`                       | PWA configuration                 |
| `/humans.txt`                             | Site credits                      |
| `/ads.txt`                                | Authorised ad sellers             |
| `/sellers.json`                           | Ad seller info                    |
| `/.well-known/security.txt`               | Vulnerability reporting info      |
| `/.well-known/assetlinks.json`            | Android app deep linking          |
| `/.well-known/apple-app-site-association` | iOS app deep linking              |
| `/.well-known/change-password`            | Password change redirect          |
| `/[indexnow-key].txt`                     | IndexNow API key verification     |

---

## Related Resources

- [SEO Implementation Examples](../../examples/seo/SEO.md) — Framework-specific code for TALL,
  Django, React, React Native
- [Google Search Console](https://search.google.com/search-console) — Submit sitemaps and monitor
  indexing
- [Bing Webmaster Tools](https://www.bing.com/webmasters) — IndexNow and Bing indexing
- [Schema.org](https://schema.org) — Structured data vocabulary reference
- [llms.txt specification](https://llmstxt.org) — AI agent content guide format
