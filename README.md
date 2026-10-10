# Sung's Grotto — cronopioz.com

Portfolio of Sung-A Jang, migrated from Squarespace to [Astro](https://astro.build) and deployed with GitHub Pages.

## Structure

```
src/content/projects/<slug>/index.md   one folder per project (frontmatter + HTML body)
src/content/projects/<slug>/cover.webp card / social image (Astro resizes it at build)
src/content/pages/about.md             About page
public/images/<slug>/                  images used inside project bodies
public/files/                          PDFs (papers, portfolio)
src/pages/                             routes: / , /projects, /projects/category/<Cat>, /projects/<permalink>, /archive, /about, /search
src/styles/global.css                  all styling
.github/workflows/deploy.yml           build + deploy to GitHub Pages on every push to main
scrape/                                one-off Squarespace migration scripts (kept for reference)
```

## Updating exhibitions

- **Home page “Recent exhibitions”**: edit `src/data/exhibitions.ts` (newest first; the home page shows the first 5).
- **Full CV**: edit `src/content/pages/about.md` (section with `id="exhibitions"`).

## Adding a project

Create `src/content/projects/my-project/index.md`:

```markdown
---
title: "My Project"
date: 2026-11-01
categories: ["Art", "Research"]     # Art | Research | Design | Infographics
featured: true                      # show on the home page
featuredOrder: 0                    # position on the home page (0 = first)
excerpt: "One or two sentences for cards, search and social previews."
cover: ./cover.jpg
---

Plain **Markdown** works. Put images next to this file or in `public/images/my-project/`.

![Installation view](./install.jpg)

<div class="gallery gallery-grid" style="--cols:3">
  <figure><img src="/images/my-project/a.webp" alt=""></figure>
  <figure><img src="/images/my-project/b.webp" alt=""></figure>
</div>
```

`permalink` (optional) sets the URL under `/projects/`; it defaults to the folder name.
`draft: true` hides a project.

Layout helpers available in bodies: `.gallery-grid` (with `--cols`), `.gallery-stacked`, `.gallery-slides` (swipe carousel),
`.video` (wrap an `<iframe>`), `.sq-row` / `.sq-col style="--span:6"` (12-column rows).

## Local preview (optional)

Needs Node ≥ 22.12.

```bash
npm install
npm run dev        # http://localhost:4321
npm run build      # full build incl. search index -> dist/
```

When switching `BASE_PATH` between local builds, delete `.astro/` and `node_modules/.astro/` (Astro caches rendered Markdown).

## Deployment

The workflow works out the base path by itself:

| Repo | URL | Base |
|---|---|---|
| `blhuillier/cronopioz` (testing) | https://blhuillier.github.io/cronopioz/ | `/cronopioz` |
| `splazt/splazt.github.io` (final) | https://splazt.github.io/ | `/` |

One-time setup in each repo: **Settings → Pages → Source: GitHub Actions**.

### Search engines (hidden while testing)

Test deploys are **not indexed**: every page gets `<meta name="robots" content="noindex, nofollow">` and the sitemap is empty.
Indexing switches on automatically only when the repository variable `SITE_URL` is set (i.e. once cronopioz.com
points here — step 1 of “Custom domain” below). Force it either way with the repository variable `NOINDEX=true` / `NOINDEX=false`.
Note: `blhuillier.github.io` redirects to `www.benjissi.com`, so the test copy is served at `www.benjissi.com/cronopioz/`.

### Hand-over

1. `blhuillier/cronopioz` → Settings → Danger zone → **Transfer ownership** → `splazt`.
2. Sung accepts, renames the repo to `splazt.github.io`, and re-adds Benjamin as collaborator.
3. Settings → Pages → Source: GitHub Actions (re-check after transfer). Push or re-run the workflow.
   It stays hidden from search engines on `splazt.github.io` too, until `SITE_URL` is set.

### Custom domain (when leaving Squarespace)

1. Repo → Settings → Secrets and variables → Actions → **Variables**: `SITE_URL=https://cronopioz.com`, `BASE_PATH=/`.
2. Settings → Pages → Custom domain: `cronopioz.com`, then **Enforce HTTPS**.
3. DNS at the registrar: `A` records for `cronopioz.com` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`; `CNAME www` → `splazt.github.io`.
4. Verify the domain in Sung's GitHub account settings (Pages → Verified domains).
5. Only then cancel Squarespace (transfer the domain out first if it is registered there).

## Squarespace migration (already done)

```bash
python3 scrape/scrape_squarespace.py    # raw dump -> _squarespace/ (not committed)
python3 scrape/convert_squarespace.py   # -> src/content, public/images, public/files (needs bs4, Pillow)
```

Re-running the converter **overwrites** `src/content/projects`, `public/images` and the About page — don't run it after editing content by hand.

Known gap: the master's thesis PDF (`/s/Sungthesis_finalv.pdf`) was already a dead link on Squarespace; add the file to `public/files/` and fix the link in `src/content/projects/mastersthesis/index.md`.
