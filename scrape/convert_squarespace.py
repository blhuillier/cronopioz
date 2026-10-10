#!/usr/bin/env python3
"""
Convert the raw Squarespace dump (_squarespace/, made by scrape_squarespace.py)
into Astro content. Run from the project root:

    python3 scrape/convert_squarespace.py

Writes:
    src/content/projects/<slug>/index.md   frontmatter + cleaned HTML body
    src/content/projects/<slug>/cover.*    card/cover image (optimised by Astro at build)
    src/content/pages/about.md
    public/images/<slug>/*                 body images, resized (max 2000 px) to WebP; GIFs kept
    public/files/*                         PDFs

Squarespace layout (12-column rows, spacer columns, galleries, video embeds) is kept
as simple semantic HTML styled by src/styles/global.css (.sq-row / .sq-col / .gallery).

Needs: beautifulsoup4, Pillow. Re-running overwrites generated content.
"""

import html
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, unquote

from bs4 import BeautifulSoup, NavigableString, Tag
from PIL import Image, ImageOps

SRC = Path("_squarespace")
CONTENT = Path("src/content")
PUBLIC = Path("public")
MAX_PX = 2000
COVER_PX = 1600
BANNER_RE = re.compile(r"archived version|아카이브된|major update is underway", re.I)
ALLOWED_STYLE = re.compile(r"text-align\s*:\s*(center|right|left)", re.I)

manifest = json.loads((SRC / "manifest.json").read_text())
IMG_MAP = manifest["images"]          # cdn url (no query) -> images/<file>
FILE_MAP = manifest.get("files", {})  # url -> files/<name>
warnings = []


# ---------------------------------------------------------------- helpers
def clean_url(u):
    return html.unescape(u or "").split("?")[0].strip()


def local_image(u):
    u = clean_url(u)
    if u.startswith("//"):
        u = "https:" + u
    rel = IMG_MAP.get(u)
    if not rel:
        # tolerate http/https or encoding differences
        for k, v in IMG_MAP.items():
            if k.split("/")[-2:] == u.split("/")[-2:]:
                return SRC / v
        return None
    return SRC / rel


