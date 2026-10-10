# TODO

## Go live for real (cronopioz.com)

The site is currently **hidden from search engines** on purpose: every page has
`<meta name="robots" content="noindex, nofollow">` and `sitemap.xml` is empty.
This switches off automatically once the repository variable `SITE_URL` is set (see `.github/workflows/deploy.yml`).

- [ ] Transfer `blhuillier/cronopioz` → `splazt` (Settings → Danger zone → Transfer ownership); Sung accepts.
- [ ] Sung renames the repo to `splazt.github.io` and re-adds Benjamin as collaborator.
- [ ] Settings → Pages → Source: **GitHub Actions** (re-check after the transfer).
- [ ] Repo → Settings → Secrets and variables → Actions → **Variables**:
  - `SITE_URL` = `https://cronopioz.com`  ← **this removes the noindex** and fills the sitemap
  - `BASE_PATH` = `/`
  - delete `NOINDEX` if it was ever set
- [ ] Settings → Pages → Custom domain: `cronopioz.com`, then tick **Enforce HTTPS**.
- [ ] DNS at the registrar: `A` records for `cronopioz.com` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`; `CNAME www` → `splazt.github.io`.
- [ ] Verify the domain in Sung's GitHub account (Settings → Pages → Verified domains).
- [ ] Re-run the deploy workflow, then check on the live site:
  - page source has **no** `<meta name="robots" content="noindex`
  - `https://cronopioz.com/robots.txt` lists the sitemap
  - `https://cronopioz.com/sitemap.xml` lists ~55 URLs
  - old links still work (e.g. `/projects/chimera`, `/projects/2017/12/7/ai-docent`, `/aboutsung`)
- [ ] Google Search Console: add `cronopioz.com`, submit `sitemap.xml`.
- [ ] Only then cancel Squarespace (transfer the domain out first if it is registered there).
- [ ] Delete the test copy if it still exists anywhere (`www.benjissi.com/cronopioz/`).

## Content

- [ ] Injury Atlas: The Dossiers — new project page (needs images + text from Sung).
- [ ] Martian Gardener images are extracted from the portfolio PDF (~1900 px) — replace with original files.
- [ ] Confirm with Sung: Felt Seams role (curator/artist?), Iași dates, Bogotá and Breeze 2026 details.
- [ ] Master's thesis PDF (`/s/Sungthesis_finalv.pdf`) was a dead link on Squarespace — add to `public/files/` and fix the link in `src/content/projects/mastersthesis/index.md`.
- [ ] `public/files/02__.pdf` is a 2016 ARKO policy report — keep or remove?
- [ ] Drop the draft pages `home2-1`, `new-cover-page-1`, `projects-1` from consideration (not migrated).

## Housekeeping

- [ ] Delete `_to_delete/` (leftovers, git-ignored).
