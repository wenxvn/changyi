"""Check the actual displayed resource path, size reduction and source identity."""
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote
import app


def test_first_page_variants_retain_original_identity_and_reduce_transfer():
    root = Path(app.BASE_DIR)
    urls = json.loads((root / "frontend/src/data/doctor-photo-variants.json").read_text(encoding="utf-8"))
    doctors = app.app.test_client().get("/api/v1/doctors?page_size=24").get_json()["data"]["items"]
    source_bytes = target_bytes = mapped = 0
    for doctor in doctors:
        photo = doctor.get("photo_url")
        key = unquote(photo) if photo else ""
        if key not in urls:
            continue
        source = root / key.lstrip("/")
        prefix = hashlib.sha256(source.read_bytes()).hexdigest()[:20]
        assert urls[key] == prefix
        target = root / "static/images/doctor-variants" / f"{prefix}-160.webp"
        source_bytes += source.stat().st_size
        target_bytes += target.stat().st_size
        mapped += 1
    assert mapped > 0
    assert target_bytes < source_bytes * .1


def test_content_addressed_variant_is_served_with_immutable_cache():
    root = Path(app.BASE_DIR)
    variant = next((root / "static/images/doctor-variants").glob("*-160.webp"))
    client = app.app.test_client()
    result = client.get("/static/images/doctor-variants/" + variant.name)
    assert result.status_code == 200
    assert result.content_type == "image/webp"
    assert "immutable" in result.headers["Cache-Control"]
    missing = client.get("/static/images/doctor-variants/" + "0" * 20 + "-160.webp")
    assert missing.status_code == 404
    assert "immutable" not in missing.headers.get("Cache-Control", "")
