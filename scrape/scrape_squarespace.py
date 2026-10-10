#!/usr/bin/env python3
"""
Raw dump of a Squarespace site (cronopioz.com) for migration to Astro.

Standard library only (no pip needed). Run from the cronopioz/ folder:

    python3 scrape/scrape_squarespace.py

Output (in ./_squarespace/):
    pages/<slug>.json   Squarespace JSON view of every page / item (?format=json)
    pages/<slug>.html   rendered HTML (layout reference, fallback content)
    images/<asset>-<filename>   full-resolution images (?format=original)
    files/              linked PDFs and other documents
    manifest.json       url -> local files, image url -> local path, errors

The conversion to Markdown/Astro content happens in a second step, from these raw files.
Re-running is safe: files already on disk are skipped.
"""

import json
import re
import sys
import time
import hashlib
import urllib.request
import urllib.error
from urllib.parse import urljoin, urlparse, unquote
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = "https://www.cronopioz.com"
HOSTS = {"www.cronopioz.com", "cronopioz.com"}
SEEDS = ["/", "/projects", "/archive", "/about", "/featured", "/sitemap.xml"]
OUT = Path("_squarespace")
MAX_PAGES = 400
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"

SKIP_PREFIXES = ("/cart", "/account", "/commerce", "/api/", "/s/", "/static/", "/universal/",
                 "/config", "/search")
DOC_EXT = (".pdf", ".zip", ".mp4", ".mov", ".mp3", ".wav", ".docx", ".pptx")
IMG_RE = re.compile(
    r"https?://(?:images\.squarespace-cdn\.com|static1\.squarespace\.com)/[^\s\"'<>\\)]+",
    re.I,
)
HREF_RE = re.compile(r"""href\s*=\s*["']([^"'#]+)""", re.I)
LOC_RE = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.I)


