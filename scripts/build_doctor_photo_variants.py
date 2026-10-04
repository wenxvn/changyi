"""Deterministic display-size derivatives of existing local doctor photos.

Retains source images and provenance; does not invent/retouch identity or upgrade
license verification. Generates a compact frontend URL map and audit metadata.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "static/images/doctors"
OUTPUT = ROOT / "static/images/doctor-variants"
SIZES = (80, 160, 320)


def build(source_root=SOURCE, output_root=OUTPUT, *, limit=None):
    output_root.mkdir(parents=True, exist_ok=True)
    urls, records, failures = {}, [], []
    sources = sorted(p for p in source_root.rglob("*") if p.is_file() and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
    for source in sources[:limit]:
        try:
            source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            source_url = "/" + quote(source.relative_to(ROOT).as_posix(), safe="/")
            variants = {}
            with Image.open(source) as opened:
                oriented = ImageOps.exif_transpose(opened)
                for size in SIZES:
                    target = output_root / f"{source_hash[:20]}-{size}.webp"
                    if not target.exists():
                        image = oriented.convert("RGB")
                        image.thumbnail((size, size), Image.Resampling.LANCZOS)
                        image.save(target, format="WEBP", quality=82, method=4)
                    variants[str(size)] = "/" + target.relative_to(ROOT).as_posix()
            # Preserve original paths too when a source API uses literal Unicode.
            urls["/" + source.relative_to(ROOT).as_posix()] = source_hash[:20]
            records.append({"source_url": source_url, "source_sha256": source_hash, "source_bytes": source.stat().st_size, "variants": variants, "bytes": {size: (ROOT / url.lstrip("/")).stat().st_size for size, url in variants.items()}, "transformation": "exif orientation + aspect-preserving downsize, no crop/retouch", "source_verification": "unchanged; derived asset is not source verification"})
        except Exception as error:
            failures.append({"path": str(source.relative_to(ROOT)), "error": str(error)})
    manifest = {"schema": "doctor-image-variants/v1", "records": records, "failures": failures, "source_images_kept": True}
    metadata = output_root / "manifest.json"
    metadata.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    frontend = ROOT / "frontend/src/data/doctor-photo-variants.json"
    frontend.parent.mkdir(parents=True, exist_ok=True)
    frontend.write_text(json.dumps(urls, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    result = build(limit=args.limit)
    print(f"generated={len(result['records'])} failed={len(result['failures'])}")
    print(f"source_bytes={sum(r['source_bytes'] for r in result['records'])} list_160_bytes={sum(r['bytes']['160'] for r in result['records'])}")
    return int(bool(result["failures"]))


if __name__ == "__main__":
    raise SystemExit(main())
