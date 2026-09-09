import json
import mimetypes
import re
import ssl
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parents[1] / "static" / "images" / "hospitals"

HOSPITALS = [
    {"id": 1, "name": "常州市第一人民医院", "url": "http://www.czfph.com/"},
    {"id": 2, "name": "常州市第二人民医院", "url": "https://www.czey.com/"},
    {"id": 3, "name": "常州市中医医院", "url": "https://czzyy.com/"},
    {"id": 4, "name": "常州市第三人民医院", "url": "https://www.jsczsy.cn/"},
    {"id": 5, "name": "常州市肿瘤医院", "url": "https://www.czdsyy.cn/"},
    {"id": 6, "name": "常州市儿童医院", "url": "https://www.czsetyy.cn/"},
    {"id": 7, "name": "常州市妇幼保健院", "url": "http://www.czfybjy.com/"},
    {"id": 8, "name": "武进人民医院", "url": "http://www.wjh.cn/"},
    {"id": 9, "name": "金坛第一人民医院", "url": "https://www.jtrmyy.com/"},
    {"id": 10, "name": "溧阳市人民医院", "url": "https://www.lyrmyy.com/"},
    {"id": 11, "name": "常州市老年病医院", "url": "https://www.dayi.org.cn/hospital/1140219"},
    {"id": 12, "name": "武进中医医院", "url": "https://www.wjzyyy.com/"},
    {"id": 13, "name": "溧阳市中医医院", "url": "https://www.dayi.org.cn/hospital/1133138"},
    {"id": 14, "name": "常州市德安医院", "url": "http://www.czdeanhospital.com/"},
    {"id": 15, "name": "常州市第七人民医院", "url": "https://www.dayi.org.cn/hospital/1140219"},
    {"id": 16, "name": "常州市口腔医院", "url": "https://www.czskq.com/"},
    {"id": 17, "name": "常州市中西医结合医院", "url": "https://www.jsczsy.cn/"},
    {"id": 18, "name": "金坛区中医医院", "url": "https://www.jswsrc.com.cn/company/index.php?c=show&id=9326"},
    {"id": 19, "name": "金坛区第二人民医院", "url": "https://m.bohe.cn/hospital/34663/"},
    {"id": 20, "name": "溧阳市妇幼保健院", "url": "https://yyk.39.net/cz2/e8f36/"},
    {"id": 21, "name": "新北区三井人民医院", "url": "https://www.bohe.cn/hospital/37356/introduce/"},
]


class ImageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []
        self.icons = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "img" and attrs.get("src"):
            self.images.append(attrs)
        if tag == "link":
            rel = " ".join(attrs.get("rel", []) if isinstance(attrs.get("rel"), list) else [attrs.get("rel", "")]).lower()
            if ("icon" in rel or "shortcut" in rel) and attrs.get("href"):
                self.icons.append(attrs.get("href"))


def fetch(url, timeout=12):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        },
    )
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read(), resp.headers.get("Content-Type", ""), resp.geturl()


def decode_html(raw, content_type):
    match = re.search(r"charset=([\w-]+)", content_type or "", re.I)
    encodings = [match.group(1)] if match else []
    encodings += ["utf-8", "gb18030"]
    for enc in encodings:
        try:
            return raw.decode(enc)
        except Exception:
            pass
    return raw.decode("utf-8", "ignore")


def score_image(attrs):
    text = " ".join(str(attrs.get(k, "")) for k in ("src", "alt", "title", "class", "id")).lower()
    score = 0
    for token in ("logo", "log", "brand", "head", "医院", "hospital", "top"):
        if token in text:
            score += 10
    for token in ("qrcode", "qr", "weixin", "wx", "banner", "slide", "news", "doctor", "avatar"):
        if token in text:
            score -= 12
    return score


def extension_from(content_type, url):
    ext = mimetypes.guess_extension((content_type or "").split(";")[0].strip()) or Path(urllib.parse.urlparse(url).path).suffix
    if ext.lower() in (".jpeg", ".jpe"):
        ext = ".jpg"
    if ext.lower() not in (".png", ".jpg", ".gif", ".webp", ".svg", ".ico"):
        ext = ".png"
    return ext.lower()


def write_fallback(hospital):
    hid = hospital["id"]
    name = hospital["name"]
    text = name.replace("常州市", "").replace("医院", "")[:2] or "医"
    color = "#10b981" if "中医" in name else ("#c559f0" if any(k in name for k in ("妇幼", "儿童", "口腔", "肿瘤", "德安")) else "#1e40af")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96">
<rect width="96" height="96" rx="22" fill="{color}"/>
<rect x="28" y="20" width="40" height="56" rx="8" fill="white" opacity=".96"/>
<rect x="42" y="30" width="12" height="28" rx="2" fill="{color}"/>
<rect x="34" y="38" width="28" height="12" rx="2" fill="{color}"/>
<text x="48" y="86" text-anchor="middle" font-size="18" font-family="Microsoft YaHei,Arial" font-weight="700" fill="white">{text}</text>
</svg>'''
    path = OUT_DIR / f"hospital_{hid}.svg"
    path.write_text(svg, encoding="utf-8")
    return path, "generated"


def scrape_one(hospital):
    hid = hospital["id"]
    page_url = hospital["url"]
    try:
        raw, content_type, final_url = fetch(page_url)
        html = decode_html(raw, content_type)
        parser = ImageParser()
        parser.feed(html)
        candidates = sorted(parser.images, key=score_image, reverse=True)
        urls = []
        for attrs in candidates[:8]:
            src = attrs.get("src") or attrs.get("data-src") or attrs.get("data-original")
            if src:
                urls.append(urllib.parse.urljoin(final_url, src))
        for icon in parser.icons:
            urls.append(urllib.parse.urljoin(final_url, icon))
        urls.append(urllib.parse.urljoin(final_url, "/favicon.ico"))
        seen = set()
        for img_url in urls:
            if img_url in seen:
                continue
            seen.add(img_url)
            try:
                data, ctype, real_url = fetch(img_url)
                if len(data) < 200:
                    continue
                ext = extension_from(ctype, real_url)
                path = OUT_DIR / f"hospital_{hid}{ext}"
                path.write_bytes(data)
                return path, real_url
            except Exception:
                continue
    except Exception:
        pass
    return write_fallback(hospital)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for hospital in HOSPITALS:
        path, source = scrape_one(hospital)
        manifest[str(hospital["id"])] = {
            "id": hospital["id"],
            "name": hospital["name"],
            "file": path.name,
            "url": "/static/images/hospitals/" + path.name,
            "source": source,
        }
        print(f"{hospital['id']:02d} {hospital['name']} -> {path.name} ({source})")
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
