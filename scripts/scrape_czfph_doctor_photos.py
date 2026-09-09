import json
import os
import re
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser


BASE_URL = "http://www.czfph.com/list/323.html"
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "images", "doctors", "czfph_323")


class LinkImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self._stack = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            self._stack.append({"href": attrs.get("href", ""), "text": "", "imgs": []})
        elif tag == "img":
            src = attrs.get("src") or attrs.get("data-src") or attrs.get("original")
            alt = attrs.get("alt", "")
            if self._stack:
                self._stack[-1]["imgs"].append({"src": src, "alt": alt})

    def handle_data(self, data):
        if self._stack:
            self._stack[-1]["text"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self._stack:
            item = self._stack.pop()
            if item.get("href") or item.get("imgs"):
                self.items.append(item)


def fetch_bytes(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": BASE_URL,
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read(), resp.headers.get("Content-Type", "")


def fetch_text(url):
    data, _ = fetch_bytes(url)
    return data.decode("utf-8", "ignore")


def clean_name(text):
    text = re.sub(r"\s+", "", text or "")
    text = re.sub(r"[\\/:*?\"<>|]", "_", text)
    return text[:40] or "doctor"


def absolutize(url, base=BASE_URL):
    if not url:
        return ""
    return urllib.parse.urljoin(base, url)


def is_doctor_photo(src):
    if not src:
        return False
    lower = src.lower()
    if not re.search(r"\.(jpg|jpeg|png|webp)(\?|$)", lower):
        return False
    blocked = ("logo", "icon", "banner", "wx", "qrcode", "weixin", "favicon", "nav", "bg")
    return not any(b in lower for b in blocked)


def looks_like_doctor_record(name, page_url):
    if not page_url or page_url.rstrip("/") == BASE_URL.rstrip("/"):
        return False
    if name in ("心血管内科", "科室介绍", "专家介绍"):
        return False
    return any(k in name for k in ("医师", "教授", "博士", "主任", "副主任", "主治"))


def collect_from_list_page():
    html = fetch_text(BASE_URL)
    parser = LinkImageParser()
    parser.feed(html)
    records = []
    seen_imgs = set()
    for item in parser.items:
        text = clean_name(item.get("text"))
        href = absolutize(item.get("href"))
        for img in item.get("imgs", []):
            src = absolutize(img.get("src"))
            if not is_doctor_photo(src) or src in seen_imgs:
                continue
            seen_imgs.add(src)
            name = clean_name(img.get("alt") or text)
            if not looks_like_doctor_record(name, href):
                continue
            records.append({"name": name, "page_url": href, "image_url": src})
    return records


def extension_from_url(url, content_type):
    path = urllib.parse.urlparse(url).path.lower()
    ext = os.path.splitext(path)[1]
    if ext in (".jpg", ".jpeg", ".png", ".webp"):
        return ext
    if "png" in content_type:
        return ".png"
    if "webp" in content_type:
        return ".webp"
    return ".jpg"


def download_records(records):
    os.makedirs(OUT_DIR, exist_ok=True)
    saved = []
    for index, rec in enumerate(records, 1):
        try:
            data, content_type = fetch_bytes(rec["image_url"])
            if len(data) < 1024:
                continue
            ext = extension_from_url(rec["image_url"], content_type)
            filename = f"{index:03d}_{clean_name(rec['name'])}{ext}"
            path = os.path.join(OUT_DIR, filename)
            with open(path, "wb") as f:
                f.write(data)
            saved.append({**rec, "file": path.replace("\\", "/"), "size": len(data)})
            time.sleep(0.15)
        except Exception as exc:
            saved.append({**rec, "error": str(exc)})
    manifest = os.path.join(OUT_DIR, "manifest.json")
    with open(manifest, "w", encoding="utf-8") as f:
        json.dump(saved, f, ensure_ascii=False, indent=2)
    return saved, manifest


def main():
    records = collect_from_list_page()
    saved, manifest = download_records(records)
    ok = [x for x in saved if "file" in x]
    errors = [x for x in saved if "error" in x]
    print(json.dumps({
        "source": BASE_URL,
        "found": len(records),
        "downloaded": len(ok),
        "errors": len(errors),
        "output_dir": OUT_DIR.replace("\\", "/"),
        "manifest": manifest.replace("\\", "/"),
        "sample": ok[:5],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