def save_resized(src, dest_dir, stem, max_px, keep_anim=True):
    """Resize to max_px on the long side. GIFs/SVGs copied verbatim. Returns (path, w, h)."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    ext = src.suffix.lower()
    if ext == ".svg" or (ext == ".gif" and keep_anim):
        dest = dest_dir / f"{stem}{ext}"
        shutil.copyfile(src, dest)
        try:
            with Image.open(src) as im:
                return dest, im.width, im.height
        except Exception:
            return dest, None, None
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode in ("P", "LA"):
            im = im.convert("RGBA")
        elif im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGB")
        im.thumbnail((max_px, max_px), Image.LANCZOS)
        dest = dest_dir / f"{stem}.webp"
        im.save(dest, "WEBP", quality=82, method=5)
        return dest, im.width, im.height


def safe_stem(name, used):
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", Path(unquote(name)).stem).strip("-").lower()[:60] or "img"
    base, i = stem, 2
    while stem in used:
        stem, i = f"{base}-{i}", i + 1
    used.add(stem)
    return stem


class ImageSink:
    """Collects images for one page and rewrites their URLs."""

    def __init__(self, slug):
        self.slug = slug
        self.dir = PUBLIC / "images" / slug
        self.used = set()
        self.done = {}

    def __call__(self, url, alt=""):
        url = clean_url(url)
        if url in self.done:
            return self.done[url]
        src = local_image(url)
        if not src or not src.exists():
            warnings.append(f"[{self.slug}] missing image {url}")
            self.done[url] = None
            return None
        stem = safe_stem(src.name.split("-", 1)[-1], self.used)
        dest, w, h = save_resized(src, self.dir, stem, MAX_PX)
        res = (f"/images/{self.slug}/{dest.name}", w, h)
        self.done[url] = res
        return res


def img_tag(sink, url, alt="", cls=None):
    r = sink(url, alt)
    if not r:
        return ""
    src, w, h = r
    a = [f'src="{src}"', f'alt="{html.escape(alt or "", quote=True)}"', 'loading="lazy"', 'decoding="async"']
    if w and h:
        a += [f'width="{w}"', f'height="{h}"']
    if cls:
        a.append(f'class="{cls}"')
    return f"<img {' '.join(a)}>"


def rewrite_href(href):
    if not href:
        return href
    h = html.unescape(href)
    u = urlparse(h)
    host = u.netloc.lower()
    if host in ("", "www.cronopioz.com", "cronopioz.com"):
        p = u.path or "/"
        if p.startswith("/s/") or p.lower().endswith(".pdf"):
            name = re.sub(r"[^A-Za-z0-9._-]+", "_", unquote(p.split("/")[-1]))
            if (PUBLIC / "files" / name).exists():
                return f"/files/{name}"
            warnings.append(f"dead file link {h}")
            return h if host else f"https://www.cronopioz.com{p}"
        if host or h.startswith("/"):
            if p == "/about":
                p = "/about"
            elif p == "/aboutsung":
                p = "/about"
            return p + (("#" + u.fragment) if u.fragment else "")
    return h


def clean_text_html(node):
    """Strip Squarespace attributes from a text block, keep semantic tags + links."""
    for t in node.find_all(True):
        attrs = {}
        if t.name == "a" and t.get("href"):
            attrs["href"] = rewrite_href(t["href"])
            if t.get("target") == "_blank" or urlparse(attrs["href"]).netloc:
                attrs["target"] = "_blank"
                attrs["rel"] = "noopener"
        if t.get("style"):
            m = ALLOWED_STYLE.search(t["style"])
            if m and m.group(1).lower() != "left":
                attrs["class"] = f"ta-{m.group(1).lower()}"
        if t.name == "img" and (t.get("data-src") or t.get("src")):
            attrs["alt"] = t.get("alt", "")
            attrs["data-sq-src"] = t.get("data-src") or t.get("src")
        t.attrs = attrs
    for t in node.find_all(["span"]):
        if not t.attrs:
            t.unwrap()
    out = "".join(str(c) for c in node.contents).strip()
    out = re.sub(r"<p>\s*(&nbsp;| )?\s*</p>", "", out)
    return out


def block_html(block, sink):
    cls = block.get("class", [])
    defn = block.get("data-definition-name", "")
    if "html-block" in cls:
        inner = block.select_one(".sqs-html-content") or block.select_one(".sqs-block-content")
        if not inner:
            return ""
        for para in inner.find_all(["p", "h1", "h2", "h3", "h4"]):
            if BANNER_RE.search(para.get_text(" ")) and len(para.get_text(" ")) < 200:
                para.decompose()
        h = clean_text_html(inner)
        # inline imgs inside text (rare)
        h = re.sub(r'<img alt="([^"]*)" data-sq-src="([^"]+)"/?>',
                   lambda m: img_tag(sink, m.group(2), m.group(1)), h)
        return f'<div class="text">{h}</div>' if h else ""
    if "image-block" in cls:
        img = block.select_one("img[data-src], img[src]")
        if not img:
            return ""
        alt = img.get("alt", "")
        tag = img_tag(sink, img.get("data-src") or img.get("src"), alt)
        cap = block.select_one("figcaption")
        cap_h = ""
        if cap and cap.get_text(strip=True):
            cap_h = f"<figcaption>{clean_text_html(cap)}</figcaption>"
        link = block.select_one("a[href]")
        if link and tag:
            tag = f'<a href="{rewrite_href(link["href"])}">{tag}</a>'
        return f"<figure>{tag}{cap_h}</figure>" if tag else ""
    if "gallery-block" in cls:
        try:
            cfg = json.loads(block.get("data-block-json") or "{}")
        except Exception:
            cfg = {}
        design = cfg.get("design", "grid")
        cols = cfg.get("thumbnails-per-row") or 3
        imgs = []
        for slide in block.select(".slide, .sqs-gallery-design-stacked-slide, .image-slide-anchor") or []:
            im = slide.select_one("img[data-src], img[data-image], img[src]")
            if im is None:
                continue
            u = im.get("data-src") or im.get("data-image") or im.get("src")
            if any(u == x[0] for x in imgs):
                continue
            title = slide.select_one(".meta-title, .image-slide-title")
            imgs.append((u, im.get("alt", ""), title.get_text(" ", strip=True) if title else ""))
        if not imgs:  # fallback: any img in block
            for im in block.select("img"):
                u = im.get("data-src") or im.get("data-image") or im.get("src")
                if u and all(u != x[0] for x in imgs):
                    imgs.append((u, im.get("alt", ""), ""))
        figs = []
        for u, alt, title in imgs:
            t = img_tag(sink, u, alt if not re.search(r"\.(jpe?g|png|gif)$", alt, re.I) else "")
            if t:
                figs.append(f"<figure>{t}" + (f"<figcaption>{html.escape(title)}</figcaption>" if title else "") + "</figure>")
        if not figs:
            return ""
        kind = {"grid": "grid", "stacked": "stacked", "slideshow": "slides", "slider": "slides"}.get(design, "grid")
        style = f' style="--cols:{cols}"' if kind == "grid" else ""
        return f'<div class="gallery gallery-{kind}"{style}>' + "".join(figs) + "</div>"
    if defn.endswith("spacer") or "spacer-block" in cls:
        return '<div class="spacer"></div>'
    if defn.endswith("horizontalrule") or "horizontalrule-block" in cls:
        return "<hr>"
    if defn.endswith("video") or "video-block" in cls or "embed-block" in cls:
        w = block.select_one("[data-html]")
        raw = html.unescape(w["data-html"]) if w else str(block.select_one("iframe") or "")
        m = re.search(r'src="([^"]+)"', raw)
        if not m:
            warnings.append(f"[{sink.slug}] video/embed without src")
            return ""
        src = m.group(1).replace("&amp;", "&")
        src = re.sub(r"[?&]wmode=opaque", "", src)
        if src.startswith("//"):
            src = "https:" + src
        pad = block.select_one(".embed-block-wrapper")
        ratio = "16 / 9"
        if pad and "padding-bottom" in (pad.get("style") or ""):
            pm = re.search(r"padding-bottom:\s*([\d.]+)%", pad["style"])
            if pm and float(pm.group(1)) > 0:
                ratio = f"100 / {float(pm.group(1)):.2f}"
        title = re.search(r'title="([^"]*)"', raw)
        t = html.escape(title.group(1)) if title else "Video"
        return (f'<div class="video" style="aspect-ratio:{ratio}"><iframe src="{src}" title="{t}" '
                f'loading="lazy" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe></div>')
    # Unknown block: keep its text content, warn.
    txt = block.select_one(".sqs-block-content")
    warnings.append(f"[{sink.slug}] unhandled block {cls[:3]} {defn}")
    return f'<div class="text">{clean_text_html(txt)}</div>' if txt and txt.get_text(strip=True) else ""


def layout_html(body_html, sink):
    soup = BeautifulSoup(body_html or "", "html.parser")
    layouts = soup.select(".sqs-layout") or [soup]
    out = []

    def render_row(row):
        cols = row.find_all("div", class_="col", recursive=False)
        parts, pads = [], []
        for col in cols:
            m = re.search(r"span-(\d+)", " ".join(col.get("class", [])))
            span = int(m.group(1)) if m else 12
            inner = []
            for child in col.find_all("div", recursive=False):
                if "sqs-row" in child.get("class", []):
                    inner.append(render_row(child))
                elif "sqs-block" in child.get("class", []):
                    inner.append(block_html(child, sink))
            body = "".join(x for x in inner if x)
            only_spacer = body.replace('<div class="spacer"></div>', "") == ""
            pads.append(only_spacer)
            if only_spacer:
                parts.append(f'<div class="sq-col sq-pad" style="--span:{span}"></div>')
            else:
                parts.append(f'<div class="sq-col" style="--span:{span}">{body}</div>')
        if all(pads):
            return ""
        if len(parts) == 1:  # full-width row: no wrapper needed
            return re.sub(r'^<div class="sq-col" style="--span:\d+">(.*)</div>$', r"\1", parts[0], flags=re.S)
        return '<div class="sq-row">' + "".join(parts) + "</div>"

    for layout in layouts:
        rows = layout.find_all("div", class_="sqs-row", recursive=False)
        for row in rows:
            out.append(render_row(row))
        # Stray top-level blocks (no row)
        for blk in layout.find_all("div", class_="sqs-block", recursive=False):
            out.append(block_html(blk, sink))
    h = "\n".join(x for x in out if x)
    h = re.sub(r'(<div class="spacer"></div>\s*)+', '<div class="spacer"></div>', h)
    return h.strip()


def text_of(h, n=220):
    t = BeautifulSoup(h or "", "html.parser").get_text(" ", strip=True)
    t = re.sub(r"\s+", " ", t)
    return (t[: n - 1].rsplit(" ", 1)[0] + "…") if len(t) > n else t


def yaml_str(s):
    return json.dumps(s or "", ensure_ascii=False)


# ---------------------------------------------------------------- main
def main():
    pages_dir = SRC / "pages"
    items = {}
    for f in sorted(pages_dir.glob("projects*.json")):
        if not re.fullmatch(r"projects(\.p\d+)?\.json", f.name):
            continue
        for it in json.loads(f.read_text()).get("items", []):
            items[it["urlId"]] = it

    home = json.loads((pages_dir / "_home.json").read_text()).get("mainContent", "")
    featured = []
    for h in re.findall(r'href="/projects/([^"]+)"', home):
        if h not in featured and h in items:
            featured.append(h)

    proj_root = CONTENT / "projects"
    if proj_root.exists():
        shutil.rmtree(proj_root)
    proj_root.mkdir(parents=True)
    if (PUBLIC / "images").exists():
        shutil.rmtree(PUBLIC / "images")

    # PDFs first (body links are rewritten against them)
    (PUBLIC / "files").mkdir(parents=True, exist_ok=True)
    for f in (SRC / "files").glob("*"):
        if f.suffix.lower() == ".pdf":
            shutil.copyfile(f, PUBLIC / "files" / f.name)
    for u, rel in list(IMG_MAP.items()):
        if rel.lower().endswith(".pdf"):  # a PDF caught by the image regex
            shutil.copyfile(SRC / rel, PUBLIC / "files" / Path(rel).name.split("-", 1)[-1])

    slugs = set()
    for url_id, it in items.items():
        slug = url_id.split("/")[-1]
        assert slug not in slugs, f"duplicate slug {slug}"
        slugs.add(slug)
        d = proj_root / slug
        d.mkdir()
        sink = ImageSink(slug)
        body = layout_html(it.get("body", ""), sink)

        cover_line = ""
        cover_src = local_image(it.get("assetUrl", "")) if it.get("assetUrl") else None
        if cover_src and cover_src.exists():
            dest, _, _ = save_resized(cover_src, d, "cover", COVER_PX, keep_anim=False)
            cover_line = f"cover: ./{dest.name}\n"
        else:
            warnings.append(f"[{slug}] no cover image")

        date = datetime.fromtimestamp(it["publishOn"] / 1000, tz=timezone.utc).date().isoformat()
        tags = [t for t in it.get("tags", []) if t.lower() != "feat"]
        excerpt = text_of(it.get("excerpt")) or text_of(it.get("body"), 200)
        fm = (
            "---\n"
            f"title: {yaml_str(html.unescape(it['title']))}\n"
            f"date: {date}\n"
            f"categories: {json.dumps(it.get('categories', []))}\n"
            f"tags: {json.dumps(tags)}\n"
            f"featured: {str(url_id in featured).lower()}\n"
            + (f"featuredOrder: {featured.index(url_id)}\n" if url_id in featured else "")
            + f"permalink: {yaml_str(url_id)}\n"
            f"excerpt: {yaml_str(excerpt)}\n"
            + cover_line
            + "---\n\n"
        )
        (d / "index.md").write_text(fm + body + "\n", encoding="utf-8")
        print(f"  {slug:40s} {len(sink.done):3d} images")

    # About page
    pages_out = CONTENT / "pages"
    pages_out.mkdir(parents=True, exist_ok=True)
    about = json.loads((pages_dir / "aboutsung.json").read_text())
    sink = ImageSink("about")
    body = layout_html(about.get("mainContent", ""), sink)
    (pages_out / "about.md").write_text(
        f"---\ntitle: \"About\"\n---\n\n{body}\n", encoding="utf-8")

    print(f"\n{len(items)} projects, {len(featured)} featured -> {proj_root}")
    if warnings:
        print(f"{len(warnings)} warnings:")
        for w in warnings:
            print("  ", w)


if __name__ == "__main__":
    sys.exit(main())
