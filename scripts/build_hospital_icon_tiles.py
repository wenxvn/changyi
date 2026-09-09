import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
LOGO_DIR = ROOT / "static" / "images" / "hospitals"
MANIFEST = LOGO_DIR / "manifest.json"
ICON_DIR = LOGO_DIR / "icons"

BAD_SOURCES = ("dayi.org.cn/_nuxt/img/logo",)


def load_font(size):
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/simsun.ttc",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def color_for(name):
    if "中医" in name:
        return "#10b981"
    if any(token in name for token in ("儿童", "妇幼", "口腔", "肿瘤", "德安")):
        return "#c559f0"
    return "#1e40af"


def short_name(name):
    cleaned = name.replace("常州市", "").replace("常州", "").replace("医院", "")
    return cleaned[:2] or "医"


def fallback_icon(name):
    color = color_for(name)
    img = Image.new("RGBA", (96, 96), color)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((26, 18, 70, 70), radius=9, fill="white")
    draw.rounded_rectangle((42, 28, 54, 58), radius=2, fill=color)
    draw.rounded_rectangle((34, 38, 62, 50), radius=2, fill=color)
    font = load_font(18)
    text = short_name(name)
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text(((96 - (bbox[2] - bbox[0])) / 2, 73), text, fill="white", font=font)
    return img


def non_white_bbox(img):
    rgba = img.convert("RGBA")
    pix = rgba.load()
    w, h = rgba.size
    xs, ys = [], []
    for y in range(h):
        for x in range(w):
            r, g, b, a = pix[x, y]
            if a > 8 and min(r, g, b) < 245:
                xs.append(x)
                ys.append(y)
    if not xs or not ys:
        return None
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def crop_logo_symbol(img):
    img = img.convert("RGBA")
    bbox = non_white_bbox(img)
    if bbox:
        img = img.crop(bbox)
    w, h = img.size
    if w > h * 1.8:
        img = img.crop((0, 0, min(w, max(h, int(h * 1.15))), h))
    return img


def make_tile(src):
    img = Image.open(src)
    img = crop_logo_symbol(img)
    img.thumbnail((78, 78), Image.Resampling.LANCZOS)
    tile = Image.new("RGBA", (96, 96), "white")
    x = (96 - img.width) // 2
    y = (96 - img.height) // 2
    tile.alpha_composite(img, (x, y))
    return tile


def main():
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for key, item in manifest.items():
        name = item["name"]
        source = item.get("source", "")
        file_name = item.get("file", "")
        src = LOGO_DIR / file_name
        use_fallback = source == "generated" or any(token in source for token in BAD_SOURCES) or not src.exists()
        try:
            tile = fallback_icon(name) if use_fallback else make_tile(src)
        except Exception:
            tile = fallback_icon(name)
            use_fallback = True
        out = ICON_DIR / f"hospital_{key}.png"
        tile.save(out)
        item["icon_file"] = f"icons/{out.name}"
        item["icon_url"] = "/static/images/hospitals/" + item["icon_file"]
        item["icon_source"] = "generated-tile" if use_fallback else "cropped-logo"
        print(f"{key}: {name} -> {item['icon_file']} ({item['icon_source']})")
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