def fetch(url, binary=False, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
                return data if binary else data.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (404, 410, 401, 403):
                break
        except Exception as e:  # network hiccup
            last = e
        time.sleep(1.5 * (i + 1))
    raise last


def norm_path(href, base=BASE):
    u = urlparse(urljoin(base + "/", href))
    if u.scheme not in ("http", "https") or u.netloc.lower() not in HOSTS:
        return None
    p = u.path or "/"
    if p != "/" and p.endswith("/"):
        p = p[:-1]
    return p


def slugify_path(p):
    if p == "/":
        return "_home"
    return re.sub(r"[^A-Za-z0-9._-]+", "__", p.strip("/"))


def clean_img_url(u):
    u = u.replace("&amp;", "&").split("?")[0].rstrip(",.")
    return u


def img_local_name(u):
    parts = urlparse(u).path.strip("/").split("/")
    fname = unquote(parts[-1]) or "image"
    fname = re.sub(r"[^A-Za-z0-9._+-]+", "_", fname)
    asset = parts[-2] if len(parts) >= 2 else hashlib.md5(u.encode()).hexdigest()[:10]
    asset = re.sub(r"[^A-Za-z0-9_-]+", "_", asset)[:40]
    if "." not in fname:
        fname += ".jpg"
    return f"{asset}-{fname}"


def main():
    (OUT / "pages").mkdir(parents=True, exist_ok=True)
    (OUT / "images").mkdir(parents=True, exist_ok=True)
    (OUT / "files").mkdir(parents=True, exist_ok=True)

    manifest = {"base": BASE, "pages": {}, "images": {}, "files": {}, "errors": []}
    queue = list(SEEDS)
    seen = set()
    images = set()
    docs = set()

    while queue and len(seen) < MAX_PAGES:
        raw = queue.pop(0)
        if raw == "/sitemap.xml":
            try:
                xml = fetch(BASE + "/sitemap.xml")
                (OUT / "sitemap.xml").write_text(xml, encoding="utf-8")
                for loc in LOC_RE.findall(xml):
                    p = norm_path(loc)
                    if p:
                        queue.append(p)
                images.update(clean_img_url(m) for m in IMG_RE.findall(xml))
            except Exception as e:
                manifest["errors"].append({"url": "/sitemap.xml", "error": repr(e)})
            continue

        p = norm_path(raw)
        if not p or p in seen or p.startswith(SKIP_PREFIXES):
            continue
        if p.lower().endswith(DOC_EXT):
            docs.add(BASE + p)
            continue
        seen.add(p)
        slug = slugify_path(p)
        entry = {"path": p}
        print(f"[page {len(seen):3d}] {p}", flush=True)

        # JSON view (+ pagination for collections)
        json_url = BASE + p + "?format=json"
        page_no = 0
        while json_url:
            suffix = "" if page_no == 0 else f".p{page_no}"
            cached = OUT / "pages" / f"{slug}{suffix}.json"
            was_cached = cached.exists()
            try:
                txt = cached.read_text(encoding="utf-8") if was_cached else fetch(json_url)
                data = json.loads(txt)
            except Exception as e:
                manifest["errors"].append({"url": json_url, "error": repr(e)})
                break
            suffix = "" if page_no == 0 else f".p{page_no}"
            (OUT / "pages" / f"{slug}{suffix}.json").write_text(
                json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
            entry.setdefault("json", []).append(f"pages/{slug}{suffix}.json")
            images.update(clean_img_url(m) for m in IMG_RE.findall(txt))
            for m in HREF_RE.findall(txt.replace('\\"', '"')):
                queue.append(m)
            for it in data.get("items", []) or []:
                if it.get("fullUrl"):
                    queue.append(it["fullUrl"])
            for c in (data.get("collection") or {}).get("collections", []) or []:
                if c.get("fullUrl"):
                    queue.append(c["fullUrl"])
            pag = data.get("pagination") or {}
            json_url = None
            if pag.get("nextPage") and pag.get("nextPageUrl"):
                nxt = urljoin(BASE, pag["nextPageUrl"])
                json_url = nxt + ("&" if "?" in nxt else "?") + "format=json"
                page_no += 1
            if not was_cached:
                time.sleep(0.3)

        # Rendered HTML
        try:
            hcache = OUT / "pages" / f"{slug}.html"
            html = hcache.read_text(encoding="utf-8") if hcache.exists() else fetch(BASE + p)
            (OUT / "pages" / f"{slug}.html").write_text(html, encoding="utf-8")
            entry["html"] = f"pages/{slug}.html"
            images.update(clean_img_url(m) for m in IMG_RE.findall(html))
            for m in HREF_RE.findall(html):
                queue.append(m)
                if m.lower().split("?")[0].endswith(DOC_EXT):
                    docs.add(urljoin(BASE + "/", m))
        except Exception as e:
            manifest["errors"].append({"url": BASE + p, "error": repr(e)})

        manifest["pages"][p] = entry

    # Images
    images = sorted(u for u in images if not u.endswith((".js", ".css")))
    print(f"\nDownloading {len(images)} images ...", flush=True)

    def dl_img(u):
        dest = OUT / "images" / img_local_name(u)
        if dest.exists() and dest.stat().st_size > 0:
            return u, str(dest.relative_to(OUT)), None
        for variant in (u + "?format=original", u + "?format=2500w", u):
            try:
                data = fetch(variant, binary=True)
                tmp = dest.with_suffix(dest.suffix + ".part")
                tmp.write_bytes(data)
                tmp.replace(dest)
                return u, str(dest.relative_to(OUT)), None
            except Exception as e:
                err = repr(e)
        return u, None, err

    with ThreadPoolExecutor(16) as ex:
        for i, (u, local, err) in enumerate(ex.map(dl_img, images), 1):
            if local:
                manifest["images"][u] = local
            else:
                manifest["errors"].append({"url": u, "error": err})
            if i % 25 == 0:
                print(f"  {i}/{len(images)}", flush=True)

    # Documents (PDFs etc.)
    for u in sorted(docs):
        name = re.sub(r"[^A-Za-z0-9._-]+", "_", unquote(urlparse(u).path.split("/")[-1])) or "file"
        dest = OUT / "files" / name
        try:
            if not dest.exists():
                dest.write_bytes(fetch(u, binary=True))
            manifest["files"][u] = str(dest.relative_to(OUT))
        except Exception as e:
            manifest["errors"].append({"url": u, "error": repr(e)})

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nDone: {len(manifest['pages'])} pages, {len(manifest['images'])} images, "
          f"{len(manifest['files'])} files, {len(manifest['errors'])} errors -> {OUT.resolve()}")
    if manifest["errors"]:
        print("First errors:", *manifest["errors"][:5], sep="\n  ")


if __name__ == "__main__":
    sys.exit(main())
